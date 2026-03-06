# app/database/repositories/carrinhos_repository.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from mysql.connector import Error

from app.database.connection import conectar


class CarrinhosRepository:
    def _normalizar_status(self, status: Any) -> str:
        validos = {"Disponível", "Em rota", "Manutenção"}
        s = str(status or "").strip()
        return s if s in validos else "Disponível"

    def salvar_carrinho(
        self,
        nome: str,
        capacidade: int,
        status: str = "Disponível",
        id_externo: Optional[str] = None,
        carrinho_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        nome = str(nome or "").strip()
        if not nome:
            raise ValueError("Nome é obrigatório.")

        try:
            capacidade = int(capacidade or 0)
        except Exception:
            raise ValueError("Capacidade inválida.")
        if capacidade < 0:
            capacidade = 0

        status = self._normalizar_status(status)
        id_externo = (str(id_externo).strip() if id_externo is not None else None) or None

        conn = None
        cur = None
        try:
            conn = conectar()
            conn.start_transaction()
            cur = conn.cursor(dictionary=True)

            if carrinho_id is None:
                # ✅ Inserção com id_externo automático e sem duplicar "" (unique)
                if id_externo is None:
                    tmp = f"TMP-{uuid4().hex[:16].upper()}"
                    cur.execute(
                        """
                        INSERT INTO carrinhos (id_externo, nome, capacidade, status, ativo)
                        VALUES (%s, %s, %s, %s, 1)
                        """,
                        (tmp, nome, capacidade, status),
                    )
                    novo_id = int(cur.lastrowid)
                    novo_idext = f"CAR-{novo_id:04d}"
                    cur.execute(
                        "UPDATE carrinhos SET id_externo=%s WHERE id=%s",
                        (novo_idext, novo_id),
                    )
                    conn.commit()
                    return self.obter_carrinho(novo_id) or {}

                # Inserção com id_externo manual
                try:
                    cur.execute(
                        """
                        INSERT INTO carrinhos (id_externo, nome, capacidade, status, ativo)
                        VALUES (%s, %s, %s, %s, 1)
                        """,
                        (id_externo, nome, capacidade, status),
                    )
                except Error as e:
                    if getattr(e, "errno", None) == 1062:
                        raise ValueError("ID externo já existe. Use outro ou deixe vazio para gerar automático.") from e
                    raise

                novo_id = int(cur.lastrowid)
                conn.commit()
                return self.obter_carrinho(novo_id) or {}

            # ✅ Edição: se id_externo vier None, mantém o atual
            if id_externo is None:
                cur.execute(
                    """
                    UPDATE carrinhos
                    SET nome=%s, capacidade=%s, status=%s
                    WHERE id=%s
                    """,
                    (nome, capacidade, status, int(carrinho_id)),
                )
            else:
                try:
                    cur.execute(
                        """
                        UPDATE carrinhos
                        SET id_externo=%s, nome=%s, capacidade=%s, status=%s
                        WHERE id=%s
                        """,
                        (id_externo, nome, capacidade, status, int(carrinho_id)),
                    )
                except Error as e:
                    if getattr(e, "errno", None) == 1062:
                        raise ValueError("ID externo já existe. Use outro.") from e
                    raise

            conn.commit()
            return self.obter_carrinho(int(carrinho_id)) or {}

        except Exception:
            if conn is not None:
                conn.rollback()
            raise
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def obter_carrinho(self, carrinho_id: int) -> Optional[Dict[str, Any]]:
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                """
                SELECT id, id_externo, nome, capacidade, status, ativo, cadastro
                FROM carrinhos
                WHERE id=%s
                LIMIT 1
                """,
                (int(carrinho_id),),
            )
            return cur.fetchone()
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def listar_carrinhos(
        self,
        termo: str = "",
        status: Optional[str] = None,
        incluir_inativos: bool = False,
        limite: int = 1000,
    ) -> List[Dict[str, Any]]:
        termo = str(termo or "").strip()
        like = f"%{termo}%"

        where = []
        params: List[Any] = []

        if not incluir_inativos:
            where.append("ativo=1")

        if status and str(status).strip() and str(status).strip() != "Todos":
            where.append("status=%s")
            params.append(str(status).strip())

        if termo:
            where.append("(nome LIKE %s OR id_externo LIKE %s)")
            params.extend([like, like])

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                f"""
                SELECT id, id_externo, nome, capacidade, status, ativo, cadastro
                FROM carrinhos
                {where_sql}
                ORDER BY nome ASC
                LIMIT %s
                """,
                tuple(params + [int(limite)]),
            )
            return cur.fetchall() or []
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def excluir_carrinho(self, carrinho_id: int) -> None:
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("UPDATE carrinhos SET ativo=0 WHERE id=%s", (int(carrinho_id),))
            conn.commit()
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()