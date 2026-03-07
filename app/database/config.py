import os

# ============================================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ============================================================
# Banco real do sistema:
#   geladoce
#
# ============================================================


def _env_first(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return default


DB_HOST = _env_first("GELADOCE_DB_HOST", "DB_HOST", default="127.0.0.1")
DB_PORT = int(_env_first("GELADOCE_DB_PORT", "DB_PORT", default="3306"))
DB_USER = _env_first("GELADOCE_DB_USER", "DB_USER", default="root")
DB_PASSWORD = _env_first("GELADOCE_DB_PASSWORD", "DB_PASSWORD", default="")

# ✅ Banco real do sistema
DB_NAME = _env_first("GELADOCE_DB_NAME", "DB_NAME", default="geladoce")


def get_db_config(include_database: bool = True) -> dict:
    """
    Monta a configuração padrão de conexão com MySQL.
    Se include_database=False, conecta sem selecionar um banco.
    """
    config = {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "autocommit": False,
    }

    if include_database:
        config["database"] = DB_NAME

    return config