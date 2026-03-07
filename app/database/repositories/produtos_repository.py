from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from mysql.connector import Error
from app.database.connection import conectar


class ProdutosRepository:
    """
    Repositório de Produtos/Estoque no MySQL.

    Responsabilidades:
      - produtos de venda
      - insumos internos
      - estoque consolidado
      - catálogo de vendas
      - cadastro administrativo de produtos
    """

    CATEGORIAS_VALIDAS = {"Sorvete", "Picolé", "Açaí", "Outros"}
    TIPOS_ITEM_VALIDOS = {"Produto", "Insumo"}

    def _to_decimal(self, valor: Any) -> Decimal:
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

    def _normalizar_categoria(self, categoria: Any) -> str:
        cat = str(categoria or "").strip()
        mapa = {
            "massa": "Sorvete",
            "sorvete": "Sorvete",
            "picolé": "Picolé",
            "picole": "Picolé",
            "açaí": "Açaí",
            "acai": "Açaí",
            "outros": "Outros",
            "outro": "Outros",
        }
        cat_norm = mapa.get(cat.lower(), cat)
        if cat_norm not in self.CATEGORIAS_VALIDAS:
            return "Outros"
        return cat_norm

    def _normalizar_tipo_item(self, tipo_item: Any, eh_insumo: Any) -> Tuple[str, int]:
        if eh_insumo is True or eh_insumo == 1:
            return "Insumo", 1

        txt = str(tipo_item or "").strip()
        if not txt:
            return "Produto", 0

        if txt.lower() in ("insumo", "insumos", "matéria-prima", "materia-prima", "materia prima"):
            return "Insumo", 1

        if txt not in self.TIPOS_ITEM_VALIDOS:
            return "Produto", 0

        return txt, 1 if txt == "Insumo" else 0

    def _montar_where(self, filtros: List[str]) -> str:
        return "WHERE " + " AND ".join(filtros) if filtros else ""

    def _base_select_item(self) -> str:
        return """
            SELECT
                p.id,
                p.id AS produto_id,
                p.nome,
                p.categoria,
                p.preco,
                p.ativo,
                p.tipo_item,
                p.eh_insumo,
                p.fornecedor_id,
                COALESCE(e.quantidade, 0) AS estoque,
                COALESCE(e.quantidade, 0) AS qtd
            FROM produtos p
            LEFT JOIN estoque e ON e.produto_id = p.id
        """

    def _normalizar_row_item(self, row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not row:
            return None

        row["id"] = int(row.get("id") or row.get("produto_id") or 0)
        row["produto_id"] = int(row.get("produto_id") or row.get("id") or 0)
        row["ativo"] = int(row.get("ativo") or 0)
        row["eh_insumo"] = bool(row.get("eh_insumo") or 0)
        row["estoque"] = int(row.get("estoque") or row.get("qtd") or 0)
        row["qtd"] = int(row.get("qtd") or row.get("estoque") or 0)
        return row

    def obter_produto(self, produto_id: int) -> Optional[Dict[str, Any]]:
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                f"""
                {self._base_select_item()}
                WHERE p.id = %s
                """,
                (int(produto_id),),
            )
            row = cur.fetchone()
            return self._normalizar_row_item(row)
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def obter_item_estoque(self, produto_id: int) -> Optional[Dict[str, Any]]:
        return self.obter_produto(int(produto_id))

    def listar_catalogo(
        self,
        termo: str = "",
        categoria: str = "Todos",
        incluir_inativos: bool = False,
        incluir_insumos: bool = False,
    ) -> List[Dict[str, Any]]:
        termo = str(termo or "").strip()
        categoria = str(categoria or "Todos").strip()

        filtros = []
        params: List[Any] = []

        if not incluir_inativos:
            filtros.append("p.ativo = 1")

        if not incluir_insumos:
            filtros.append("p.tipo_item = 'Produto'")
            filtros.append("p.eh_insumo = 0")

        if categoria and categoria != "Todos":
            cat = self._normalizar_categoria(categoria)
            filtros.append("p.categoria = %s")
            params.append(cat)

        if termo:
            filtros.append("p.nome LIKE %s")
            params.append(f"%{termo}%")

        where_sql = self._montar_where(filtros)

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                f"""
                {self._base_select_item()}
                {where_sql}
                ORDER BY p.nome ASC
                """,
                tuple(params),
            )
            rows = cur.fetchall() or []
            return [self._normalizar_row_item(r) for r in rows]
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def listar_produtos_admin(
        self,
        termo: str = "",
        categoria: str = "Todos",
        incluir_inativos: bool = False,
    ) -> List[Dict[str, Any]]:
        termo = str(termo or "").strip()
        categoria = str(categoria or "Todos").strip()

        filtros = [
            "p.tipo_item = 'Produto'",
            "p.eh_insumo = 0",
        ]
        params: List[Any] = []

        if not incluir_inativos:
            filtros.append("p.ativo = 1")

        if categoria and categoria != "Todos":
            cat = self._normalizar_categoria(categoria)
            filtros.append("p.categoria = %s")
            params.append(cat)

        if termo:
            filtros.append("p.nome LIKE %s")
            params.append(f"%{termo}%")

        where_sql = self._montar_where(filtros)

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                f"""
                {self._base_select_item()}
                {where_sql}
                ORDER BY p.nome ASC
                """,
                tuple(params),
            )
            rows = cur.fetchall() or []
            return [self._normalizar_row_item(r) for r in rows]
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def salvar_produto(
        self,
        nome: str,
        categoria: str,
        preco: Any,
        produto_id: Optional[int] = None,
        estoque_inicial: Optional[int] = None,
        tipo_item: Optional[str] = None,
        eh_insumo: Optional[bool] = None,
        fornecedor_id: Optional[int] = None,
        ativo: Optional[bool] = True,
    ) -> Dict[str, Any]:
        nome = str(nome or "").strip()
        if not nome:
            raise ValueError("Nome do produto é obrigatório.")

        tipo_item_norm, eh_insumo_int = self._normalizar_tipo_item(tipo_item, eh_insumo)

        if tipo_item_norm == "Insumo":
            cat = "Outros"
            preco_dec = Decimal("0")
            if ativo is None:
                ativo_int = 0
            else:
                ativo_int = 1 if (ativo is True or ativo == 1) else 0
        else:
            cat = self._normalizar_categoria(categoria)
            preco_dec = self._to_decimal(preco)
            ativo_int = 1 if (ativo is True or ativo == 1) else 0

        forn_id = int(fornecedor_id) if fornecedor_id not in (None, "", "None") else None

        conn = None
        cur = None
        try:
            conn = conectar()
            conn.start_transaction()
            cur = conn.cursor(dictionary=True)

            if produto_id:
                # CORREÇÃO PRINCIPAL:
                # verifica existência antes, em vez de usar rowcount do UPDATE
                cur.execute("SELECT id FROM produtos WHERE id = %s", (int(produto_id),))
                existe = cur.fetchone()
                if not existe:
                    raise ValueError("Produto não encontrado para atualizar.")

                cur.execute(
                    """
                    UPDATE produtos
                    SET
                        nome=%s,
                        categoria=%s,
                        preco=%s,
                        ativo=%s,
                        tipo_item=%s,
                        eh_insumo=%s,
                        fornecedor_id=%s
                    WHERE id=%s
                    """,
                    (
                        nome,
                        cat,
                        preco_dec,
                        ativo_int,
                        tipo_item_norm,
                        int(eh_insumo_int),
                        forn_id,
                        int(produto_id),
                    ),
                )

                if estoque_inicial is not None:
                    qtd = int(estoque_inicial)
                    if qtd < 0:
                        raise ValueError("Estoque inicial não pode ser negativo.")
                    cur.execute(
                        """
                        INSERT INTO estoque (produto_id, quantidade)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE quantidade=VALUES(quantidade)
                        """,
                        (int(produto_id), qtd),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO estoque (produto_id, quantidade)
                        VALUES (%s, 0)
                        ON DUPLICATE KEY UPDATE produto_id=produto_id
                        """,
                        (int(produto_id),),
                    )

                conn.commit()
                return self.obter_produto(int(produto_id)) or {}

            cur.execute(
                """
                INSERT INTO produtos (nome, categoria, preco, ativo, tipo_item, eh_insumo, fornecedor_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    nome,
                    cat,
                    preco_dec,
                    ativo_int,
                    tipo_item_norm,
                    int(eh_insumo_int),
                    forn_id,
                ),
            )
            novo_id = int(cur.lastrowid)

            qtd_ini = int(estoque_inicial) if estoque_inicial is not None else 0
            if qtd_ini < 0:
                raise ValueError("Estoque inicial não pode ser negativo.")

            cur.execute(
                "INSERT INTO estoque (produto_id, quantidade) VALUES (%s, %s)",
                (novo_id, qtd_ini),
            )

            conn.commit()
            return self.obter_produto(novo_id) or {}

        except Error:
            if conn is not None:
                conn.rollback()
            raise
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

    def salvar_insumo(
        self,
        nome: str,
        quantidade_inicial: int = 0,
        fornecedor_id: Optional[int] = None,
        produto_id: Optional[int] = None,
        ativo: bool = False,
    ) -> Dict[str, Any]:
        return self.salvar_produto(
            nome=nome,
            categoria="Outros",
            preco=Decimal("0"),
            produto_id=produto_id,
            estoque_inicial=int(quantidade_inicial),
            tipo_item="Insumo",
            eh_insumo=True,
            fornecedor_id=fornecedor_id,
            ativo=ativo,
        )

    def excluir_produto(self, produto_id: int) -> None:
        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("UPDATE produtos SET ativo = 0 WHERE id = %s", (int(produto_id),))
            conn.commit()
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def definir_estoque(self, produto_id: int, quantidade: int) -> int:
        qtd = int(quantidade)
        if qtd < 0:
            raise ValueError("Quantidade inválida.")

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO estoque (produto_id, quantidade)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE quantidade=VALUES(quantidade)
                """,
                (int(produto_id), qtd),
            )
            conn.commit()
            return qtd
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()

    def ajustar_estoque(self, produto_id: int, delta: int) -> int:
        pid = int(produto_id)
        delta = int(delta)

        conn = None
        cur = None
        try:
            conn = conectar()
            conn.start_transaction()
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO estoque (produto_id, quantidade)
                VALUES (%s, 0)
                ON DUPLICATE KEY UPDATE produto_id=produto_id
                """,
                (pid,),
            )

            cur.execute("SELECT quantidade FROM estoque WHERE produto_id = %s FOR UPDATE", (pid,))
            row = cur.fetchone()
            atual = int(row[0]) if row else 0
            novo = atual + delta

            if novo < 0:
                raise ValueError("Estoque insuficiente.")

            cur.execute("UPDATE estoque SET quantidade = %s WHERE produto_id = %s", (novo, pid))
            conn.commit()
            return novo

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

    def listar_estoque(self, termo: str = "") -> List[Dict[str, Any]]:
        termo = str(termo or "").strip()
        filtros = []
        params: List[Any] = []

        if termo:
            filtros.append("p.nome LIKE %s")
            params.append(f"%{termo}%")

        where_sql = self._montar_where(filtros)

        conn = None
        cur = None
        try:
            conn = conectar()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                f"""
                {self._base_select_item()}
                {where_sql}
                ORDER BY p.nome ASC
                """,
                tuple(params),
            )

            rows = cur.fetchall() or []
            itens = []
            for r in rows:
                r = self._normalizar_row_item(r)
                qtd = int(r.get("qtd") or 0)

                if qtd <= 0:
                    status = "Crítico"
                elif qtd <= 10:
                    status = "Normal"
                else:
                    status = "Cheio"

                itens.append({
                    "id": r["id"],
                    "produto_id": r["produto_id"],
                    "nome": r.get("nome", ""),
                    "qtd": qtd,
                    "status": status,
                    "categoria": r.get("categoria", "Outros"),
                    "preco": r.get("preco", Decimal("0")),
                    "tipo_item": r.get("tipo_item", "Produto"),
                    "eh_insumo": bool(r.get("eh_insumo", False)),
                    "ativo": int(r.get("ativo", 0)),
                    "fornecedor_id": r.get("fornecedor_id"),
                })
            return itens
        finally:
            try:
                if cur is not None:
                    cur.close()
            finally:
                if conn is not None and conn.is_connected():
                    conn.close()