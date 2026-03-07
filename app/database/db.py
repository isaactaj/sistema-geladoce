# -*- coding: utf-8 -*-
from __future__ import annotations

from app.database.connection import conectar as _conectar_oficial


def conectar():
    try:
        return _conectar_oficial()
    except Exception as e:
        print(f"[DB] Falha ao conectar no MySQL: {e}")
        return None