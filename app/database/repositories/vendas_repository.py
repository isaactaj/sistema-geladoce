from __future__ import annotations

from datetime import datetime, date, time
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.database.connection import conectar


class VendasRepository:
    """
    Repositório de vendas do Geladoce.

    Compatível com:
    - SistemaService.registrar_venda(...)
    - SistemaService.listar_vendas(...)
    - SistemaService.resumo_fechamento(...)
    - Dashboard de relatórios
    """

    # ======================================================
    # HELPERS
    # ======================================================
    def _to_decimal(self, valor: Any) -> Decimal:
        if isinstance(valor, Decimal):
            return valor
        try:
            txt = str(valor).strip().replace("R$", "").replace(" ", "")
            if not txt:
                return Decimal("0")
            if "," in txt and "." in txt:
                txt = txt.replace(".", "").replace(",", ".")
            else:
                txt = txt.replace(",", ".")
            return Decimal(txt)
        except Exception:
            return Decimal("0")

    def _normalizar_datetime(self, valor: Any) -> datetime:
        if isinstance(valor, datetime):
            return valor
        if isinstance(valor, date):
            return datetime.combine(valor, time.min)

        txt = str(valor).strip()
        formatos = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
        ]
        for fmt in formatos:
            try:
                return datetime.strptime(txt, fmt)
            except Exception:
                pass
        return datetime.now()

    def _buscar_produto(self, cur, produto_id: int) -> Optional[Dict[str, Any]]:
        sql = """
            SELECT
                p.id,
                p.nome,
                p.categoria,
                p.preco,
                p.ativo,
                p.tipo_item,
                p.eh_insumo,
                COALESCE(e.quantidade, 0) AS estoque_atual
            FROM produtos p
            LEFT JOIN estoque e
                ON e.produto_id = p.id
            WHERE p.id = %s
        """
        cur.execute(sql, (int(produto_id),))
        return cur.fetchone()

    def _listar_itens_da_venda(self, cur, venda_id: int) -> List[Dict[str, Any]]:
        sql = """
            SELECT
                vi.id,
                vi.venda_id,
                vi.produto_id,
                p.nome AS produto_nome,
                p.categoria AS categoria,
                vi.qtd,
                vi.unitario,
                vi.total
            FROM vendas_itens vi
            INNER JOIN produtos p
                ON p.id = vi.produto_id
            WHERE vi.venda_id = %s
            ORDER BY vi.id
        """
        cur.execute(sql, (int(venda_id),))
        rows = cur.fetchall() or []

        itens = []
        for r in rows:
            itens.append({
                "id": r["id"],
                "venda_id": r["venda_id"],
                "produto_id": r["produto_id"],
                "produto_nome": r["produto_nome"],
                "nome": r["produto_nome"],
                "categoria": r["categoria"],
                "qtd": int(r["qtd"] or 0),
                "unitario": self._to_decimal(r["unitario"]),
                "total": self._to_decimal(r["total"]),
            })
        return itens

    # ======================================================
    # REGISTRAR VENDA
    # ======================================================
    def registrar_venda(
        self,
        tipo: str,
        itens: List[Dict[str, Any]],
        forma_pagamento: str,
        cliente_id: Optional[int] = None,
        revendedor_id: Optional[int] = None,
        desconto: Any = 0,
        taxa_entrega: Any = 0,
        observacao: str = "",
        data_venda: Optional[Any] = None,
        status: str = "FINALIZADA",
    ) -> Dict[str, Any]:
        if not itens:
            raise ValueError("A venda precisa ter ao menos 1 item.")

        tipo = str(tipo).strip().upper()
        status = str(status).strip().upper()
        forma_pagamento = str(forma_pagamento).strip()
        desconto_dec = self._to_decimal(desconto)
        taxa_entrega_dec = self._to_decimal(taxa_entrega)
        data_ref = self._normalizar_datetime(data_venda) if data_venda else datetime.now()

        conn = None
        cur = None

        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)

            subtotal = Decimal("0")
            itens_processados: List[Dict[str, Any]] = []

            for item in itens:
                produto_id = int(item.get("produto_id") or item.get("id"))
                qtd = int(item.get("qtd") or 0)

                if qtd <= 0:
                    raise ValueError(f"Quantidade inválida para o produto {produto_id}.")

                prod = self._buscar_produto(cur, produto_id)
                if not prod:
                    raise ValueError(f"Produto {produto_id} não encontrado.")

                unitario = self._to_decimal(prod["preco"])
                total_item = unitario * Decimal(qtd)

                subtotal += total_item

                itens_processados.append({
                    "produto_id": produto_id,
                    "produto_nome": prod["nome"],
                    "categoria": prod["categoria"],
                    "qtd": qtd,
                    "unitario": unitario,
                    "total": total_item,
                    "estoque_atual": int(prod.get("estoque_atual") or 0),
                })

            total = subtotal - desconto_dec + taxa_entrega_dec
            if total < 0:
                total = Decimal("0")

            sql_venda = """
                INSERT INTO vendas (
                    tipo,
                    status,
                    data,
                    cliente_id,
                    revendedor_id,
                    fechamento_id,
                    forma_pagamento,
                    observacao,
                    subtotal,
                    desconto,
                    taxa_entrega,
                    total
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(
                sql_venda,
                (
                    tipo,
                    status,
                    data_ref,
                    int(cliente_id) if cliente_id else None,
                    int(revendedor_id) if revendedor_id else None,
                    None,
                    forma_pagamento,
                    str(observacao or "").strip(),
                    subtotal,
                    desconto_dec,
                    taxa_entrega_dec,
                    total,
                ),
            )
            venda_id = int(cur.lastrowid)

            sql_item = """
                INSERT INTO vendas_itens (
                    venda_id,
                    produto_id,
                    qtd,
                    unitario,
                    total
                ) VALUES (%s, %s, %s, %s, %s)
            """

            for item in itens_processados:
                cur.execute(
                    sql_item,
                    (
                        venda_id,
                        item["produto_id"],
                        item["qtd"],
                        item["unitario"],
                        item["total"],
                    ),
                )

                # Se existir linha no estoque, reduz
                cur.execute(
                    "SELECT quantidade FROM estoque WHERE produto_id = %s",
                    (item["produto_id"],),
                )
                row_est = cur.fetchone()
                if row_est is not None:
                    quantidade_atual = int(row_est["quantidade"] or 0)
                    nova_qtd = quantidade_atual - int(item["qtd"])
                    if nova_qtd < 0:
                        nova_qtd = 0

                    cur.execute(
                        "UPDATE estoque SET quantidade = %s WHERE produto_id = %s",
                        (nova_qtd, item["produto_id"]),
                    )

            conn.commit()

            return {
                "id": venda_id,
                "tipo": tipo,
                "status": status,
                "data": data_ref,
                "cliente_id": int(cliente_id) if cliente_id else None,
                "revendedor_id": int(revendedor_id) if revendedor_id else None,
                "fechamento_id": None,
                "forma_pagamento": forma_pagamento,
                "observacao": str(observacao or "").strip(),
                "subtotal": subtotal,
                "desconto": desconto_dec,
                "taxa_entrega": taxa_entrega_dec,
                "total": total,
                "itens": itens_processados,
            }

        except Exception:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise

        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    # ======================================================
    # LISTAR VENDAS
    # ======================================================
    def listar_vendas(
        self,
        tipo: Optional[str] = None,
        data_inicial: Optional[datetime] = None,
        data_final: Optional[datetime] = None,
        incluir_itens: bool = False,
    ) -> List[Dict[str, Any]]:
        conn = None
        cur = None

        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)

            sql = """
                SELECT
                    v.id,
                    v.tipo,
                    v.status,
                    v.data,
                    v.cliente_id,
                    c.nome AS cliente_nome,
                    v.revendedor_id,
                    r.nome AS revendedor_nome,
                    v.fechamento_id,
                    v.forma_pagamento,
                    v.observacao,
                    v.subtotal,
                    v.desconto,
                    v.taxa_entrega,
                    v.total
                FROM vendas v
                LEFT JOIN clientes c
                    ON c.id = v.cliente_id
                LEFT JOIN clientes r
                    ON r.id = v.revendedor_id
                WHERE 1=1
            """
            params: List[Any] = []

            if tipo:
                sql += " AND v.tipo = %s"
                params.append(str(tipo).strip().upper())

            if data_inicial:
                sql += " AND v.data >= %s"
                params.append(self._normalizar_datetime(data_inicial))

            if data_final:
                sql += " AND v.data <= %s"
                params.append(self._normalizar_datetime(data_final))

            sql += " ORDER BY v.data ASC, v.id ASC"

            cur.execute(sql, tuple(params))
            rows = cur.fetchall() or []

            saida: List[Dict[str, Any]] = []
            for r in rows:
                venda = {
                    "id": int(r["id"]),
                    "tipo": r["tipo"],
                    "status": r["status"],
                    "data": r["data"],
                    "cliente_id": r["cliente_id"],
                    "cliente_nome": r.get("cliente_nome"),
                    "revendedor_id": r["revendedor_id"],
                    "revendedor_nome": r.get("revendedor_nome"),
                    "fechamento_id": r["fechamento_id"],
                    "forma_pagamento": r["forma_pagamento"],
                    "observacao": r["observacao"],
                    "subtotal": self._to_decimal(r["subtotal"]),
                    "desconto": self._to_decimal(r["desconto"]),
                    "taxa_entrega": self._to_decimal(r["taxa_entrega"]),
                    "total": self._to_decimal(r["total"]),
                    "itens": [],
                }

                if incluir_itens:
                    venda["itens"] = self._listar_itens_da_venda(cur, venda["id"])

                saida.append(venda)

            return saida

        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    # ======================================================
    # RESUMO POR DIA
    # ======================================================
    def resumo_por_dia(self, dia: date) -> Dict[str, Any]:
        conn = None
        cur = None

        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)

            sql = """
                SELECT
                    COALESCE(SUM(CASE WHEN status <> 'CANCELADA' THEN subtotal ELSE 0 END), 0) AS vendas_brutas,
                    COALESCE(SUM(CASE WHEN status <> 'CANCELADA' THEN desconto ELSE 0 END), 0) AS descontos,
                    COALESCE(SUM(CASE WHEN status = 'CANCELADA' THEN total ELSE 0 END), 0) AS cancelamentos,
                    COALESCE(SUM(CASE WHEN status <> 'CANCELADA' THEN total ELSE 0 END), 0) AS total_liquido,

                    COALESCE(SUM(CASE WHEN status <> 'CANCELADA' AND forma_pagamento = 'Dinheiro' THEN total ELSE 0 END), 0) AS dinheiro,
                    COALESCE(SUM(CASE WHEN status <> 'CANCELADA' AND forma_pagamento = 'Pix' THEN total ELSE 0 END), 0) AS pix,
                    COALESCE(SUM(CASE WHEN status <> 'CANCELADA' AND forma_pagamento IN ('Cartão', 'Cartao') THEN total ELSE 0 END), 0) AS cartao,
                    COALESCE(SUM(CASE WHEN status <> 'CANCELADA' AND forma_pagamento = 'Prazo' THEN total ELSE 0 END), 0) AS prazo,

                    COALESCE(COUNT(CASE WHEN status <> 'CANCELADA' THEN 1 END), 0) AS qtd_vendas
                FROM vendas
                WHERE DATE(data) = %s
            """
            cur.execute(sql, (dia,))
            row = cur.fetchone() or {}

            return {
                "data_fechamento": dia,
                "vendas_brutas": self._to_decimal(row.get("vendas_brutas", 0)),
                "descontos": self._to_decimal(row.get("descontos", 0)),
                "cancelamentos": self._to_decimal(row.get("cancelamentos", 0)),
                "total_liquido": self._to_decimal(row.get("total_liquido", 0)),
                "dinheiro": self._to_decimal(row.get("dinheiro", 0)),
                "pix": self._to_decimal(row.get("pix", 0)),
                "cartao": self._to_decimal(row.get("cartao", 0)),
                "prazo": self._to_decimal(row.get("prazo", 0)),
                "total_recebido": self._to_decimal(row.get("total_liquido", 0)),
                "qtd_vendas": int(row.get("qtd_vendas", 0) or 0),
            }

        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()