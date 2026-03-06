from __future__ import annotations

from typing import Any, Dict, List, Optional
from mysql.connector import Error

from app.database.connection import conectar


class ClientesRepository:
    """
    Camada de persistência de clientes.

    Compatível com o contrato esperado pelo SistemaService:
      - salvar_cliente(...)
      - listar_clientes(...)
      - listar_revendedores(...)
      - obter_cliente(...)
      - excluir_cliente(...)

    Padrão de exclusão: lógica (status='Inativo').
    """

    # ======================================================
    # HELPERS
    # ======================================================
    @staticmethod
    def _somente_digitos(valor: str) -> str:
        return "".join(ch for ch in str(valor or "") if ch.isdigit())

    @staticmethod
    def _close(conn, cur) -> None:
        try:
            if cur is not None:
                cur.close()
        finally:
            if conn is not None and getattr(conn, "is_connected", lambda: False)():
                conn.close()

    # ======================================================
    # CONSULTAS
    # ======================================================
    def listar_clientes(
        self,
        termo: str = "",
        tipo_cliente: Optional[str] = None,
        incluir_inativos: bool = False,
        limite: int = 500,
    ) -> List[Dict[str, Any]]:
        termo = (termo or "").strip()
        tipo = (tipo_cliente or "").strip()

        where_parts: List[str] = []
        params: List[Any] = []

        if not incluir_inativos:
            where_parts.append("status = 'Ativo'")

        if tipo:
            tipo_norm = "Revendedor" if tipo.lower() == "revendedor" else "Varejo"
            where_parts.append("tipo_cliente = %s")
            params.append(tipo_norm)

        if termo:
            like = f"%{termo}%"
            digits = self._somente_digitos(termo)

            conds = [
                "nome LIKE %s",
                "email LIKE %s",
                "telefone LIKE %s",
                "cpf_cnpj LIKE %s",
            ]
            params.extend([like, like, like, like])

            if digits and digits != termo:
                conds.extend(["cpf_cnpj LIKE %s", "telefone LIKE %s"])
                params.extend([f"%{digits}%", f"%{digits}%"])

            where_parts.append("(" + " OR ".join(conds) + ")")

        sql = """
            SELECT
                id, nome, cpf_cnpj, telefone, email,
                tipo_cliente, status,
                pontos_atuais, total_acumulado,
                ultima_compra, cadastro, atualizado_em
            FROM clientes
        """

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

    def listar_revendedores(self, termo: str = "", incluir_inativos: bool = False) -> List[Dict[str, Any]]:
        return self.listar_clientes(
            termo=termo,
            tipo_cliente="Revendedor",
            incluir_inativos=incluir_inativos,
        )

    def obter_cliente(self, cliente_id: int) -> Optional[Dict[str, Any]]:
        sql = """
            SELECT
                id, nome, cpf_cnpj, telefone, email,
                tipo_cliente, status,
                pontos_atuais, total_acumulado,
                ultima_compra, cadastro, atualizado_em
            FROM clientes
            WHERE id = %s
            LIMIT 1
        """

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(sql, (int(cliente_id),))
            return cur.fetchone()
        finally:
            self._close(conn, cur)

    def existe_cpf_cnpj(self, cpf_cnpj: str, ignorar_id: Optional[int] = None) -> bool:
        doc = self._somente_digitos(cpf_cnpj)
        if not doc:
            return False

        sql = "SELECT id FROM clientes WHERE cpf_cnpj = %s"
        params: List[Any] = [doc]

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

    # ======================================================
    # ESCRITAS
    # ======================================================
    def salvar_cliente(
        self,
        nome: str,
        cpf_cnpj: str,
        telefone: str,
        email: str = "",
        tipo_cliente: str = "Varejo",
        cliente_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        nome = str(nome or "").strip()
        telefone = str(telefone or "").strip()
        email = str(email or "").strip() or None

        doc = self._somente_digitos(cpf_cnpj)
        tipo_norm = "Revendedor" if str(tipo_cliente).strip().lower() == "revendedor" else "Varejo"

        if not nome:
            raise ValueError("Nome é obrigatório.")

        if len(doc) not in (11, 14):
            raise ValueError("CPF/CNPJ inválido: informe 11 dígitos (CPF) ou 14 dígitos (CNPJ).")

        if not telefone:
            raise ValueError("Telefone é obrigatório.")

        if self.existe_cpf_cnpj(doc, ignorar_id=cliente_id):
            raise ValueError("Já existe um cliente com este CPF/CNPJ.")

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor()

            if cliente_id is None:
                sql = """
                    INSERT INTO clientes (
                        nome, cpf_cnpj, telefone, email,
                        tipo_cliente, status
                    )
                    VALUES (%s, %s, %s, %s, %s, 'Ativo')
                """
                cur.execute(sql, (nome, doc, telefone, email, tipo_norm))
                conn.commit()
                novo_id = int(cur.lastrowid)
                return self.obter_cliente(novo_id) or {}

            sql = """
                UPDATE clientes
                SET
                    nome = %s,
                    cpf_cnpj = %s,
                    telefone = %s,
                    email = %s,
                    tipo_cliente = %s,
                    status = 'Ativo'
                WHERE id = %s
            """
            cur.execute(sql, (nome, doc, telefone, email, tipo_norm, int(cliente_id)))
            conn.commit()
            return self.obter_cliente(int(cliente_id)) or {}

        except Error as e:
            raise RuntimeError(f"Erro ao salvar cliente no MySQL: {e}")
        finally:
            self._close(conn, cur)

    def excluir_cliente(self, cliente_id: int, definitivo: bool = False) -> None:
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor()

            if definitivo:
                cur.execute("DELETE FROM clientes WHERE id = %s", (int(cliente_id),))
            else:
                cur.execute("UPDATE clientes SET status = 'Inativo' WHERE id = %s", (int(cliente_id),))

            conn.commit()

        except Error as e:
            raise RuntimeError(f"Erro ao excluir/inativar cliente: {e}")
        finally:
            self._close(conn, cur)