from __future__ import annotations

from typing import Any, Dict, List, Optional
from app.database.connection import conectar


class FormasPagamentoRepository:
    """
    Tabela: formas_pagamento (codigo PK, descricao)
    """

    def listar_formas(self) -> List[Dict[str, Any]]:
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT codigo, descricao FROM formas_pagamento ORDER BY codigo ASC")
            return cur.fetchall() or []
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def existe(self, codigo: str) -> bool:
        codigo = str(codigo or "").strip()
        if not codigo:
            return False
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM formas_pagamento WHERE codigo = %s LIMIT 1", (codigo,))
            return cur.fetchone() is not None
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()