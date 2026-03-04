# app/database/connection.py

from pathlib import Path

import mysql.connector
from mysql.connector import Error

from app.database.config import DB_NAME, get_db_config


# ============================================================
# CONEXÃO COM MYSQL
# ============================================================

def conectar_sem_banco():
    """
    Abre conexão sem selecionar database.
    Útil para criar o banco pela primeira vez.
    """
    try:
        conn = mysql.connector.connect(**get_db_config(include_database=False))
        return conn
    except Error as e:
        raise ConnectionError(f"Erro ao conectar ao MySQL sem banco selecionado: {e}") from e


def conectar():
    """
    Abre a conexão principal já apontando para o banco do sistema.
    """
    try:
        conn = mysql.connector.connect(**get_db_config(include_database=True))
        return conn
    except Error as e:
        raise ConnectionError(f"Erro ao conectar ao banco '{DB_NAME}': {e}") from e


def criar_banco_se_nao_existir():
    """
    Garante que o banco exista antes de usar o sistema.
    """
    conn = None
    cursor = None

    try:
        conn = conectar_sem_banco()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            CREATE DATABASE IF NOT EXISTS `{DB_NAME}`
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_unicode_ci
            """
        )
        conn.commit()
    except Error as e:
        raise RuntimeError(f"Erro ao criar o banco '{DB_NAME}': {e}") from e
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


# ============================================================
# SCHEMA (TABELAS + ÍNDICES + MIGRAÇÕES)
# ============================================================

def _ler_comandos_sql(schema_path: Path):
    """
    Lê o schema.sql e separa os comandos por ';',
    ignorando comentários iniciados com '--'.

    Obs.: Serve bem para CREATE TABLE/INDEX/ALTER TABLE comuns.
    Se você tiver PROCEDURE/TRIGGER com ';' interno, aí precisa parser.
    """
    conteudo = schema_path.read_text(encoding="utf-8")

    linhas_validas = []
    for linha in conteudo.splitlines():
        linha_strip = linha.strip()
        if not linha_strip or linha_strip.startswith("--"):
            continue
        linhas_validas.append(linha)

    sql_limpo = "\n".join(linhas_validas)

    comandos = []
    for comando in sql_limpo.split(";"):
        cmd = comando.strip()
        if cmd:
            comandos.append(cmd)

    return comandos


def _eh_create_index(comando: str) -> bool:
    c = comando.strip().lower()
    return c.startswith("create index") or c.startswith("create unique index")


def _eh_alter_add_column(comando: str) -> bool:
    c = " ".join(comando.strip().lower().split())
    return c.startswith("alter table") and " add column " in c


def _executar_comando(cursor, comando: str):
    """
    Executa um comando SQL com tolerância idempotente:
      - ignora erro 1061 para CREATE INDEX (índice já existe)
      - ignora erro 1060 para ALTER TABLE ... ADD COLUMN (coluna já existe)
    """
    try:
        cursor.execute(comando)
    except Error as e:
        errno = getattr(e, "errno", None)

        # 1061 = Duplicate key name (índice já existe)
        if errno == 1061 and _eh_create_index(comando):
            return

        # 1060 = Duplicate column name (coluna já existe)
        if errno == 1060 and _eh_alter_add_column(comando):
            return

        raise RuntimeError(
            f"Erro ao executar SQL (errno={errno}): {e}\nSQL: {comando}"
        ) from e


def criar_tabelas_se_nao_existirem():
    """
    Executa o schema.sql para criar tabelas/índices e aplicar migrações.

    - CREATE TABLE IF NOT EXISTS é repetível
    - CREATE INDEX precisa tolerância (1061)
    - ALTER TABLE ADD COLUMN precisa tolerância (1060)
    """
    conn = None
    cursor = None

    try:
        schema_path = Path(__file__).resolve().with_name("schema.sql")
        if not schema_path.exists():
            raise FileNotFoundError(f"Arquivo schema.sql não encontrado em: {schema_path}")

        comandos = _ler_comandos_sql(schema_path)

        conn = conectar()
        cursor = conn.cursor()

        for comando in comandos:
            _executar_comando(cursor, comando)

        conn.commit()

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


# ============================================================
# TESTE DE CONEXÃO
# ============================================================

def testar_conexao():
    """
    Valida rapidamente se a conexão está funcionando.
    """
    conn = None
    cursor = None

    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return True
    except Error:
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()