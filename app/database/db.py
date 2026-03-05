# -*- coding: utf-8 -*-
from __future__ import annotations

import os

try:
    import mysql.connector
    from mysql.connector import Error
except Exception as e:
    mysql = None
    Error = Exception


class _ConnWrapper:
    """
    Wrapper para permitir:
      - uso direto (conn.cursor(), conn.close(), etc)
      - uso com 'with' (context manager), se algum repo usar isso
    """
    def __init__(self, conn):
        self._conn = conn

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def __enter__(self):
        return self._conn

    def __exit__(self, exc_type, exc, tb):
        try:
            self._conn.close()
        except Exception:
            pass
        return False


def conectar():
    """
    Abre conexão com MySQL.

    Configuração via variáveis de ambiente:
      DB_HOST (default: localhost)
      DB_PORT (default: 3306)
      DB_USER (default: root)
      DB_PASSWORD (default: "")
      DB_NAME (default: geladoce)

    Retorna:
      - _ConnWrapper(conn) em caso de sucesso
      - None em caso de falha
    """
    if mysql is None:
        raise ModuleNotFoundError(
            "mysql-connector-python não está instalado. "
            "Instale com: pip install mysql-connector-python"
        )

    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "3306"))
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "geladoce")

    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            autocommit=False,
        )
        return _ConnWrapper(conn)
    except Error as e:
        print(f"[DB] Falha ao conectar no MySQL: {e}")
        return None