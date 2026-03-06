# app/database/repositories/usuarios_repository.py
import base64
import hashlib
import hmac
import secrets
from typing import Optional, Dict

from mysql.connector import Error

from app.database.connection import conectar


class UsuariosRepository:
    """
    Repositório de usuários do sistema (login).

    Regras:
    - login pode ser "admin" (padrão) ou o CPF (para usuários criados pela tela).
    - cpf é a ligação com a tabela funcionarios (FK: usuarios.cpf -> funcionarios.cpf).
    - senha é armazenada com hash PBKDF2 (não salva senha em texto puro).
    """

    PBKDF2_ITERS = 180_000

    # ----------------------------
    # Hash de senha
    # ----------------------------
    def _hash_senha(self, senha: str) -> str:
        senha_bytes = senha.encode("utf-8")
        salt = secrets.token_bytes(16)
        dk = hashlib.pbkdf2_hmac("sha256", senha_bytes, salt, self.PBKDF2_ITERS)
        return "pbkdf2_sha256${}${}${}".format(
            self.PBKDF2_ITERS,
            base64.b64encode(salt).decode("utf-8"),
            base64.b64encode(dk).decode("utf-8"),
        )

    def _verificar_senha(self, senha: str, senha_hash: str) -> bool:
        try:
            algo, iters, salt_b64, dk_b64 = senha_hash.split("$", 3)
            if algo != "pbkdf2_sha256":
                return False

            iters = int(iters)
            salt = base64.b64decode(salt_b64.encode("utf-8"))
            dk_real = base64.b64decode(dk_b64.encode("utf-8"))

            dk_teste = hashlib.pbkdf2_hmac(
                "sha256", senha.encode("utf-8"), salt, iters
            )
            return hmac.compare_digest(dk_real, dk_teste)
        except Exception:
            return False

    def _somente_digitos(self, valor: str) -> str:
        return "".join(ch for ch in str(valor) if ch.isdigit())

    # ----------------------------
    # Admin padrão
    # ----------------------------
    def garantir_admin_padrao(self):
        """
        Garante que exista um usuário admin padrão.
        login: admin
        senha: admin
        cpf: 00000000000 (também cria/atualiza funcionário com esse cpf)
        """
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)

            cur.execute("SELECT id FROM usuarios WHERE login=%s LIMIT 1", ("admin",))
            existe = cur.fetchone()
            if existe:
                return

            cpf_admin = "00000000000"
            # garante funcionário para satisfazer FK
            cur.execute(
                """
                INSERT INTO funcionarios (nome, cpf, telefone, cargo, tipo_acesso, ativo)
                VALUES (%s, %s, %s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE
                    nome=VALUES(nome),
                    tipo_acesso=VALUES(tipo_acesso),
                    ativo=1
                """,
                ("Administrador", cpf_admin, "", "", "Administrador"),
            )

            senha_hash = self._hash_senha("admin")
            cur.execute(
                """
                INSERT INTO usuarios (nome, login, cpf, senha_hash, tipo_acesso)
                VALUES (%s, %s, %s, %s, %s)
                """,
                ("Administrador", "admin", cpf_admin, senha_hash, "Administrador"),
            )

            conn.commit()

        finally:
            if cur is not None:
                cur.close()
            if conn is not None and conn.is_connected():
                conn.close()

    # ----------------------------
    # Autenticação
    # ----------------------------
    def autenticar(self, login_ou_cpf: str, senha: str) -> Optional[Dict]:
        login_ou_cpf = str(login_ou_cpf).strip()
        senha = str(senha)

        if not login_ou_cpf or not senha:
            return None

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)

            cpf_digits = self._somente_digitos(login_ou_cpf)
            cur.execute(
                """
                SELECT id, nome, login, cpf, senha_hash, tipo_acesso
                FROM usuarios
                WHERE login = %s OR cpf = %s
                LIMIT 1
                """,
                (login_ou_cpf, cpf_digits),
            )
            row = cur.fetchone()
            if not row:
                return None

            if not self._verificar_senha(senha, row["senha_hash"]):
                return None

            return {
                "id": row["id"],
                "nome": row["nome"],
                "login": row["login"],
                "cpf": row["cpf"],
                "tipo_acesso": row["tipo_acesso"],
            }

        finally:
            if cur is not None:
                cur.close()
            if conn is not None and conn.is_connected():
                conn.close()

    # ----------------------------
    # Criar usuário (Sign in)
    # ----------------------------
    def criar_usuario(self, nome: str, cpf: str, senha: str, tipo_acesso: str) -> Dict:
        nome = str(nome).strip()
        cpf_digits = self._somente_digitos(cpf)
        senha = str(senha)

        tipo_acesso = "Administrador" if str(tipo_acesso).strip().lower() == "administrador" else "Colaborador"

        if not nome:
            raise ValueError("Nome é obrigatório.")
        if len(cpf_digits) != 11:
            raise ValueError("CPF inválido: informe 11 dígitos.")
        if len(senha) < 4:
            raise ValueError("Senha muito curta (mínimo 4 caracteres).")

        # padrão: login = CPF (pra você conseguir logar imediatamente)
        login = cpf_digits

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)

            # 1) garante/atualiza funcionário (para manter FK e ligar ao resto do sistema)
            cur.execute(
                """
                INSERT INTO funcionarios (nome, cpf, telefone, cargo, tipo_acesso, ativo)
                VALUES (%s, %s, %s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE
                    nome=VALUES(nome),
                    tipo_acesso=VALUES(tipo_acesso),
                    ativo=1
                """,
                (nome, cpf_digits, "", "", tipo_acesso),
            )

            # 2) cria usuário
            senha_hash = self._hash_senha(senha)
            cur.execute(
                """
                INSERT INTO usuarios (nome, login, cpf, senha_hash, tipo_acesso)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (nome, login, cpf_digits, senha_hash, tipo_acesso),
            )

            conn.commit()

            return {
                "id": cur.lastrowid,
                "nome": nome,
                "login": login,
                "cpf": cpf_digits,
                "tipo_acesso": tipo_acesso,
            }

        except Error as e:
            # erros comuns: duplicidade de login/cpf
            msg = str(e).lower()
            if "duplicate" in msg or "1062" in msg:
                raise ValueError("Já existe um usuário com este CPF/login.")
            raise

        finally:
            if cur is not None:
                cur.close()
            if conn is not None and conn.is_connected():
                conn.close()

    # ----------------------------
    # Alterar senha (admin)
    # ----------------------------
    def alterar_senha(self, login_ou_cpf: str, nova_senha: str) -> None:
        login_ou_cpf = str(login_ou_cpf).strip()
        cpf_digits = self._somente_digitos(login_ou_cpf)
        nova_senha = str(nova_senha)

        if not login_ou_cpf:
            raise ValueError("Informe o usuário/CPF.")
        if len(nova_senha) < 4:
            raise ValueError("Senha muito curta (mínimo 4 caracteres).")

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor()

            senha_hash = self._hash_senha(nova_senha)
            cur.execute(
                """
                UPDATE usuarios
                SET senha_hash=%s, atualizado_em=NOW()
                WHERE login=%s OR cpf=%s
                """,
                (senha_hash, login_ou_cpf, cpf_digits),
            )

            if cur.rowcount == 0:
                raise ValueError("Usuário/CPF não encontrado.")

            conn.commit()

        finally:
            if cur is not None:
                cur.close()
            if conn is not None and conn.is_connected():
                conn.close()