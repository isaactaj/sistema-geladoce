from __future__ import annotations

from pathlib import Path
from typing import List

import mysql.connector
from mysql.connector import Error

from app.database.config import DB_NAME, get_db_config

# ============================================================
# CONEXÃO COM MYSQL
# ============================================================

_DEFAULT_CHARSET = "utf8mb4"
_DEFAULT_COLLATION = "utf8mb4_unicode_ci"
_DEFAULT_TIMEOUT = 8  # segundos


def _connect(include_database: bool):
    """
    Conecta no MySQL com parâmetros mais seguros para app desktop.
    """
    cfg = get_db_config(include_database=include_database)

    cfg.setdefault("autocommit", False)
    cfg.setdefault("connection_timeout", _DEFAULT_TIMEOUT)
    cfg.setdefault("charset", _DEFAULT_CHARSET)
    cfg.setdefault("collation", _DEFAULT_COLLATION)
    cfg.setdefault("use_unicode", True)

    conn = mysql.connector.connect(**cfg)

    try:
        conn.autocommit = False
    except Exception:
        pass

    return conn


def conectar_sem_banco():
    """
    Abre conexão sem selecionar database.
    Útil para criação manual do banco.
    """
    try:
        return _connect(include_database=False)
    except Error as e:
        raise ConnectionError(
            f"Erro ao conectar ao MySQL sem banco selecionado: {e}"
        ) from e


def conectar():
    """
    Abre a conexão principal já apontando para o banco do sistema.
    """
    try:
        return _connect(include_database=True)
    except Error as e:
        raise ConnectionError(
            f"Erro ao conectar ao banco '{DB_NAME}': {e}"
        ) from e


def criar_banco_se_nao_existir():
    """
    Garante que o banco exista.
    Esta função é segura: cria o banco apenas se ele não existir.
    """
    conn = None
    cursor = None
    try:
        conn = conectar_sem_banco()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            CREATE DATABASE IF NOT EXISTS `{DB_NAME}`
            CHARACTER SET {_DEFAULT_CHARSET}
            COLLATE {_DEFAULT_COLLATION}
            """
        )
        conn.commit()
    except Error as e:
        raise RuntimeError(
            f"Erro ao criar o banco '{DB_NAME}': {e}"
        ) from e
    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            if conn is not None and conn.is_connected():
                conn.close()


# ============================================================
# SCHEMA SQL
# ============================================================

def _strip_comments(sql: str) -> str:
    """
    Remove comentários do SQL sem quebrar strings.
    Suporta:
      - -- comentário
      - # comentário
      - /* comentário em bloco */
    """
    out = []
    i = 0
    n = len(sql)

    in_squote = False
    in_dquote = False
    in_btick = False
    in_block_comment = False

    while i < n:
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ""

        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        if not in_squote and not in_dquote and not in_btick and ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue

        if not in_squote and not in_dquote and not in_btick:
            if ch == "-" and nxt == "-":
                while i < n and sql[i] not in ("\n", "\r"):
                    i += 1
                continue
            if ch == "#":
                while i < n and sql[i] not in ("\n", "\r"):
                    i += 1
                continue

        if ch == "'" and not in_dquote and not in_btick:
            if i > 0 and sql[i - 1] == "\\":
                out.append(ch)
                i += 1
                continue
            in_squote = not in_squote
            out.append(ch)
            i += 1
            continue

        if ch == '"' and not in_squote and not in_btick:
            if i > 0 and sql[i - 1] == "\\":
                out.append(ch)
                i += 1
                continue
            in_dquote = not in_dquote
            out.append(ch)
            i += 1
            continue

        if ch == "`" and not in_squote and not in_dquote:
            in_btick = not in_btick
            out.append(ch)
            i += 1
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def _split_statements(sql: str) -> List[str]:
    """
    Divide o SQL em statements por ';', ignorando ';' dentro de strings/crases.
    """
    if "delimiter" in sql.lower():
        raise RuntimeError(
            "Seu schema.sql contém 'DELIMITER'. "
            "O executor atual não suporta procedures/triggers com delimitador customizado."
        )

    stmts = []
    buff = []

    in_squote = False
    in_dquote = False
    in_btick = False

    i = 0
    n = len(sql)
    while i < n:
        ch = sql[i]

        if ch == "'" and not in_dquote and not in_btick:
            if i > 0 and sql[i - 1] == "\\":
                buff.append(ch)
                i += 1
                continue
            in_squote = not in_squote
            buff.append(ch)
            i += 1
            continue

        if ch == '"' and not in_squote and not in_btick:
            if i > 0 and sql[i - 1] == "\\":
                buff.append(ch)
                i += 1
                continue
            in_dquote = not in_dquote
            buff.append(ch)
            i += 1
            continue

        if ch == "`" and not in_squote and not in_dquote:
            in_btick = not in_btick
            buff.append(ch)
            i += 1
            continue

        if ch == ";" and not in_squote and not in_dquote and not in_btick:
            stmt = "".join(buff).strip()
            if stmt:
                stmts.append(stmt)
            buff = []
            i += 1
            continue

        buff.append(ch)
        i += 1

    tail = "".join(buff).strip()
    if tail:
        stmts.append(tail)

    return stmts


def _ler_comandos_sql(schema_path: Path) -> List[str]:
    conteudo = schema_path.read_text(encoding="utf-8")
    sem_comentarios = _strip_comments(conteudo)
    comandos = _split_statements(sem_comentarios)
    return comandos


def _eh_create_index(comando: str) -> bool:
    c = comando.strip().lower()
    return c.startswith("create index") or c.startswith("create unique index")


def _eh_alter_add_column(comando: str) -> bool:
    c = " ".join(comando.strip().lower().split())
    return c.startswith("alter table") and " add column " in c


def _eh_drop_fk(comando: str) -> bool:
    c = " ".join(comando.strip().lower().split())
    return c.startswith("alter table") and " drop foreign key " in c


def _eh_drop_index(comando: str) -> bool:
    c = " ".join(comando.strip().lower().split())
    return c.startswith("alter table") and (" drop index " in c or " drop key " in c)


def _eh_add_fk(comando: str) -> bool:
    c = " ".join(comando.strip().lower().split())
    return c.startswith("alter table") and " add constraint " in c and " foreign key " in c


def _executar_comando(cursor, comando: str):
    """
    Executa um comando SQL com tolerância idempotente.
    """
    try:
        cursor.execute(comando)
    except Error as e:
        errno = getattr(e, "errno", None)

        if errno == 1061 and _eh_create_index(comando):
            return

        if errno == 1060 and _eh_alter_add_column(comando):
            return

        if errno == 1091 and (_eh_drop_fk(comando) or _eh_drop_index(comando)):
            return

        if errno in (1826, 1831) and _eh_add_fk(comando):
            return

        raise RuntimeError(
            f"Erro ao executar SQL (errno={errno}): {e}\nSQL:\n{comando}"
        ) from e


def criar_tabelas_se_nao_existirem():
    """
    ATENÇÃO:
    Esta função executa o schema.sql completo.

    Se o schema.sql tiver DROP TABLE / DROP VIEW, a operação será destrutiva.
    Portanto, use esta função APENAS manualmente quando quiser recriar a base.
    Não chame isso no startup do sistema.
    """
    conn = None
    cursor = None

    schema_path = Path(__file__).resolve().with_name("schema.sql")
    if not schema_path.exists():
        raise FileNotFoundError(f"Arquivo schema.sql não encontrado em: {schema_path}")

    comandos = _ler_comandos_sql(schema_path)

    try:
        conn = conectar()
        cursor = conn.cursor()

        for comando in comandos:
            cmd = comando.strip()
            if not cmd:
                continue
            _executar_comando(cursor, cmd)

        conn.commit()

    except Exception:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        raise

    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            if conn is not None and conn.is_connected():
                conn.close()


def testar_conexao() -> bool:
    """
    Testa se o app consegue abrir conexão com o banco configurado.
    """
    conn = None
    cursor = None
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE(), 1")
        cursor.fetchone()
        return True
    except Exception:
        return False
    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            if conn is not None and conn.is_connected():
                conn.close()