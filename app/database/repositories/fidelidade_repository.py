from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from mysql.connector import Error
from app.database.connection import conectar


class FidelidadeRepository:
    """
    Persistência da fidelidade.

    - RN05
    - movimentações em mov_fidelidade
    - saldo em clientes (pontos_atuais / total_acumulado)

    Agora suporta (opcional): mov_fidelidade.usuario_id
    """

    @staticmethod
    def _close(conn, cur) -> None:
        try:
            if cur is not None:
                cur.close()
        finally:
            if conn is not None and getattr(conn, "is_connected", lambda: False)():
                conn.close()

    @staticmethod
    def _to_decimal(valor) -> Decimal:
        if isinstance(valor, Decimal):
            return valor
        txt = str(valor).strip().replace("R$", "").replace(" ", "")
        if not txt:
            return Decimal("0")
        if "," in txt and "." in txt:
            txt = txt.replace(".", "").replace(",", ".")
        else:
            txt = txt.replace(",", ".")
        try:
            return Decimal(txt)
        except Exception:
            return Decimal("0")

    @staticmethod
    def _normalizar_acao(acao: str) -> Optional[str]:
        mapa = {
            "ADICIONAR": "ADICIONAR",
            "REMOVER": "REMOVER",
            "RESGATAR": "RESGATAR",
            "BONUS": "BONUS",
            "BÔNUS": "BONUS",
            "ZERAR": "ZERAR",
        }
        return mapa.get(str(acao or "").strip().upper())

    def calcular_pontos_rn05(self, tipo_cliente, valor_total) -> int:
        valor = self._to_decimal(valor_total)
        tipo = str(tipo_cliente or "").strip().lower()

        if valor <= 0:
            return 0
        if tipo == "varejo":
            return int(valor // Decimal("5"))
        if tipo == "revendedor":
            return int(valor // Decimal("50")) * 2
        return 0

    def obter_saldo_cliente(self, cliente_id: int) -> Optional[Dict[str, Any]]:
        sql = """
            SELECT
                id, nome, telefone, tipo_cliente, status,
                pontos_atuais, total_acumulado, ultima_compra, cadastro
            FROM clientes
            WHERE id = %s
            LIMIT 1
        """
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(sql, (int(cliente_id),))
            return cur.fetchone()
        finally:
            self._close(conn, cur)

    def obter_extrato_fidelidade(self, cliente_id: int, limite: int = 200) -> List[Dict[str, Any]]:
        sql = """
            SELECT
                m.id,
                m.cliente_id,
                m.acao,
                m.pontos,
                m.motivo,
                m.venda_id,
                m.usuario_id,
                m.data
            FROM mov_fidelidade m
            WHERE m.cliente_id = %s
            ORDER BY m.data DESC, m.id DESC
            LIMIT %s
        """
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(sql, (int(cliente_id), int(limite)))
            return cur.fetchall() or []
        finally:
            self._close(conn, cur)

    def movimentar_fidelidade(
        self,
        cliente_id: int,
        acao: str,
        pontos: int,
        motivo: str = "",
        venda_id: Optional[int] = None,
        usuario_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        acao_real = self._normalizar_acao(acao)
        if not acao_real:
            raise ValueError("Ação de fidelidade inválida.")

        try:
            pontos_int = int(pontos)
        except Exception:
            pontos_int = 0

        conn = None
        cur = None
        try:
            conn = conectar()
            conn.start_transaction()
            cur = conn.cursor(dictionary=True)

            cur.execute(
                """
                SELECT id, nome, status, tipo_cliente, pontos_atuais, total_acumulado
                FROM clientes
                WHERE id = %s
                LIMIT 1
                FOR UPDATE
                """,
                (int(cliente_id),),
            )
            cliente = cur.fetchone()
            if not cliente:
                raise ValueError("Cliente não encontrado.")
            if cliente.get("status") != "Ativo":
                raise ValueError("Cliente inativo não pode receber movimentações.")

            saldo_atual = int(cliente.get("pontos_atuais", 0))
            total_acumulado = int(cliente.get("total_acumulado", 0))

            pontos_registro = pontos_int
            novo_saldo = saldo_atual
            novo_total_acumulado = total_acumulado

            if acao_real in ("ADICIONAR", "BONUS"):
                if pontos_int <= 0:
                    raise ValueError("Informe uma quantidade válida de pontos.")
                novo_saldo = saldo_atual + pontos_int
                novo_total_acumulado = total_acumulado + pontos_int

            elif acao_real == "REMOVER":
                if pontos_int <= 0:
                    raise ValueError("Informe uma quantidade válida de pontos.")
                novo_saldo = max(0, saldo_atual - pontos_int)

            elif acao_real == "RESGATAR":
                if pontos_int <= 0:
                    raise ValueError("Informe uma quantidade válida de pontos.")
                if pontos_int > saldo_atual:
                    raise ValueError("Pontos insuficientes para resgate.")
                novo_saldo = saldo_atual - pontos_int

            elif acao_real == "ZERAR":
                if pontos_int <= 0:
                    pontos_registro = saldo_atual
                novo_saldo = 0

            cur.execute(
                """
                UPDATE clientes
                SET pontos_atuais=%s, total_acumulado=%s
                WHERE id=%s
                """,
                (novo_saldo, novo_total_acumulado, int(cliente_id)),
            )

            cur.execute(
                """
                INSERT INTO mov_fidelidade (cliente_id, acao, pontos, motivo, venda_id, usuario_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    int(cliente_id),
                    acao_real,
                    int(pontos_registro),
                    (str(motivo).strip() or "Sem motivo"),
                    int(venda_id) if venda_id is not None else None,
                    int(usuario_id) if usuario_id is not None else None,
                ),
            )

            movimento_id = int(cur.lastrowid)
            conn.commit()

            return {
                "id": movimento_id,
                "cliente_id": int(cliente_id),
                "acao": acao_real,
                "pontos": int(pontos_registro),
                "motivo": (str(motivo).strip() or "Sem motivo"),
                "venda_id": int(venda_id) if venda_id is not None else None,
                "usuario_id": int(usuario_id) if usuario_id is not None else None,
                "saldo_anterior": saldo_atual,
                "saldo_atual": novo_saldo,
                "total_acumulado": novo_total_acumulado,
            }

        except Error as e:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise RuntimeError(f"Erro ao movimentar fidelidade no MySQL: {e}")
        finally:
            self._close(conn, cur)