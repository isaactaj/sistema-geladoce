# app/database/repositories/funcionarios_repository.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from mysql.connector import Error

from app.database.connection import conectar


class FuncionariosRepository:
    """
    Tabela: funcionarios

    Usos no sistema:
    - Funcionários gerais (CRUD)
    - Entregadores: filtro por cargo contendo entreg/moto/motoboy
    - Motoristas: filtro por cargo contendo motorist
      (motoristas "externos" também ficam aqui)
    """

    def _norm_tipo_acesso(self, tipo: Any) -> str:
        t = str(tipo or "").strip()
        return t if t in {"Colaborador", "Administrador"} else "Colaborador"

    def _digits(self, s: Any) -> str:
        return "".join(ch for ch in str(s or "") if ch.isdigit())

    def salvar_funcionario(
        self,
        nome: str,
        telefone: str = "",
        cargo: str = "",
        funcionario_id: Optional[int] = None,
        cpf: str = "",
        tipo_acesso: str = "Colaborador",
        ativo: bool = True,
    ) -> Dict[str, Any]:
        nome = str(nome or "").strip()
        if not nome:
            raise ValueError("Nome é obrigatório.")

        cpf_digits = self._digits(cpf)
        if len(cpf_digits) != 11:
            raise ValueError("CPF inválido (11 dígitos).")

        tel = str(telefone or "").strip()
        if not tel:
            raise ValueError("Telefone é obrigatório.")

        cargo_txt = str(cargo or "").strip()
        tipo = self._norm_tipo_acesso(tipo_acesso)
        ativo_int = 1 if (ativo is True or ativo == 1) else 0

        conn = None
        cur = None
        try:
            conn = conectar()
            conn.start_transaction()
            cur = conn.cursor(dictionary=True)

            if funcionario_id is None:
                cur.execute(
                    """
                    INSERT INTO funcionarios
                    (nome, cpf, telefone, cargo, tipo_acesso, ativo)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (nome, cpf_digits, tel, cargo_txt, tipo, ativo_int),
                )
                new_id = int(cur.lastrowid)
                conn.commit()
                return self.obter_funcionario(new_id) or {}

            cur.execute(
                """
                UPDATE funcionarios
                SET nome=%s, cpf=%s, telefone=%s, cargo=%s, tipo_acesso=%s, ativo=%s
                WHERE id=%s
                """,
                (nome, cpf_digits, tel, cargo_txt, tipo, ativo_int, int(funcionario_id)),
            )
            if cur.rowcount == 0:
                raise ValueError("Funcionário não encontrado para atualizar.")
            conn.commit()
            return self.obter_funcionario(int(funcionario_id)) or {}

        except Error:
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

    def obter_funcionario(self, funcionario_id: int) -> Optional[Dict[str, Any]]:
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                """
                SELECT id, nome, cpf, telefone, cargo, tipo_acesso, ativo, cadastro, atualizado_em
                FROM funcionarios
                WHERE id=%s
                LIMIT 1
                """,
                (int(funcionario_id),),
            )
            row = cur.fetchone()
            if not row:
                return None
            row["ativo"] = int(row.get("ativo") or 0)
            return row
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def listar_funcionarios(self, termo: str = "", cargo: Optional[str] = None, tipo_acesso: Optional[str] = None) -> List[Dict[str, Any]]:
        termo = str(termo or "").strip()
        cargo = str(cargo or "").strip()
        tipo_acesso = str(tipo_acesso or "").strip()

        where = ["ativo = 1"]
        params: List[Any] = []

        if termo:
            where.append("(nome LIKE %s OR cpf LIKE %s OR telefone LIKE %s)")
            params.extend([f"%{termo}%", f"%{termo}%", f"%{termo}%"])

        if cargo:
            where.append("cargo LIKE %s")
            params.append(f"%{cargo}%")

        if tipo_acesso:
            where.append("tipo_acesso = %s")
            params.append(tipo_acesso)

        where_sql = "WHERE " + " AND ".join(where)

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                f"""
                SELECT id, nome, cpf, telefone, cargo, tipo_acesso, ativo, cadastro, atualizado_em
                FROM funcionarios
                {where_sql}
                ORDER BY nome ASC, id ASC
                """,
                tuple(params),
            )
            rows = cur.fetchall() or []
            for r in rows:
                r["ativo"] = int(r.get("ativo") or 0)
            return rows
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def excluir_funcionario(self, funcionario_id: int) -> None:
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("UPDATE funcionarios SET ativo=0 WHERE id=%s", (int(funcionario_id),))
            conn.commit()
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    # -----------------------------
    # ENTREGADORES (filtro por cargo)
    # -----------------------------
    def listar_entregadores(self, termo: str = "") -> List[Dict[str, Any]]:
        termo = str(termo or "").strip()
        where = ["ativo = 1", "(LOWER(cargo) LIKE '%entreg%' OR LOWER(cargo) LIKE '%motoboy%' OR LOWER(cargo) LIKE '%moto%')"]
        params: List[Any] = []

        if termo:
            where.append("(nome LIKE %s OR cpf LIKE %s OR telefone LIKE %s)")
            params.extend([f"%{termo}%", f"%{termo}%", f"%{termo}%"])

        where_sql = "WHERE " + " AND ".join(where)

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                f"""
                SELECT id, nome, cpf, telefone, cargo, tipo_acesso, ativo, cadastro, atualizado_em
                FROM funcionarios
                {where_sql}
                ORDER BY nome ASC, id ASC
                """,
                tuple(params),
            )
            rows = cur.fetchall() or []
            for r in rows:
                r["ativo"] = int(r.get("ativo") or 0)
            return rows
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    # -----------------------------
    # MOTORISTAS (externos) -> funcionarios com cargo "Motorista"
    # -----------------------------
    def salvar_motorista(self, nome: str, cpf: str, telefone: str, motorista_id: Optional[int] = None) -> Dict[str, Any]:
        return self.salvar_funcionario(
            nome=nome,
            cpf=cpf,
            telefone=telefone,
            cargo="Motorista",
            tipo_acesso="Colaborador",
            funcionario_id=motorista_id,
            ativo=True,
        )

    def listar_motoristas(self, termo: str = "") -> List[Dict[str, Any]]:
        # Motorista pode aparecer como "Motorista", "motorista externo", etc.
        conn = None
        cur = None
        termo = str(termo or "").strip()
        where = ["ativo = 1", "LOWER(cargo) LIKE '%motorist%'"]
        params: List[Any] = []

        if termo:
            where.append("(nome LIKE %s OR cpf LIKE %s OR telefone LIKE %s)")
            params.extend([f"%{termo}%", f"%{termo}%", f"%{termo}%"])

        where_sql = "WHERE " + " AND ".join(where)

        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                f"""
                SELECT id, nome, cpf, telefone, cargo, tipo_acesso, ativo, cadastro, atualizado_em
                FROM funcionarios
                {where_sql}
                ORDER BY nome ASC, id ASC
                """,
                tuple(params),
            )
            rows = cur.fetchall() or []
            for r in rows:
                r["ativo"] = int(r.get("ativo") or 0)
            return rows
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def obter_motorista(self, motorista_id: int) -> Optional[Dict[str, Any]]:
        return self.obter_funcionario(int(motorista_id))

    def excluir_motorista(self, motorista_id: int) -> None:
        return self.excluir_funcionario(int(motorista_id))