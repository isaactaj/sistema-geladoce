# app/database/repositories/agendamentos_repository.py
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from app.database.connection import conectar


class AgendamentosRepository:
    """
    Repositório compatível com o schema atual:

    Tabela principal:
      - agendamentos

    Relacionamentos usados:
      - carrinhos
      - funcionarios

    Regras:
      - 1 carrinho por agendamento
      - 1 motorista por agendamento
      - conflito por sobreposição:
          NOT (fim_min <= novo_inicio OR inicio_min >= novo_fim)
      - considera apenas status <> 'Cancelado'
    """

    STATUS_VALIDOS = {"Agendado", "Confirmado", "Cancelado"}

    def _normalizar_status(self, status: Any) -> str:
        txt = str(status or "").strip()
        return txt if txt in self.STATUS_VALIDOS else "Agendado"

    def _to_int(self, v: Any, default: int = 0) -> int:
        try:
            return int(v)
        except Exception:
            return default

    def _normalizar_row(self, row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not row:
            return None

        row["id"] = int(row.get("id") or 0)
        row["inicio_min"] = int(row.get("inicio_min") or 0)
        row["fim_min"] = int(row.get("fim_min") or 0)
        row["carrinho_id"] = int(row.get("carrinho_id") or 0) if row.get("carrinho_id") is not None else None
        row["motorista_id"] = int(row.get("motorista_id") or 0) if row.get("motorista_id") is not None else None

        # Compatibilidade com estruturas antigas
        row["quantidade_carrinhos"] = 1 if row.get("carrinho_id") else 0
        row["carrinho_preferido_id"] = row.get("carrinho_id")
        row["observacao"] = row.get("obs")

        if row.get("carrinho_id"):
            row["carrinhos"] = [
                {
                    "id": row.get("carrinho_id"),
                    "nome": row.get("carrinho_nome"),
                    "id_externo": row.get("carrinho_id_externo"),
                }
            ]
        else:
            row["carrinhos"] = []

        return row

    def _validar_motorista(self, cur, motorista_id: Optional[int]) -> None:
        if motorista_id is None:
            return

        cur.execute(
            """
            SELECT id, nome, ativo
            FROM funcionarios
            WHERE id = %s
            LIMIT 1
            """,
            (int(motorista_id),),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Motorista não encontrado.")

        ativo = int(row.get("ativo") or 0)
        if ativo != 1:
            raise ValueError("Motorista está inativo.")

    def _validar_carrinho(self, cur, carrinho_id: Optional[int]) -> None:
        if carrinho_id is None:
            return

        cur.execute(
            """
            SELECT id, nome, ativo, status
            FROM carrinhos
            WHERE id = %s
            LIMIT 1
            """,
            (int(carrinho_id),),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Carrinho não encontrado.")

        ativo = int(row.get("ativo") or 0)
        status = str(row.get("status") or "").strip()

        if ativo != 1:
            raise ValueError("Carrinho está inativo.")

        if status == "Manutenção":
            raise ValueError("Carrinho está em manutenção.")

    def _conflito_motorista(
        self,
        cur,
        data_ref: date,
        motorista_id: int,
        inicio_min: int,
        fim_min: int,
        agendamento_id: Optional[int],
    ) -> bool:
        params: List[Any] = [data_ref, int(motorista_id), int(fim_min), int(inicio_min)]
        sql = """
            SELECT id
            FROM agendamentos
            WHERE data = %s
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

    def _conflito_carrinho(
        self,
        cur,
        data_ref: date,
        carrinho_id: int,
        inicio_min: int,
        fim_min: int,
        agendamento_id: Optional[int],
    ) -> bool:
        params: List[Any] = [data_ref, int(carrinho_id), int(fim_min), int(inicio_min)]
        sql = """
            SELECT id
            FROM agendamentos
            WHERE data = %s
              AND status <> 'Cancelado'
              AND carrinho_id = %s
              AND NOT (fim_min <= %s OR inicio_min >= %s)
        """

        if agendamento_id is not None:
            sql += " AND id <> %s"
            params.append(int(agendamento_id))

        sql += " LIMIT 1"
        cur.execute(sql, tuple(params))
        return cur.fetchone() is not None

    def salvar_agendamento(
        self,
        data: date,
        inicio: str,
        fim: str,
        inicio_min: int,
        fim_min: int,
        carrinho_id: Optional[int] = None,
        motorista_id: Optional[int] = None,
        local: str = "",
        status: str = "Agendado",
        obs: str = "",
        agendamento_id: Optional[int] = None,
        # compatibilidade com chamadas antigas
        id_carrinho: Optional[int] = None,
        funcionario_id: Optional[int] = None,
        observacao: Optional[str] = None,
        quantidade_carrinhos: Optional[int] = None,
        carrinho_preferido_id: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Compatibiliza chamadas novas e antigas:
        - carrinho_id / id_carrinho / carrinho_preferido_id
        - motorista_id / funcionario_id
        - obs / observacao
        """

        if carrinho_id in (None, "", "None"):
            if id_carrinho not in (None, "", "None"):
                carrinho_id = id_carrinho
            elif carrinho_preferido_id not in (None, "", "None"):
                carrinho_id = carrinho_preferido_id

        if motorista_id in (None, "", "None") and funcionario_id not in (None, "", "None"):
            motorista_id = funcionario_id

        if (obs is None or str(obs).strip() == "") and observacao not in (None, ""):
            obs = observacao

        local = str(local or "").strip()
        if not local:
            raise ValueError("Local é obrigatório.")

        if carrinho_id in (None, "", "None"):
            raise ValueError("Carrinho é obrigatório.")

        if motorista_id in (None, "", "None"):
            raise ValueError("Motorista é obrigatório.")

        st = self._normalizar_status(status)
        carrinho_id = int(carrinho_id)
        motorista_id = int(motorista_id)
        obs_txt = str(obs or "").strip() or None

        conn = None
        cur = None
        try:
            conn = conectar()
            conn.start_transaction()
            cur = conn.cursor(dictionary=True)

            # valida entidades
            self._validar_carrinho(cur, carrinho_id)
            self._validar_motorista(cur, motorista_id)

            # valida conflito de carrinho
            if self._conflito_carrinho(cur, data, carrinho_id, inicio_min, fim_min, agendamento_id):
                raise ValueError("Conflito: carrinho já está agendado nesse horário.")

            # valida conflito de motorista
            if self._conflito_motorista(cur, data, motorista_id, inicio_min, fim_min, agendamento_id):
                raise ValueError("Conflito: motorista já está agendado nesse horário.")

            if agendamento_id is None:
                cur.execute(
                    """
                    INSERT INTO agendamentos
                    (data, inicio, fim, inicio_min, fim_min,
                     carrinho_id, motorista_id, local, status, obs)
                    VALUES
                    (%s, %s, %s, %s, %s,
                     %s, %s, %s, %s, %s)
                    """,
                    (
                        data,
                        inicio,
                        fim,
                        int(inicio_min),
                        int(fim_min),
                        carrinho_id,
                        motorista_id,
                        local,
                        st,
                        obs_txt,
                    ),
                )
                ag_id = int(cur.lastrowid)
            else:
                ag_id = int(agendamento_id)

                cur.execute("SELECT id FROM agendamentos WHERE id = %s LIMIT 1", (ag_id,))
                existe = cur.fetchone()
                if not existe:
                    raise ValueError("Agendamento não encontrado para atualizar.")

                cur.execute(
                    """
                    UPDATE agendamentos
                    SET
                        data = %s,
                        inicio = %s,
                        fim = %s,
                        inicio_min = %s,
                        fim_min = %s,
                        carrinho_id = %s,
                        motorista_id = %s,
                        local = %s,
                        status = %s,
                        obs = %s
                    WHERE id = %s
                    """,
                    (
                        data,
                        inicio,
                        fim,
                        int(inicio_min),
                        int(fim_min),
                        carrinho_id,
                        motorista_id,
                        local,
                        st,
                        obs_txt,
                        ag_id,
                    ),
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
                """
                SELECT
                    a.id,
                    a.data,
                    a.inicio,
                    a.fim,
                    a.inicio_min,
                    a.fim_min,
                    a.carrinho_id,
                    a.motorista_id,
                    a.local,
                    a.status,
                    a.obs,
                    a.cadastro,
                    c.nome AS carrinho_nome,
                    c.id_externo AS carrinho_id_externo,
                    f.nome AS motorista_nome
                FROM agendamentos a
                LEFT JOIN carrinhos c ON c.id = a.carrinho_id
                LEFT JOIN funcionarios f ON f.id = a.motorista_id
                WHERE a.id = %s
                LIMIT 1
                """,
                (int(agendamento_id),),
            )
            return self._normalizar_row(cur.fetchone())
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
            where.append("a.status <> 'Cancelado'")

        if data is not None:
            where.append("a.data = %s")
            params.append(data)
        else:
            if data_inicial is not None:
                where.append("a.data >= %s")
                params.append(data_inicial)
            if data_final is not None:
                where.append("a.data <= %s")
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
                    a.id,
                    a.data,
                    a.inicio,
                    a.fim,
                    a.inicio_min,
                    a.fim_min,
                    a.carrinho_id,
                    a.motorista_id,
                    a.local,
                    a.status,
                    a.obs,
                    a.cadastro,
                    c.nome AS carrinho_nome,
                    c.id_externo AS carrinho_id_externo,
                    f.nome AS motorista_nome
                FROM agendamentos a
                LEFT JOIN carrinhos c ON c.id = a.carrinho_id
                LEFT JOIN funcionarios f ON f.id = a.motorista_id
                {where_sql}
                ORDER BY a.data ASC, a.inicio_min ASC, a.id ASC
                LIMIT %s
                """,
                tuple(params + [int(limite)]),
            )
            rows = cur.fetchall() or []
            return [self._normalizar_row(r) for r in rows]
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
            cur.execute("DELETE FROM agendamentos WHERE id = %s", (int(agendamento_id),))
            conn.commit()
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()