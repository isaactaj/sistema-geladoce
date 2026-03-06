# app/database/repositories/agendamentos_repository.py
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from mysql.connector import Error
from app.database.connection import conectar


class AgendamentosRepository:
    """
    Tabelas:
      - agendamentos
      - agendamentos_carrinhos
    View:
      - vw_agendamentos_resumo

    Regras:
      - agendamento pode reservar N carrinhos (auto seleção)
      - carrinho_preferido_id opcional (se vier, tenta incluir)
      - motorista_id opcional (se vier, valida conflito)
      - conflito por sobreposição:
          NOT (fim_min <= novo_inicio OR inicio_min >= novo_fim)
      - considera apenas status <> 'Cancelado'
    """

    def _normalizar_status(self, status: Any) -> str:
        txt = str(status or "").strip()
        validos = {"Agendado", "Confirmado", "Cancelado"}
        return txt if txt in validos else "Agendado"

    def _to_int(self, v: Any, default: int = 0) -> int:
        try:
            return int(v)
        except Exception:
            return default

    def _validar_motorista(self, cur, motorista_id: Optional[int]) -> None:
        if motorista_id is None:
            return
        cur.execute("SELECT id, ativo FROM funcionarios WHERE id=%s LIMIT 1", (int(motorista_id),))
        row = cur.fetchone()
        if not row:
            raise ValueError("Motorista não encontrado.")
        ativo = int(row.get("ativo") or 0) if isinstance(row, dict) else int(row[1] or 0)
        if ativo != 1:
            raise ValueError("Motorista está inativo.")

    def _validar_carrinho_preferido(self, cur, carrinho_id: Optional[int]) -> None:
        if carrinho_id is None:
            return
        cur.execute("SELECT id, ativo, status FROM carrinhos WHERE id=%s LIMIT 1", (int(carrinho_id),))
        row = cur.fetchone()
        if not row:
            raise ValueError("Carrinho preferido não encontrado.")
        if isinstance(row, dict):
            ativo = int(row.get("ativo") or 0)
            status = str(row.get("status") or "")
        else:
            ativo = int(row[1] or 0)
            status = str(row[2] or "")
        if ativo != 1:
            raise ValueError("Carrinho preferido está inativo.")
        if status == "Manutenção":
            raise ValueError("Carrinho preferido está em Manutenção.")

    def _conflito_motorista(
        self,
        cur,
        data_ref: date,
        motorista_id: int,
        inicio_min: int,
        fim_min: int,
        agendamento_id: Optional[int],
    ) -> bool:
        params = [data_ref, int(motorista_id), int(fim_min), int(inicio_min)]
        sql = """
            SELECT id
            FROM agendamentos
            WHERE data=%s
              AND status <> 'Cancelado'
              AND motorista_id = %s
              AND NOT (fim_min <= %s OR inicio_min >= %s)
        """
        if agendamento_id is not None:
            sql += " AND id <> %s"
            params.append(int(agendamento_id))
        sql += " LIMIT 1"
        cur.execute(sql, tuple(params))
        return cur.fetchone() is not None

    def _carrinhos_ocupados(
        self,
        cur,
        data_ref: date,
        inicio_min: int,
        fim_min: int,
        agendamento_id: Optional[int],
    ) -> set:
        params = [data_ref, int(fim_min), int(inicio_min)]
        sql = """
            SELECT ac.carrinho_id
            FROM agendamentos a
            JOIN agendamentos_carrinhos ac ON ac.agendamento_id = a.id
            WHERE a.data = %s
              AND a.status <> 'Cancelado'
              AND NOT (a.fim_min <= %s OR a.inicio_min >= %s)
        """
        if agendamento_id is not None:
            sql += " AND a.id <> %s"
            params.append(int(agendamento_id))

        cur.execute(sql, tuple(params))
        rows = cur.fetchall() or []
        ocupados = set()
        for r in rows:
            if isinstance(r, dict):
                ocupados.add(int(r.get("carrinho_id")))
            else:
                ocupados.add(int(r[0]))
        return ocupados

    def _selecionar_carrinhos_disponiveis(
        self,
        cur,
        quantidade: int,
        ocupados: set,
        carrinho_preferido_id: Optional[int],
    ) -> List[int]:
        # Apenas carrinhos ativos e disponíveis
        cur.execute(
            """
            SELECT id
            FROM carrinhos
            WHERE ativo=1 AND status='Disponível'
            ORDER BY id ASC
            """
        )
        rows = cur.fetchall() or []
        candidatos = []
        for r in rows:
            cid = int(r.get("id")) if isinstance(r, dict) else int(r[0])
            if cid in ocupados:
                continue
            candidatos.append(cid)

        selecionados: List[int] = []

        if carrinho_preferido_id is not None:
            pid = int(carrinho_preferido_id)
            if pid in ocupados:
                raise ValueError("Carrinho preferido está ocupado nesse horário.")
            if pid not in candidatos:
                raise ValueError("Carrinho preferido não está disponível (status/ativo/ocupado).")
            selecionados.append(pid)

        for cid in candidatos:
            if len(selecionados) >= quantidade:
                break
            if carrinho_preferido_id is not None and cid == int(carrinho_preferido_id):
                continue
            selecionados.append(cid)

        if len(selecionados) < quantidade:
            raise ValueError("Não há carrinhos suficientes disponíveis para esse horário.")

        return selecionados

    def salvar_agendamento(
        self,
        data: date,
        inicio: str,
        fim: str,
        inicio_min: int,
        fim_min: int,
        quantidade_carrinhos: int,
        local: str,
        status: str = "Agendado",
        obs: str = "",
        carrinho_preferido_id: Optional[int] = None,
        motorista_id: Optional[int] = None,
        agendamento_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        st = self._normalizar_status(status)
        local = str(local or "").strip()
        if not local:
            raise ValueError("Local é obrigatório.")

        qtd = self._to_int(quantidade_carrinhos, 1)
        if qtd <= 0:
            qtd = 1

        obs_txt = str(obs or "").strip() or None
        carrinho_pref = int(carrinho_preferido_id) if carrinho_preferido_id not in (None, "", "None") else None
        motorista = int(motorista_id) if motorista_id not in (None, "", "None") else None

        conn = None
        cur = None
        try:
            conn = conectar()
            conn.start_transaction()
            cur = conn.cursor(dictionary=True)

            # valida entidades (se vierem)
            self._validar_motorista(cur, motorista)
            self._validar_carrinho_preferido(cur, carrinho_pref)

            # conflito motorista (se houver)
            if motorista is not None:
                if self._conflito_motorista(cur, data, motorista, inicio_min, fim_min, agendamento_id):
                    raise ValueError("Conflito: motorista já está agendado nesse horário.")

            # carrinhos ocupados por sobreposição
            ocupados = self._carrinhos_ocupados(cur, data, inicio_min, fim_min, agendamento_id)

            # escolhe carrinhos disponíveis
            carrinhos_escolhidos = self._selecionar_carrinhos_disponiveis(
                cur=cur,
                quantidade=qtd,
                ocupados=ocupados,
                carrinho_preferido_id=carrinho_pref,
            )

            # salva agendamento base
            if agendamento_id is None:
                cur.execute(
                    """
                    INSERT INTO agendamentos
                    (data, inicio, fim, inicio_min, fim_min,
                     quantidade_carrinhos, carrinho_preferido_id, motorista_id,
                     local, status, obs)
                    VALUES
                    (%s, %s, %s, %s, %s,
                     %s, %s, %s,
                     %s, %s, %s)
                    """,
                    (
                        data, inicio, fim, int(inicio_min), int(fim_min),
                        int(qtd), carrinho_pref, motorista,
                        local, st, obs_txt
                    ),
                )
                ag_id = int(cur.lastrowid)
            else:
                ag_id = int(agendamento_id)
                cur.execute(
                    """
                    UPDATE agendamentos
                    SET data=%s, inicio=%s, fim=%s, inicio_min=%s, fim_min=%s,
                        quantidade_carrinhos=%s,
                        carrinho_preferido_id=%s,
                        motorista_id=%s,
                        local=%s, status=%s, obs=%s
                    WHERE id=%s
                    """,
                    (
                        data, inicio, fim, int(inicio_min), int(fim_min),
                        int(qtd),
                        carrinho_pref,
                        motorista,
                        local, st, obs_txt,
                        ag_id
                    ),
                )
                if cur.rowcount == 0:
                    raise ValueError("Agendamento não encontrado para atualizar.")

                # refaz mapeamento
                cur.execute("DELETE FROM agendamentos_carrinhos WHERE agendamento_id=%s", (ag_id,))

            # insere mapeamento carrinhos
            for cid in carrinhos_escolhidos:
                cur.execute(
                    "INSERT INTO agendamentos_carrinhos (agendamento_id, carrinho_id) VALUES (%s, %s)",
                    (ag_id, int(cid)),
                )

            conn.commit()
            return self.obter_agendamento(ag_id) or {}

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

    def obter_agendamento(self, agendamento_id: int) -> Optional[Dict[str, Any]]:
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT * FROM vw_agendamentos_resumo WHERE id=%s LIMIT 1",
                (int(agendamento_id),),
            )
            return cur.fetchone()
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def listar_agendamentos(
        self,
        data: Optional[date] = None,
        data_inicial: Optional[date] = None,
        data_final: Optional[date] = None,
        incluir_cancelados: bool = False,
        limite: int = 2000,
    ) -> List[Dict[str, Any]]:
        where = []
        params: List[Any] = []

        if not incluir_cancelados:
            where.append("status <> 'Cancelado'")

        if data is not None:
            where.append("data = %s")
            params.append(data)
        else:
            if data_inicial is not None:
                where.append("data >= %s")
                params.append(data_inicial)
            if data_final is not None:
                where.append("data <= %s")
                params.append(data_final)

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                f"""
                SELECT *
                FROM vw_agendamentos_resumo
                {where_sql}
                ORDER BY data ASC, inicio_min ASC, id ASC
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

    def excluir_agendamento(self, agendamento_id: int) -> None:
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM agendamentos WHERE id=%s", (int(agendamento_id),))
            conn.commit()
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()