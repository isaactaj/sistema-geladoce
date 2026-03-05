from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from app.database.connection import conectar


class VendasRepository:
    """
    Tabelas:
      - vendas
      - vendas_itens
      - estoque / produtos (para validação e baixa)

    Regras:
      - Tudo em UMA transação
      - Estoque com SELECT ... FOR UPDATE
      - Não vende produto inativo
      - Por padrão, não vende insumo (tipo_item='Insumo' ou eh_insumo=1)
    """

    def _to_decimal(self, valor: Any) -> Decimal:
        if isinstance(valor, Decimal):
            return valor
        txt = str(valor).strip().replace("R$", "").replace(" ", "")
        if not txt:
            return Decimal("0")
        if "," in txt and "." in txt:
            txt = txt.replace(".", "").replace(",", ".")
        else:
            txt = txt.replace(",", ".")
        try:
            return Decimal(txt)
        except Exception:
            return Decimal("0")

    def _normalizar_forma_pagamento(self, forma: str, codigos_existentes: Optional[set] = None) -> str:
        f = str(forma or "").strip()
        if not f:
            raise ValueError("Forma de pagamento é obrigatória.")

        # tolerância com acento
        equivalencias = {
            "cartao": "Cartao",
            "cartão": "Cartão",
        }
        low = f.lower()
        if low in equivalencias:
            prefer = equivalencias[low]
            if codigos_existentes and prefer in codigos_existentes:
                return prefer

        # se o DB tiver, mantém como está
        if codigos_existentes and f in codigos_existentes:
            return f

        # fallback: tenta Cartão/Cartao
        if codigos_existentes:
            if f.lower() == "cartao" and "Cartao" in codigos_existentes:
                return "Cartao"
            if f.lower() == "cartão" and "Cartão" in codigos_existentes:
                return "Cartão"

        # se chegou aqui, vai falhar no FK — melhor falhar com mensagem clara
        raise ValueError("Forma de pagamento inválida (não cadastrada em formas_pagamento).")

    def _listar_codigos_pagamento(self, cur) -> set:
        cur.execute("SELECT codigo FROM formas_pagamento")
        rows = cur.fetchall() or []
        # cursor pode estar como tuple
        return {r[0] for r in rows}

    def registrar_venda(
        self,
        tipo: str,
        itens: List[Dict[str, Any]],
        forma_pagamento: str,
        cliente_id: Optional[int] = None,
        revendedor_id: Optional[int] = None,
        desconto: Decimal = Decimal("0"),
        taxa_entrega: Decimal = Decimal("0"),
        observacao: str = "",
        data_venda: Optional[datetime] = None,
        status: str = "FINALIZADA",
        fechamento_id: Optional[int] = None,
        permitir_insumos: bool = False,
    ) -> Dict[str, Any]:
        tipo = str(tipo or "").strip().upper()
        if tipo not in ("BALCAO", "REVENDA", "DELIVERY"):
            raise ValueError("Tipo de venda inválido.")

        status = str(status or "FINALIZADA").strip().upper()
        if status not in ("ABERTA", "FINALIZADA", "CANCELADA"):
            raise ValueError("Status inválido.")

        data_ref = data_venda if isinstance(data_venda, datetime) else datetime.now()
        desconto = self._to_decimal(desconto)
        taxa_entrega = self._to_decimal(taxa_entrega)
        if desconto < 0:
            desconto = Decimal("0")
        if taxa_entrega < 0:
            taxa_entrega = Decimal("0")

        if not itens:
            raise ValueError("A venda precisa ter ao menos 1 item.")

        # consolida itens repetidos
        consolidados: Dict[int, int] = {}
        for it in itens:
            pid = int(it.get("produto_id"))
            qtd = int(it.get("qtd"))
            if qtd <= 0:
                raise ValueError("Quantidade inválida.")
            consolidados[pid] = consolidados.get(pid, 0) + qtd

        produto_ids = list(consolidados.keys())

        conn = None
        cur = None
        try:
            conn = conectar()
            conn.start_transaction()
            cur = conn.cursor()

            codigos = self._listar_codigos_pagamento(cur)
            forma_ok = self._normalizar_forma_pagamento(forma_pagamento, codigos_existentes=codigos)

            # garante linha de estoque
            for pid in produto_ids:
                cur.execute(
                    """
                    INSERT INTO estoque (produto_id, quantidade)
                    VALUES (%s, 0)
                    ON DUPLICATE KEY UPDATE produto_id=produto_id
                    """,
                    (pid,),
                )

            placeholders = ",".join(["%s"] * len(produto_ids))
            cur.execute(
                f"""
                SELECT
                    p.id, p.nome, p.categoria, p.preco, p.ativo, p.tipo_item, p.eh_insumo,
                    e.quantidade
                FROM produtos p
                JOIN estoque e ON e.produto_id = p.id
                WHERE p.id IN ({placeholders})
                FOR UPDATE
                """,
                tuple(produto_ids),
            )
            rows = cur.fetchall() or []
            mapa = {int(r[0]): r for r in rows}

            # valida e calcula
            itens_norm: List[Dict[str, Any]] = []
            subtotal = Decimal("0")

            for pid, qtd in consolidados.items():
                if pid not in mapa:
                    raise ValueError(f"Produto {pid} não encontrado.")

                r = mapa[pid]
                ativo = int(r[4] or 0)
                tipo_item = str(r[5] or "Produto")
                eh_insumo = int(r[6] or 0)
                estoque_atual = int(r[7] or 0)

                if ativo != 1:
                    raise ValueError(f"Produto inativo: {r[1]}.")
                if not permitir_insumos and (tipo_item == "Insumo" or eh_insumo == 1):
                    raise ValueError(f"Item é insumo e não pode ser vendido: {r[1]}.")

                if estoque_atual < qtd:
                    raise ValueError(f"Estoque insuficiente para {r[1]}.")

                unit = self._to_decimal(r[3])
                total_item = unit * qtd

                itens_norm.append({
                    "produto_id": pid,
                    "produto_nome": r[1],
                    "categoria": r[2],
                    "qtd": qtd,
                    "unitario": unit,
                    "total": total_item,
                })
                subtotal += total_item

            if desconto > subtotal:
                desconto = subtotal

            total = (subtotal - desconto) + taxa_entrega
            if total < 0:
                total = Decimal("0")

            # baixa estoque
            for it in itens_norm:
                pid = int(it["produto_id"])
                qtd = int(it["qtd"])
                novo = int(mapa[pid][7]) - qtd
                if novo < 0:
                    raise ValueError("Estoque insuficiente.")
                cur.execute("UPDATE estoque SET quantidade=%s WHERE produto_id=%s", (novo, pid))

            # insere venda
            cur.execute(
                """
                INSERT INTO vendas
                (tipo, status, data, cliente_id, revendedor_id, fechamento_id,
                 forma_pagamento, observacao, subtotal, desconto, taxa_entrega, total)
                VALUES
                (%s, %s, %s, %s, %s, %s,
                 %s, %s, %s, %s, %s, %s)
                """,
                (
                    tipo, status, data_ref,
                    cliente_id, revendedor_id, fechamento_id,
                    forma_ok, (str(observacao).strip() or None),
                    subtotal, desconto, taxa_entrega, total
                ),
            )
            venda_id = int(cur.lastrowid)

            # itens
            for it in itens_norm:
                cur.execute(
                    """
                    INSERT INTO vendas_itens (venda_id, produto_id, qtd, unitario, total)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (venda_id, int(it["produto_id"]), int(it["qtd"]), it["unitario"], it["total"]),
                )

            conn.commit()

            return {
                "id": venda_id,
                "tipo": tipo,
                "status": status,
                "data": data_ref,
                "cliente_id": cliente_id,
                "revendedor_id": revendedor_id,
                "fechamento_id": fechamento_id,
                "forma_pagamento": forma_ok,
                "observacao": str(observacao).strip(),
                "subtotal": subtotal,
                "desconto": desconto,
                "taxa_entrega": taxa_entrega,
                "total": total,
                "itens": itens_norm,
            }

        except Exception:
            if conn is not None:
                conn.rollback()
            raise
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def listar_vendas(
        self,
        tipo: Optional[str] = None,
        data_inicial: Optional[datetime] = None,
        data_final: Optional[datetime] = None,
        incluir_itens: bool = True,
        limite: int = 2000,
    ) -> List[Dict[str, Any]]:
        where = []
        params: List[Any] = []

        if tipo:
            where.append("v.tipo = %s")
            params.append(str(tipo).strip().upper())

        if data_inicial:
            where.append("v.data >= %s")
            params.append(data_inicial)

        if data_final:
            where.append("v.data <= %s")
            params.append(data_final)

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                f"""
                SELECT
                    v.id, v.tipo, v.status, v.data,
                    v.cliente_id, v.revendedor_id, v.fechamento_id,
                    v.forma_pagamento, v.observacao,
                    v.subtotal, v.desconto, v.taxa_entrega, v.total
                FROM vendas v
                {where_sql}
                ORDER BY v.data DESC, v.id DESC
                LIMIT %s
                """,
                tuple(params + [int(limite)]),
            )
            vendas = cur.fetchall() or []
            if not incluir_itens or not vendas:
                return vendas

            ids = [v["id"] for v in vendas]
            placeholders = ",".join(["%s"] * len(ids))
            cur.execute(
                f"""
                SELECT
                    i.venda_id,
                    i.produto_id,
                    p.nome AS produto_nome,
                    p.categoria,
                    i.qtd,
                    i.unitario,
                    i.total
                FROM vendas_itens i
                JOIN produtos p ON p.id = i.produto_id
                WHERE i.venda_id IN ({placeholders})
                ORDER BY i.id ASC
                """,
                tuple(ids),
            )
            itens = cur.fetchall() or []
            mapa: Dict[int, List[Dict[str, Any]]] = {}
            for it in itens:
                mapa.setdefault(int(it["venda_id"]), []).append({
                    "produto_id": int(it["produto_id"]),
                    "produto_nome": it["produto_nome"],
                    "categoria": it["categoria"],
                    "qtd": int(it["qtd"]),
                    "unitario": self._to_decimal(it["unitario"]),
                    "total": self._to_decimal(it["total"]),
                })

            for v in vendas:
                v["itens"] = mapa.get(int(v["id"]), [])

            return vendas
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def resumo_por_dia(self, dia: date) -> Dict[str, Any]:
        ini = datetime(dia.year, dia.month, dia.day, 0, 0, 0)
        fim = datetime(dia.year, dia.month, dia.day, 23, 59, 59)
        vendas = self.listar_vendas(data_inicial=ini, data_final=fim, incluir_itens=False)

        vendas_brutas = sum((self._to_decimal(v.get("subtotal", 0)) for v in vendas if v.get("status") != "CANCELADA"), Decimal("0"))
        descontos = sum((self._to_decimal(v.get("desconto", 0)) for v in vendas if v.get("status") != "CANCELADA"), Decimal("0"))
        cancelamentos = sum((self._to_decimal(v.get("total", 0)) for v in vendas if v.get("status") == "CANCELADA"), Decimal("0"))
        total_liquido = sum((self._to_decimal(v.get("total", 0)) for v in vendas if v.get("status") != "CANCELADA"), Decimal("0"))

        dinheiro = sum((self._to_decimal(v.get("total", 0)) for v in vendas if v.get("status") != "CANCELADA" and v.get("forma_pagamento") == "Dinheiro"), Decimal("0"))
        pix = sum((self._to_decimal(v.get("total", 0)) for v in vendas if v.get("status") != "CANCELADA" and v.get("forma_pagamento") == "Pix"), Decimal("0"))
        cartao = sum((self._to_decimal(v.get("total", 0)) for v in vendas if v.get("status") != "CANCELADA" and v.get("forma_pagamento") in ("Cartão", "Cartao")), Decimal("0"))
        prazo = sum((self._to_decimal(v.get("total", 0)) for v in vendas if v.get("status") != "CANCELADA" and v.get("forma_pagamento") == "Prazo"), Decimal("0"))

        return {
            "data": dia,
            "vendas_brutas": vendas_brutas,
            "descontos": descontos,
            "cancelamentos": cancelamentos,
            "total_liquido": total_liquido,
            "dinheiro": dinheiro,
            "pix": pix,
            "cartao": cartao,
            "prazo": prazo,
            "total_recebido": dinheiro + pix + cartao + prazo,
            "qtd_vendas": sum((1 for v in vendas if v.get("status") != "CANCELADA")),
        }