# app/database/repositories/agendamentos_repository.py
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from app.database.connection import conectar


class AgendamentosRepository:
    """
    - Motoristas = funcionarios (compatível com seu schema atual)
    - Suporta N carrinhos via tabela agendamentos_carrinhos
    """

    def _normalizar_status(self, status: Any) -> str:
        txt = str(status or "").strip()
        validos = {"Agendado", "Confirmado", "Cancelado"}
        return txt if txt in validos else "Agendado"

    def _validar_carrinho_ativo(self, cur, carrinho_id: int) -> None:
        cur.execute("SELECT id, ativo FROM carrinhos WHERE id=%s LIMIT 1", (int(carrinho_id),))
        c = cur.fetchone()
        if not c or int(c.get("ativo") or 0) != 1:
            raise ValueError("Carrinho não encontrado ou inativo.")

    def _validar_motorista_ativo(self, cur, motorista_id: int) -> None:
        cur.execute("SELECT id, ativo FROM funcionarios WHERE id=%s LIMIT 1", (int(motorista_id),))
        f = cur.fetchone()
        if not f or int(f.get("ativo") or 0) != 1:
            raise ValueError("Motorista/Funcionário não encontrado ou inativo.")

    def _carrinho_ocupado(
        self,
        cur,
        data_ref: date,
        inicio_min: int,
        fim_min: int,
        carrinho_id: int,
        excluir_agendamento_id: Optional[int],
    ) -> bool:
        params: List[Any] = [data_ref, int(carrinho_id), int(fim_min), int(inicio_min)]
        sql = """
            SELECT 1
            FROM agendamentos a
            JOIN agendamentos_carrinhos ac ON ac.agendamento_id = a.id
            WHERE a.data = %s
              AND a.status <> 'Cancelado'
              AND ac.carrinho_id = %s
              AND NOT (a.fim_min <= %s OR a.inicio_min >= %s)
        """
        if excluir_agendamento_id is not None:
            sql += " AND a.id <> %s"
            params.append(int(excluir_agendamento_id))
        sql += " LIMIT 1"
        cur.execute(sql, tuple(params))
        return cur.fetchone() is not None

    def _motorista_ocupado(
        self,
        cur,
        data_ref: date,
        inicio_min: int,
        fim_min: int,
        motorista_id: int,
        excluir_agendamento_id: Optional[int],
    ) -> bool:
        params: List[Any] = [data_ref, int(motorista_id), int(fim_min), int(inicio_min)]
        sql = """
            SELECT 1
            FROM agendamentos a
            WHERE a.data = %s
              AND a.status <> 'Cancelado'
              AND a.motorista_id = %s
              AND NOT (a.fim_min <= %s OR a.inicio_min >= %s)
        """
        if excluir_agendamento_id is not None:
            sql += " AND a.id <> %s"
            params.append(int(excluir_agendamento_id))
        sql += " LIMIT 1"
        cur.execute(sql, tuple(params))
        return cur.fetchone() is not None

    def _selecionar_carrinhos_disponiveis(
        self,
        cur,
        data_ref: date,
        inicio_min: int,
        fim_min: int,
        qtd: int,
        carrinho_preferido_id: Optional[int],
        excluir_agendamento_id: Optional[int],
    ) -> List[int]:
        selecionados: List[int] = []

        # Preferido primeiro (se houver)
        if carrinho_preferido_id is not None:
            self._validar_carrinho_ativo(cur, int(carrinho_preferido_id))
            if self._carrinho_ocupado(cur, data_ref, inicio_min, fim_min, int(carrinho_preferido_id), excluir_agendamento_id):
                raise ValueError("Carrinho preferido já está agendado nesse horário.")
            selecionados.append(int(carrinho_preferido_id))

        # Candidatos ativos
        cur.execute("SELECT id FROM carrinhos WHERE ativo=1 ORDER BY id ASC LIMIT 800")
        candidatos = [int(r["id"]) for r in (cur.fetchall() or [])]

        for cid in candidatos:
            if cid in selecionados:
                continue
            if self._carrinho_ocupado(cur, data_ref, inicio_min, fim_min, cid, excluir_agendamento_id):
                continue
            selecionados.append(cid)
            if len(selecionados) >= qtd:
                break

        if len(selecionados) < qtd:
            raise ValueError("Não há carrinhos suficientes disponíveis para esse horário.")

        return selecionados

    def salvar_agendamento(
        self,
        data: date,
        inicio: str,
        fim: str,
        inicio_min: int,
        fim_min: int,
        local: str,
        qtd_carrinhos: int = 1,
        carrinho_preferido_id: Optional[int] = None,
        motorista_id: Optional[int] = None,   # funcionarios.id
        status: str = "Agendado",
        obs: str = "",
        agendamento_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        st = self._normalizar_status(status)
        local = str(local or "").strip()
        if not local:
            raise ValueError("Local é obrigatório.")

        try:
            qtd_carrinhos = int(qtd_carrinhos or 1)
        except Exception:
            qtd_carrinhos = 1
        if qtd_carrinhos <= 0:
            raise ValueError("Quantidade de carrinhos inválida.")

        obs = str(obs or "").strip() or None

        conn = None
        cur = None
        try:
            conn = conectar()
            conn.start_transaction()
            cur = conn.cursor(dictionary=True)

            # Motorista opcional (funcionarios)
            if motorista_id is not None:
                self._validar_motorista_ativo(cur, int(motorista_id))
                if self._motorista_ocupado(cur, data, inicio_min, fim_min, int(motorista_id), agendamento_id):
                    raise ValueError("Conflito: motorista já está agendado nesse horário.")

            # Seleção automática de carrinhos (inclui preferido se houver)
            carrinhos_ids = self._selecionar_carrinhos_disponiveis(
                cur=cur,
                data_ref=data,
                inicio_min=inicio_min,
                fim_min=fim_min,
                qtd=qtd_carrinhos,
                carrinho_preferido_id=int(carrinho_preferido_id) if carrinho_preferido_id is not None else None,
                excluir_agendamento_id=agendamento_id,
            )

            carrinho_principal_id = (
                int(carrinho_preferido_id)
                if carrinho_preferido_id is not None
                else int(carrinhos_ids[0])
            )

            if agendamento_id is None:
                cur.execute(
                    """
                    INSERT INTO agendamentos
                    (data, inicio, fim, inicio_min, fim_min, carrinho_id, motorista_id, local, status, obs, qtd_carrinhos)
                    VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        data, inicio, fim, inicio_min, fim_min,
                        carrinho_principal_id,
                        int(motorista_id) if motorista_id is not None else None,
                        local, st, obs, int(qtd_carrinhos),
                    ),
                )
                agendamento_id = int(cur.lastrowid)
            else:
                cur.execute(
                    """
                    UPDATE agendamentos
                    SET data=%s, inicio=%s, fim=%s, inicio_min=%s, fim_min=%s,
                        carrinho_id=%s, motorista_id=%s, local=%s, status=%s, obs=%s, qtd_carrinhos=%s
                    WHERE id=%s
                    """,
                    (
                        data, inicio, fim, inicio_min, fim_min,
                        carrinho_principal_id,
                        int(motorista_id) if motorista_id is not None else None,
                        local, st, obs, int(qtd_carrinhos),
                        int(agendamento_id),
                    ),
                )
                cur.execute("DELETE FROM agendamentos_carrinhos WHERE agendamento_id=%s", (int(agendamento_id),))

            for cid in carrinhos_ids:
                cur.execute(
                    "INSERT INTO agendamentos_carrinhos (agendamento_id, carrinho_id) VALUES (%s, %s)",
                    (int(agendamento_id), int(cid)),
                )

            conn.commit()
            return self.obter_agendamento(int(agendamento_id)) or {}

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
                    a.id, a.data, a.inicio, a.fim, a.inicio_min, a.fim_min,
                    a.carrinho_id,
                    c.nome AS carrinho_nome,
                    c.id_externo AS carrinho_id_externo,
                    a.motorista_id,
                    f.nome AS motorista_nome,
                    a.local, a.status, a.obs, a.cadastro,
                    a.qtd_carrinhos,
                    GROUP_CONCAT(c2.id_externo ORDER BY c2.id SEPARATOR ', ') AS carrinhos_texto
                FROM agendamentos a
                LEFT JOIN carrinhos c ON c.id = a.carrinho_id
                LEFT JOIN funcionarios f ON f.id = a.motorista_id
                LEFT JOIN agendamentos_carrinhos ac ON ac.agendamento_id = a.id
                LEFT JOIN carrinhos c2 ON c2.id = ac.carrinho_id
                WHERE a.id = %s
                GROUP BY a.id
                LIMIT 1
                """,
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
                    a.id, a.data, a.inicio, a.fim, a.inicio_min, a.fim_min,
                    a.carrinho_id,
                    c.nome AS carrinho_nome,
                    c.id_externo AS carrinho_id_externo,
                    a.motorista_id,
                    f.nome AS motorista_nome,
                    a.local, a.status, a.obs, a.cadastro,
                    a.qtd_carrinhos,
                    GROUP_CONCAT(c2.id_externo ORDER BY c2.id SEPARATOR ', ') AS carrinhos_texto
                FROM agendamentos a
                LEFT JOIN carrinhos c ON c.id = a.carrinho_id
                LEFT JOIN funcionarios f ON f.id = a.motorista_id
                LEFT JOIN agendamentos_carrinhos ac ON ac.agendamento_id = a.id
                LEFT JOIN carrinhos c2 ON c2.id = ac.carrinho_id
                {where_sql}
                GROUP BY a.id
                ORDER BY a.data ASC, a.inicio_min ASC
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
            cur.execute("DELETE FROM agendamentos WHERE id = %s", (int(agendamento_id),))
            conn.commit()
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()