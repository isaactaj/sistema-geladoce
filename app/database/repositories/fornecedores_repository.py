# app/database/repositories/fornecedores_repository.py

from __future__ import annotations

from typing import Any, Dict, List, Optional
from mysql.connector import Error

from app.database.connection import conectar


class FornecedoresRepository:
    """
    Camada de persistência de fornecedores.

    Compatível com a UI atual e com o contrato esperado pelo SistemaService:
      - listar_fornecedores(...)
      - obter_fornecedor(...)
      - salvar_fornecedor(...)
      - excluir_fornecedor(...)

    Observação:
    - Como a tabela fornecedores não possui campo de status/ativo,
      a exclusão aqui é definitiva (DELETE).
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
    def listar_fornecedores(self, termo: str = "", limite: int = 500) -> List[Dict[str, Any]]:
        """
        Lista fornecedores, com busca por:
        - razão social
        - CNPJ
        - telefone
        - observações
        """
        termo = (termo or "").strip()

        sql = """
            SELECT
                id,
                razao,
                cnpj,
                telefone,
                observacoes,
                cadastro,
                atualizado_em
            FROM fornecedores
        """
        params: List[Any] = []
        where_parts: List[str] = []

        if termo:
            like = f"%{termo}%"
            digits = self._somente_digitos(termo)

            conds = [
                "razao LIKE %s",
                "observacoes LIKE %s",
                "telefone LIKE %s",
                "cnpj LIKE %s",
            ]
            params.extend([like, like, like, like])

            # busca adicional quando o usuário digita com máscara
            if digits and digits != termo:
                conds.extend(["cnpj LIKE %s", "telefone LIKE %s"])
                params.extend([f"%{digits}%", f"%{digits}%"])

            where_parts.append("(" + " OR ".join(conds) + ")")

        if where_parts:
            sql += " WHERE " + " AND ".join(where_parts)

        sql += " ORDER BY razao ASC LIMIT %s"
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

    def obter_fornecedor(self, fornecedor_id: int) -> Optional[Dict[str, Any]]:
        sql = """
            SELECT
                id,
                razao,
                cnpj,
                telefone,
                observacoes,
                cadastro,
                atualizado_em
            FROM fornecedores
            WHERE id = %s
            LIMIT 1
        """

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(sql, (int(fornecedor_id),))
            return cur.fetchone()
        finally:
            self._close(conn, cur)

    def existe_cnpj(self, cnpj: str, ignorar_id: Optional[int] = None) -> bool:
        """
        Verifica duplicidade de CNPJ.
        Útil antes de INSERT/UPDATE e reforça a regra do UNIQUE no banco.
        """
        cnpj_digits = self._somente_digitos(cnpj)
        if len(cnpj_digits) != 14:
            return False

        sql = "SELECT id FROM fornecedores WHERE cnpj = %s"
        params: List[Any] = [cnpj_digits]

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
    def salvar_fornecedor(
        self,
        razao: str,
        cnpj: str,
        telefone: str,
        observacoes: str = "",
        fornecedor_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Salva fornecedor.

        - Se fornecedor_id for None: INSERT
        - Se fornecedor_id vier: UPDATE

        Retorna o fornecedor salvo no formato dict.
        """
        razao = str(razao or "").strip()
        telefone = str(telefone or "").strip()
        observacoes = str(observacoes or "").strip()
        cnpj_digits = self._somente_digitos(cnpj)

        # Validações de domínio
        if not razao:
            raise ValueError("Razão Social é obrigatória.")

        if len(cnpj_digits) != 14:
            raise ValueError("CNPJ inválido: informe 14 dígitos.")

        if not telefone:
            raise ValueError("Telefone é obrigatório.")

        if self.existe_cnpj(cnpj_digits, ignorar_id=fornecedor_id):
            raise ValueError("Já existe um fornecedor com este CNPJ.")

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor()

            if fornecedor_id is None:
                sql = """
                    INSERT INTO fornecedores (
                        razao,
                        cnpj,
                        telefone,
                        observacoes
                    )
                    VALUES (%s, %s, %s, %s)
                """
                cur.execute(sql, (razao, cnpj_digits, telefone, observacoes))
                conn.commit()
                novo_id = int(cur.lastrowid)
                return self.obter_fornecedor(novo_id) or {}

            # UPDATE
            sql = """
                UPDATE fornecedores
                SET
                    razao = %s,
                    cnpj = %s,
                    telefone = %s,
                    observacoes = %s,
                    atualizado_em = NOW()
                WHERE id = %s
            """
            cur.execute(sql, (razao, cnpj_digits, telefone, observacoes, int(fornecedor_id)))
            conn.commit()
            return self.obter_fornecedor(int(fornecedor_id)) or {}

        except Error as e:
            raise RuntimeError(f"Erro ao salvar fornecedor no MySQL: {e}")
        finally:
            self._close(conn, cur)

    def excluir_fornecedor(self, fornecedor_id: int) -> None:
        """
        Exclui definitivamente o fornecedor.

        Como a tabela fornecedores não possui coluna 'ativo' ou 'status',
        a exclusão aqui é física (DELETE).
        """
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM fornecedores WHERE id = %s", (int(fornecedor_id),))
            conn.commit()
        except Error as e:
            raise RuntimeError(f"Erro ao excluir fornecedor: {e}")
        finally:
            self._close(conn, cur)