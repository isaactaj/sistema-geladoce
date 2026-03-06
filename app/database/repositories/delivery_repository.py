# app/database/repositories/delivery_repository.py
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.database.connection import conectar


class DeliveryRepository:
    """
    Tabelas:
      - delivery_pedidos
      - delivery_itens
      - produtos + estoque (para validar itens)
      - formas_pagamento (FK)

    Regras:
      - salva pedido + itens em UMA transação
      - valida produto ativo e não-insumo
      - valida estoque suficiente no momento do salvamento (não baixa aqui)
      - calcula subtotal/total (total = subtotal + taxa)
      - venda_id é só vínculo (gerado pelo SistemaService quando status exigir)
    """

    def _to_decimal(self, valor: Any) -> Decimal:
        if isinstance(valor, Decimal):
            return valor
        s = str(valor).strip().replace("R$", "").replace(" ", "")
        if not s:
            return Decimal("0")
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", ".")
        try:
            return Decimal(s)
        except Exception:
            return Decimal("0")

    def _listar_codigos_pagamento(self, cur) -> set:
        cur.execute("SELECT codigo FROM formas_pagamento")
        rows = cur.fetchall() or []
        # pode vir tuple
        return {r[0] for r in rows}

    def _normalizar_forma_pagamento(self, forma: str, codigos: set) -> str:
        f = str(forma or "").strip()
        if not f:
            raise ValueError("Forma de pagamento é obrigatória.")

        equivalencias = {
            "cartao": "Cartao",
            "cartão": "Cartão",
        }
        low = f.lower()
        if low in equivalencias:
            cand = equivalencias[low]
            if cand in codigos:
                return cand

        if f in codigos:
            return f

        # tenta fallback
        if low == "cartao" and "Cartao" in codigos:
            return "Cartao"
        if low == "cartão" and "Cartão" in codigos:
            return "Cartão"

        raise ValueError("Forma de pagamento inválida (não cadastrada em formas_pagamento).")

    def salvar_pedido(
        self,
        *,
        data: date,
        prev_saida: Optional[str],
        cliente_id: Optional[int],
        cliente_nome: str,
        cliente_telefone: str,
        end_rua: str,
        end_num: Optional[str],
        end_bairro: str,
        end_cidade: str,
        end_comp: Optional[str],
        entregador_id: Optional[int],
        forma_pagamento: str,
        status: str,
        taxa_entrega: Any,
        obs: str,
        itens: List[Dict[str, Any]],
        pedido_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        cliente_nome = str(cliente_nome or "").strip()
        cliente_telefone = str(cliente_telefone or "").strip()
        end_rua = str(end_rua or "").strip()
        end_bairro = str(end_bairro or "").strip()
        end_cidade = str(end_cidade or "").strip() or "Belém"
        status = str(status or "Pendente").strip()

        if not cliente_nome:
            raise ValueError("Nome do cliente é obrigatório.")
        if not cliente_telefone:
            raise ValueError("Telefone do cliente é obrigatório.")
        if not end_rua or not end_bairro:
            raise ValueError("Informe pelo menos Rua e Bairro.")
        if not itens:
            raise ValueError("Adicione ao menos 1 item ao pedido.")

        taxa = self._to_decimal(taxa_entrega)
        if taxa < 0:
            taxa = Decimal("0")

        # consolida itens
        consolidados: Dict[int, int] = {}
        for it in itens:
            pid = it.get("produto_id", it.get("id"))
            qtd = it.get("qtd", 0)
            pid = int(pid)
            qtd = int(qtd)
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
            forma_ok = self._normalizar_forma_pagamento(forma_pagamento, codigos)

            # garante linha de estoque (idempotente)
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
                    p.id, p.nome, p.preco, p.ativo, p.tipo_item, p.eh_insumo,
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

            itens_norm: List[Dict[str, Any]] = []
            subtotal = Decimal("0")

            for pid, qtd in consolidados.items():
                if pid not in mapa:
                    raise ValueError(f"Produto {pid} não encontrado.")

                r = mapa[pid]
                nome = r[1]
                preco = self._to_decimal(r[2])
                ativo = int(r[3] or 0)
                tipo_item = str(r[4] or "Produto")
                eh_insumo = int(r[5] or 0)
                estoque_atual = int(r[6] or 0)

                if ativo != 1:
                    raise ValueError(f"Produto inativo: {nome}.")
                if tipo_item == "Insumo" or eh_insumo == 1:
                    raise ValueError(f"Item é insumo e não pode ser vendido: {nome}.")
                if estoque_atual < qtd:
                    raise ValueError(f"Estoque insuficiente para {nome}.")

                total_item = preco * qtd
                itens_norm.append({
                    "produto_id": pid,
                    "produto_nome": nome,
                    "qtd": qtd,
                    "unitario": preco,
                    "total": total_item,
                })
                subtotal += total_item

            total = subtotal + taxa

            if pedido_id is None:
                cur.execute(
                    """
                    INSERT INTO delivery_pedidos
                    (data, prev_saida, cliente_id, cliente_nome, cliente_telefone,
                     end_rua, end_num, end_bairro, end_cidade, end_comp,
                     entregador_id, forma_pagamento, status, taxa_entrega,
                     subtotal, total, obs, venda_id)
                    VALUES
                    (%s, %s, %s, %s, %s,
                     %s, %s, %s, %s, %s,
                     %s, %s, %s, %s,
                     %s, %s, %s, NULL)
                    """,
                    (
                        data,
                        (str(prev_saida).strip() if prev_saida else None),
                        int(cliente_id) if cliente_id else None,
                        cliente_nome,
                        cliente_telefone,
                        end_rua,
                        (str(end_num).strip() if end_num else None),
                        end_bairro,
                        end_cidade,
                        (str(end_comp).strip() if end_comp else None),
                        int(entregador_id) if entregador_id else None,
                        forma_ok,
                        status,
                        taxa,
                        subtotal,
                        total,
                        (str(obs).strip() or None),
                    ),
                )
                pid_salvo = int(cur.lastrowid)
            else:
                pid_salvo = int(pedido_id)
                cur.execute(
                    """
                    UPDATE delivery_pedidos
                    SET
                        data=%s,
                        prev_saida=%s,
                        cliente_id=%s,
                        cliente_nome=%s,
                        cliente_telefone=%s,
                        end_rua=%s,
                        end_num=%s,
                        end_bairro=%s,
                        end_cidade=%s,
                        end_comp=%s,
                        entregador_id=%s,
                        forma_pagamento=%s,
                        status=%s,
                        taxa_entrega=%s,
                        subtotal=%s,
                        total=%s,
                        obs=%s
                    WHERE id=%s
                    """,
                    (
                        data,
                        (str(prev_saida).strip() if prev_saida else None),
                        int(cliente_id) if cliente_id else None,
                        cliente_nome,
                        cliente_telefone,
                        end_rua,
                        (str(end_num).strip() if end_num else None),
                        end_bairro,
                        end_cidade,
                        (str(end_comp).strip() if end_comp else None),
                        int(entregador_id) if entregador_id else None,
                        forma_ok,
                        status,
                        taxa,
                        subtotal,
                        total,
                        (str(obs).strip() or None),
                        pid_salvo,
                    ),
                )
                if cur.rowcount == 0:
                    raise ValueError("Pedido não encontrado para atualizar.")

                # remove itens anteriores
                cur.execute("DELETE FROM delivery_itens WHERE pedido_id=%s", (pid_salvo,))

            # insere itens
            for it in itens_norm:
                cur.execute(
                    """
                    INSERT INTO delivery_itens (pedido_id, produto_id, qtd, unitario, total)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (pid_salvo, int(it["produto_id"]), int(it["qtd"]), it["unitario"], it["total"]),
                )

            conn.commit()
            return self.obter_pedido(pid_salvo) or {}

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

    def vincular_venda(self, pedido_id: int, venda_id: int) -> None:
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("UPDATE delivery_pedidos SET venda_id=%s WHERE id=%s", (int(venda_id), int(pedido_id)))
            conn.commit()
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def obter_pedido(self, pedido_id: int) -> Optional[Dict[str, Any]]:
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)

            cur.execute(
                """
                SELECT
                    p.*,
                    f.nome AS entregador_nome,
                    f.telefone AS entregador_telefone
                FROM delivery_pedidos p
                LEFT JOIN funcionarios f ON f.id = p.entregador_id
                WHERE p.id=%s
                LIMIT 1
                """,
                (int(pedido_id),),
            )
            pedido = cur.fetchone()
            if not pedido:
                return None

            cur.execute(
                """
                SELECT
                    i.produto_id,
                    pr.nome AS produto_nome,
                    i.qtd,
                    i.unitario,
                    i.total
                FROM delivery_itens i
                JOIN produtos pr ON pr.id = i.produto_id
                WHERE i.pedido_id=%s
                ORDER BY i.id ASC
                """,
                (int(pedido_id),),
            )
            itens = cur.fetchall() or []
            pedido["itens"] = itens
            return pedido

        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def listar_por_data(self, dia: date, limite: int = 2000) -> List[Dict[str, Any]]:
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                """
                SELECT
                    p.id,
                    p.data,
                    p.prev_saida,
                    p.cliente_nome,
                    p.cliente_telefone,
                    p.total,
                    p.status,
                    p.forma_pagamento,
                    p.taxa_entrega,
                    p.entregador_id,
                    f.nome AS entregador_nome,
                    p.venda_id
                FROM delivery_pedidos p
                LEFT JOIN funcionarios f ON f.id = p.entregador_id
                WHERE p.data=%s
                ORDER BY (p.prev_saida IS NULL) ASC, p.prev_saida ASC, p.id DESC
                LIMIT %s
                """,
                (dia, int(limite)),
            )
            return cur.fetchall() or []
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def excluir_pedido(self, pedido_id: int) -> None:
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM delivery_pedidos WHERE id=%s", (int(pedido_id),))
            conn.commit()
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()