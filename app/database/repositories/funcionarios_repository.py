# app/database/repositories/funcionarios_repository.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from mysql.connector import Error

from app.database.connection import conectar


class FuncionariosRepository:
    """
    Persistência de funcionários.

    - Exclusão lógica (ativo=0) para não quebrar FKs (usuarios/agendamentos/fechamentos)
    - Schema atual possui atualizado_em (ON UPDATE), então não precisamos setar manualmente.
    """

    @staticmethod
    def _somente_digitos(valor: str) -> str:
        return "".join(ch for ch in str(valor or "") if ch.isdigit())

    @staticmethod
    def _normalizar_tipo_acesso(tipo_acesso: str) -> str:
        txt = str(tipo_acesso or "").strip().lower()
        if txt == "administrador":
            return "Administrador"
        return "Colaborador"

    @staticmethod
    def _close(conn, cur) -> None:
        try:
            if cur is not None:
                cur.close()
        finally:
            if conn is not None and getattr(conn, "is_connected", lambda: False)():
                conn.close()

    def listar_funcionarios(
        self,
        termo: str = "",
        cargo: Optional[str] = None,
        tipo_acesso: Optional[str] = None,
        incluir_inativos: bool = False,
        limite: int = 500,
    ) -> List[Dict[str, Any]]:
        termo = (termo or "").strip()
        cargo_filtro = (cargo or "").strip()
        tipo_filtro = (tipo_acesso or "").strip()

        sql = """
            SELECT
                id, nome, cpf, telefone, cargo, tipo_acesso, ativo,
                cadastro, atualizado_em
            FROM funcionarios
        """

        where_parts: List[str] = []
        params: List[Any] = []

        if not incluir_inativos:
            where_parts.append("ativo = 1")

        if cargo_filtro:
            where_parts.append("LOWER(cargo) LIKE %s")
            params.append(f"%{cargo_filtro.lower()}%")

        if tipo_filtro:
            tipo_norm = self._normalizar_tipo_acesso(tipo_filtro)
            where_parts.append("tipo_acesso = %s")
            params.append(tipo_norm)

        if termo:
            like = f"%{termo}%"
            digits = self._somente_digitos(termo)

            conds = [
                "nome LIKE %s",
                "telefone LIKE %s",
                "cargo LIKE %s",
                "tipo_acesso LIKE %s",
                "cpf LIKE %s",
            ]
            params.extend([like, like, like, like, like])

            if digits and digits != termo:
                conds.extend(["cpf LIKE %s", "telefone LIKE %s"])
                params.extend([f"%{digits}%", f"%{digits}%"])

            where_parts.append("(" + " OR ".join(conds) + ")")

        if where_parts:
            sql += " WHERE " + " AND ".join(where_parts)

        sql += " ORDER BY nome ASC LIMIT %s"
        params.append(int(limite))

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(sql, params)
            return cur.fetchall() or []
        finally:
            self._close(conn, cur)

    def listar_entregadores(self, termo: str = "", incluir_inativos: bool = False) -> List[Dict[str, Any]]:
        sql = """
            SELECT
                id, nome, cpf, telefone, cargo, tipo_acesso, ativo,
                cadastro, atualizado_em
            FROM funcionarios
        """

        where_parts: List[str] = []
        params: List[Any] = []

        if not incluir_inativos:
            where_parts.append("ativo = 1")

        where_parts.append(
            "("
            "LOWER(cargo) LIKE %s OR "
            "LOWER(cargo) LIKE %s OR "
            "LOWER(cargo) LIKE %s"
            ")"
        )
        params.extend(["%entreg%", "%motoboy%", "%moto%"])

        if termo:
            like = f"%{termo}%"
            digits = self._somente_digitos(termo)

            conds = [
                "nome LIKE %s",
                "telefone LIKE %s",
                "cargo LIKE %s",
                "tipo_acesso LIKE %s",
                "cpf LIKE %s",
            ]
            params.extend([like, like, like, like, like])

            if digits and digits != termo:
                conds.extend(["cpf LIKE %s", "telefone LIKE %s"])
                params.extend([f"%{digits}%", f"%{digits}%"])

            where_parts.append("(" + " OR ".join(conds) + ")")

        if where_parts:
            sql += " WHERE " + " AND ".join(where_parts)

        sql += " ORDER BY nome ASC"

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(sql, params)
            encontrados = cur.fetchall() or []
        finally:
            self._close(conn, cur)

        if encontrados:
            return encontrados

        return self.listar_funcionarios(termo=termo, incluir_inativos=incluir_inativos)

    def obter_funcionario(self, funcionario_id: int) -> Optional[Dict[str, Any]]:
        sql = """
            SELECT
                id, nome, cpf, telefone, cargo, tipo_acesso, ativo,
                cadastro, atualizado_em
            FROM funcionarios
            WHERE id = %s
            LIMIT 1
        """
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(sql, (int(funcionario_id),))
            return cur.fetchone()
        finally:
            self._close(conn, cur)

    def existe_cpf(self, cpf: str, ignorar_id: Optional[int] = None) -> bool:
        cpf_digits = self._somente_digitos(cpf)
        if len(cpf_digits) != 11:
            return False

        sql = "SELECT id FROM funcionarios WHERE cpf = %s"
        params: List[Any] = [cpf_digits]

        if ignorar_id is not None:
            sql += " AND id <> %s"
            params.append(int(ignorar_id))

        sql += " LIMIT 1"

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(sql, params)
            return cur.fetchone() is not None
        finally:
            self._close(conn, cur)

    def salvar_funcionario(
        self,
        nome: str,
        telefone: str = "",
        cargo: str = "",
        funcionario_id: Optional[int] = None,
        cpf: str = "",
        tipo_acesso: str = "Colaborador",
    ) -> Dict[str, Any]:
        nome = str(nome or "").strip()
        telefone = str(telefone or "").strip()
        cargo = str(cargo or "").strip()
        cpf_digits = self._somente_digitos(cpf)
        tipo_norm = self._normalizar_tipo_acesso(tipo_acesso)

        if not nome:
            raise ValueError("Nome é obrigatório.")
        if len(cpf_digits) != 11:
            raise ValueError("CPF deve ter 11 números.")
        if not telefone:
            raise ValueError("Telefone é obrigatório.")
        if self.existe_cpf(cpf_digits, ignorar_id=funcionario_id):
            raise ValueError("Já existe um funcionário com este CPF.")

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor()

            if funcionario_id is None:
                cur.execute(
                    """
                    INSERT INTO funcionarios (nome, cpf, telefone, cargo, tipo_acesso, ativo)
                    VALUES (%s, %s, %s, %s, %s, 1)
                    """,
                    (nome, cpf_digits, telefone, cargo, tipo_norm),
                )
                conn.commit()
                return self.obter_funcionario(int(cur.lastrowid)) or {}

            cur.execute(
                """
                UPDATE funcionarios
                SET nome=%s, cpf=%s, telefone=%s, cargo=%s, tipo_acesso=%s, ativo=1
                WHERE id=%s
                """,
                (nome, cpf_digits, telefone, cargo, tipo_norm, int(funcionario_id)),
            )
            conn.commit()
            return self.obter_funcionario(int(funcionario_id)) or {}

        except Error as e:
            raise RuntimeError(f"Erro ao salvar funcionário no MySQL: {e}")
        finally:
            self._close(conn, cur)

    def excluir_funcionario(self, funcionario_id: int) -> None:
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("UPDATE funcionarios SET ativo = 0 WHERE id = %s", (int(funcionario_id),))
            conn.commit()
        except Error as e:
            raise RuntimeError(f"Erro ao excluir/inativar funcionário: {e}")
        finally:
            self._close(conn, cur)