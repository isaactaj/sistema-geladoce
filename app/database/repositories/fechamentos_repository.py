from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.database.connection import conectar


class FechamentosRepository:
    """
    Tabela: fechamentos
    View: vw_fechamentos_resumo

    Regra:
    - fechamentos guarda caixa_inicial/sangria/contado_caixa/obs/responsável
    - totais vêm da view (derivados das vendas)
    - ao salvar fechamento, vincula vendas do dia (se ainda não estiverem vinculadas)
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

    def salvar_fechamento(
        self,
        data: date,
        caixa_inicial: Decimal,
        sangria: Decimal,
        contado_caixa: Decimal,
        observacao: str = "",
        responsavel_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        conn = None
        cur = None
        try:
            conn = conectar()
            conn.start_transaction()
            cur = conn.cursor()

            # upsert por data e devolve id usando LAST_INSERT_ID
            cur.execute(
                """
                INSERT INTO fechamentos (data, caixa_inicial, sangria, contado_caixa, observacao, responsavel_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    caixa_inicial=VALUES(caixa_inicial),
                    sangria=VALUES(sangria),
                    contado_caixa=VALUES(contado_caixa),
                    observacao=VALUES(observacao),
                    responsavel_id=VALUES(responsavel_id),
                    id=LAST_INSERT_ID(id)
                """,
                (
                    data,
                    self._to_decimal(caixa_inicial),
                    self._to_decimal(sangria),
                    self._to_decimal(contado_caixa),
                    (str(observacao).strip() or None),
                    responsavel_id,
                ),
            )
            fechamento_id = int(cur.lastrowid)

            # vincula vendas do dia que ainda não têm fechamento_id
            cur.execute(
                """
                UPDATE vendas
                SET fechamento_id = %s
                WHERE fechamento_id IS NULL AND DATE(data) = %s
                """,
                (fechamento_id, data),
            )

            conn.commit()

            # retorna fechamento + resumo (view)
            return self.obter_por_id(fechamento_id) or {}

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

    def obter_por_id(self, fechamento_id: int) -> Optional[Dict[str, Any]]:
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)

            cur.execute(
                """
                SELECT
                    f.id, f.data, f.caixa_inicial, f.sangria, f.contado_caixa,
                    f.observacao, f.responsavel_id,
                    f.criado_em, f.atualizado_em
                FROM fechamentos f
                WHERE f.id = %s
                LIMIT 1
                """,
                (int(fechamento_id),),
            )
            base = cur.fetchone()
            if not base:
                return None

            # anexa resumo
            cur.execute(
                """
                SELECT *
                FROM vw_fechamentos_resumo
                WHERE fechamento_id = %s
                LIMIT 1
                """,
                (int(fechamento_id),),
            )
            resumo = cur.fetchone() or {}

            base.update({
                "vendas_brutas": self._to_decimal(resumo.get("vendas_brutas", 0)),
                "descontos": self._to_decimal(resumo.get("descontos", 0)),
                "cancelamentos": self._to_decimal(resumo.get("cancelamentos", 0)),
                "total_liquido": self._to_decimal(resumo.get("total_liquido", 0)),
                "dinheiro": self._to_decimal(resumo.get("dinheiro", 0)),
                "pix": self._to_decimal(resumo.get("pix", 0)),
                "cartao": self._to_decimal(resumo.get("cartao", 0)),
                "prazo": self._to_decimal(resumo.get("prazo", 0)),
                "total_recebido": self._to_decimal(resumo.get("total_recebido", 0)),
                "previsto_em_caixa": self._to_decimal(resumo.get("previsto_em_caixa", 0)),
                "diferenca": self._to_decimal(resumo.get("diferenca", 0)),
                "qtd_vendas": int(resumo.get("qtd_vendas", 0) or 0),
            })

            return base
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def obter_por_data(self, data: date) -> Optional[Dict[str, Any]]:
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id FROM fechamentos WHERE data = %s LIMIT 1", (data,))
            row = cur.fetchone()
            if not row:
                return None
            return self.obter_por_id(int(row["id"]))
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def listar_fechamentos(self, data_inicial: Optional[date] = None, data_final: Optional[date] = None, limite: int = 500) -> List[Dict[str, Any]]:
        where = []
        params: List[Any] = []
        if data_inicial:
            where.append("f.data >= %s")
            params.append(data_inicial)
        if data_final:
            where.append("f.data <= %s")
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
                    r.fechamento_id AS id,
                    r.data_fechamento AS data,
                    f.caixa_inicial, f.sangria, f.contado_caixa,
                    f.observacao, f.responsavel_id,
                    f.criado_em, f.atualizado_em,
                    r.vendas_brutas, r.descontos, r.cancelamentos, r.total_liquido,
                    r.dinheiro, r.pix, r.cartao, r.prazo,
                    r.total_recebido, r.previsto_em_caixa, r.diferenca, r.qtd_vendas
                FROM vw_fechamentos_resumo r
                JOIN fechamentos f ON f.id = r.fechamento_id
                {where_sql}
                ORDER BY r.data_fechamento DESC
                LIMIT %s
                """,
                tuple(params + [int(limite)]),
            )
            return cur.fetchall() or []
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def resumo_por_data(self, data: date) -> Optional[Dict[str, Any]]:
        """
        Se existir fechamento do dia, retorna view.
        Se não existir, retorna None.
        """
        row = self.obter_por_data(data)
        if not row:
            return None

        return {
            "data": row["data"],
            "vendas_brutas": self._to_decimal(row.get("vendas_brutas", 0)),
            "descontos": self._to_decimal(row.get("descontos", 0)),
            "cancelamentos": self._to_decimal(row.get("cancelamentos", 0)),
            "total_liquido": self._to_decimal(row.get("total_liquido", 0)),
            "dinheiro": self._to_decimal(row.get("dinheiro", 0)),
            "pix": self._to_decimal(row.get("pix", 0)),
            "cartao": self._to_decimal(row.get("cartao", 0)),
            "prazo": self._to_decimal(row.get("prazo", 0)),
            "total_recebido": self._to_decimal(row.get("total_recebido", 0)),
            "previsto_em_caixa": self._to_decimal(row.get("previsto_em_caixa", 0)),
            "diferenca": self._to_decimal(row.get("diferenca", 0)),
            "qtd_vendas": int(row.get("qtd_vendas", 0) or 0),
        }