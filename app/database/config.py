# app/database/config.py

import os


# ============================================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ============================================================
# Aqui eu centralizo as configurações do MySQL para não
# espalhar host, usuário e senha em vários arquivos.
#
# Como estou usando WAMP localmente, o mais comum é:
# - host: 127.0.0.1
# - port: 3306
# - user: root
# - password: "" (vazio, dependendo da instalação)
#
# Se eu mudar a senha ou o nome do banco depois,
# basta ajustar aqui.
# ============================================================

DB_HOST = os.getenv("GELADOCE_DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("GELADOCE_DB_PORT", "3306"))
DB_USER = os.getenv("GELADOCE_DB_USER", "root")
DB_PASSWORD = os.getenv("GELADOCE_DB_PASSWORD", "")
DB_NAME = os.getenv("GELADOCE_DB_NAME", "geladoce")


def get_db_config(include_database=True):
    """
    Aqui eu monto o dicionário padrão de conexão.
    Se include_database=False, eu conecto sem selecionar um banco,
    o que é útil para criar o schema pela primeira vez.
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