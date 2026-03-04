# app/database/repositories/funcionarios_repository.py

from __future__ import annotations

from typing import Any, Dict, List, Optional
from mysql.connector import Error

from app.database.connection import conectar


class FuncionariosRepository:
    """
    Camada de persistência de funcionários.

    Compatível com a UI atual e com o contrato esperado pelo SistemaService:
      - listar_funcionarios(...)
      - listar_entregadores(...)
      - obter_funcionario(...)
      - salvar_funcionario(...)
      - excluir_funcionario(...)

    Observações:
    - A exclusão aqui é lógica, usando o campo 'ativo' da tabela.
    - O schema atual não possui 'atualizado_em' em funcionarios, então
      este repository não depende dessa coluna.
    """

    # ======================================================
    # HELPERS
    # ======================================================
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

    # ======================================================
    # CONSULTAS
    # ======================================================
    def listar_funcionarios(
        self,
        termo: str = "",
        cargo: Optional[str] = None,
        tipo_acesso: Optional[str] = None,
        incluir_inativos: bool = False,
        limite: int = 500,
    ) -> List[Dict[str, Any]]:
        """
        Lista funcionários com filtros opcionais.

        Busca por:
        - nome
        - cpf
        - telefone
        - cargo
        - tipo_acesso
        """
        termo = (termo or "").strip()
        cargo_filtro = (cargo or "").strip()
        tipo_filtro = (tipo_acesso or "").strip()

        sql = """
            SELECT
                id,
                nome,
                cpf,
                telefone,
                cargo,
                tipo_acesso,
                ativo,
                cadastro
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

            # Busca adicional quando o usuário digita com máscara
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
        """
        Tenta retornar funcionários com cargo relacionado a entrega.
        Se não houver nenhum, retorna todos os funcionários para não quebrar a UI.
        """
        conn = None
        cur = None

        sql = """
            SELECT
                id,
                nome,
                cpf,
                telefone,
                cargo,
                tipo_acesso,
                ativo,
                cadastro
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

        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(sql, params)
            encontrados = cur.fetchall() or []
        finally:
            self._close(conn, cur)

        # Se não houver entregadores cadastrados, devolve todos para não quebrar a tela
        if encontrados:
            return encontrados

        return self.listar_funcionarios(termo=termo, incluir_inativos=incluir_inativos)

    def obter_funcionario(self, funcionario_id: int) -> Optional[Dict[str, Any]]:
        sql = """
            SELECT
                id,
                nome,
                cpf,
                telefone,
                cargo,
                tipo_acesso,
                ativo,
                cadastro
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
        """
        Verifica duplicidade de CPF.
        Reforça a regra do UNIQUE no banco.
        """
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

    # ======================================================
    # ESCRITAS
    # ======================================================
    def salvar_funcionario(
        self,
        nome: str,
        telefone: str = "",
        cargo: str = "",
        funcionario_id: Optional[int] = None,
        cpf: str = "",
        tipo_acesso: str = "Colaborador",
    ) -> Dict[str, Any]:
        """
        Salva funcionário.

        Compatível com versões antigas e novas:
        - antigo: salvar_funcionario(nome, telefone="", cargo="", funcionario_id=None)
        - novo:   salvar_funcionario(nome, telefone="", cargo="", funcionario_id=None, cpf="", tipo_acesso="...")

        Regras:
        - nome obrigatório
        - telefone obrigatório
        - CPF obrigatório e com 11 dígitos
        - tipo_acesso normalizado para Colaborador/Administrador
        """
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
                sql = """
                    INSERT INTO funcionarios (
                        nome,
                        cpf,
                        telefone,
                        cargo,
                        tipo_acesso,
                        ativo
                    )
                    VALUES (%s, %s, %s, %s, %s, 1)
                """
                cur.execute(sql, (nome, cpf_digits, telefone, cargo, tipo_norm))
                conn.commit()
                novo_id = int(cur.lastrowid)
                return self.obter_funcionario(novo_id) or {}

            sql = """
                UPDATE funcionarios
                SET
                    nome = %s,
                    cpf = %s,
                    telefone = %s,
                    cargo = %s,
                    tipo_acesso = %s,
                    ativo = 1
                WHERE id = %s
            """
            cur.execute(sql, (nome, cpf_digits, telefone, cargo, tipo_norm, int(funcionario_id)))
            conn.commit()
            return self.obter_funcionario(int(funcionario_id)) or {}

        except Error as e:
            raise RuntimeError(f"Erro ao salvar funcionário no MySQL: {e}")
        finally:
            self._close(conn, cur)

    def excluir_funcionario(self, funcionario_id: int) -> None:
        """
        Exclusão lógica: marca ativo = 0.
        Isso é mais seguro do que apagar definitivamente.
        """
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute(
                "UPDATE funcionarios SET ativo = 0 WHERE id = %s",
                (int(funcionario_id),)
            )
            conn.commit()
        except Error as e:
            raise RuntimeError(f"Erro ao excluir/inativar funcionário: {e}")
        finally:
            self._close(conn, cur)

    def deletar_definitivo(self, funcionario_id: int) -> None:
        """
        Remove de vez do banco.
        Use somente se você realmente quiser exclusão física.
        """
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM funcionarios WHERE id = %s", (int(funcionario_id),))
            conn.commit()
        except Error as e:
            raise RuntimeError(f"Erro ao deletar funcionário: {e}")
        finally:
            self._close(conn, cur)