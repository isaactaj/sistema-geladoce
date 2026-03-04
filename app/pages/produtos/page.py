import customtkinter as ctk
from tkinter import ttk
from decimal import Decimal
from CTkMessagebox import CTkMessagebox
from app.config import theme


class PaginaProdutos(ctk.CTkFrame):
    def __init__(self, master, sistema=None):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        self.sistema = sistema

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # --- 1. TÍTULO ---
        ctk.CTkLabel(
            self,
            text="Catálogo de Produtos",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=30, pady=(30, 10), sticky="w")

        # --- 2. BARRA DE PESQUISA ---
        self.frame_busca = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_busca.grid(row=1, column=0, padx=30, pady=(0, 10), sticky="ew")
        self.frame_busca.grid_columnconfigure(0, weight=1)

        self.entry_busca = ctk.CTkEntry(
            self.frame_busca,
            placeholder_text="Buscar por nome..."
        )
        self.entry_busca.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_busca.bind("<KeyRelease>", lambda e: self.acao_buscar())

        self.btn_buscar = ctk.CTkButton(
            self.frame_busca,
            text="Buscar",
            width=100,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            command=self.acao_buscar,
            text_color=theme.COR_TEXTO_ALT
        )
        self.btn_buscar.pack(side="left")

        # --- 3. BOTÕES DE AÇÃO ---
        self.frame_acoes = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_acoes.grid(row=2, column=0, padx=30, pady=(0, 20), sticky="w")

        btn_config = {
            "fg_color": theme.COR_BOTAO,
            "hover_color": theme.COR_HOVER,
            "font": ctk.CTkFont(family=theme.FONTE, size=13, weight="bold"),
            "height": 34,
            "text_color": theme.COR_TEXTO_ALT
        }
        pad_botoes = (0, 10)

        self.btn_adicionar = ctk.CTkButton(
            self.frame_acoes,
            text="Novo Produto",
            command=self.acao_adicionar,
            **btn_config
        )
        self.btn_adicionar.pack(side="left", padx=pad_botoes)

        self.btn_editar = ctk.CTkButton(
            self.frame_acoes,
            text="Editar Produto",
            command=self.acao_editar,
            **btn_config
        )
        self.btn_editar.pack(side="left", padx=pad_botoes)

        self.btn_excluir = ctk.CTkButton(
            self.frame_acoes,
            text="Excluir Selecionado",
            command=self.acao_excluir,
            **btn_config
        )
        self.btn_excluir.pack(side="left", padx=pad_botoes)

        self.btn_info = ctk.CTkButton(
            self.frame_acoes,
            text="Resumo",
            command=self.acao_info,
            **btn_config
        )
        self.btn_info.pack(side="left", padx=pad_botoes)

        # --- 4. TABELA ---
        self.frame_tabela = ctk.CTkFrame(self)
        self.frame_tabela.grid(row=3, column=0, padx=30, pady=(0, 30), sticky="nsew")
        self.frame_tabela.grid_columnconfigure(0, weight=1)
        self.frame_tabela.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Produtos.Treeview",
            background="white",
            foreground="black",
            rowheight=30,
            fieldbackground="white",
            font=(theme.FONTE, 11)
        )
        style.configure(
            "Produtos.Treeview.Heading",
            background="#C1ECFD",
            foreground="black",
            font=(theme.FONTE, 12, "bold")
        )
        style.map("Produtos.Treeview", background=[("selected", "#14375e")])

        colunas = ("id", "nome", "categoria", "preco")
        self.tabela = ttk.Treeview(
            self.frame_tabela,
            columns=colunas,
            show="headings",
            style="Produtos.Treeview"
        )
        self.tabela.heading("id", text="ID")
        self.tabela.heading("nome", text="Nome do Produto")
        self.tabela.heading("categoria", text="Categoria")
        self.tabela.heading("preco", text="Preço Venda")

        self.tabela.column("id", width=60, anchor="center")
        self.tabela.column("nome", width=280, anchor="w")
        self.tabela.column("categoria", width=150, anchor="center")
        self.tabela.column("preco", width=120, anchor="center")

        self.tabela.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(self.frame_tabela, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.atualizar_tabela()

    # =========================================================
    # HELPERS
    # =========================================================
    def _listar_produtos(self, termo=""):
        """
        Lê os produtos diretamente do serviço central.
        """
        try:
            return self.sistema.listar_catalogo(termo=termo, categoria="Todos")
        except TypeError:
            try:
                return self.sistema.listar_catalogo(termo)
            except TypeError:
                return self.sistema.listar_catalogo()

    def _obter_produto(self, produto_id):
        try:
            return self.sistema.obter_produto(produto_id)
        except Exception:
            return None

    def _fmt_preco(self, valor):
        try:
            if isinstance(valor, Decimal):
                valor = float(valor)
            elif isinstance(valor, str):
                txt = valor.strip().replace("R$", "").replace(" ", "")
                if "," in txt and "." in txt:
                    txt = txt.replace(".", "").replace(",", ".")
                else:
                    txt = txt.replace(",", ".")
                valor = float(txt)
            return theme.fmt_dinheiro(valor)
        except Exception:
            return str(valor)

    def _parse_preco(self, texto):
        txt = str(texto).strip().replace("R$", "").replace(" ", "")
        if not txt:
            raise ValueError("Preço é obrigatório.")

        if "," in txt and "." in txt:
            txt = txt.replace(".", "").replace(",", ".")
        else:
            txt = txt.replace(",", ".")

        valor = float(txt)
        if valor < 0:
            raise ValueError("Preço não pode ser negativo.")
        return valor

    # =========================================================
    # LÓGICA
    # =========================================================
    def atualizar_tabela(self, lista_para_exibir=None):
        if lista_para_exibir is None:
            lista_para_exibir = self._listar_produtos("")

        for item in self.tabela.get_children():
            self.tabela.delete(item)

        for p in lista_para_exibir:
            self.tabela.insert(
                "",
                "end",
                iid=str(p["id"]),
                values=(
                    p["id"],
                    p["nome"],
                    p["categoria"],
                    self._fmt_preco(p["preco"])
                )
            )

    def acao_buscar(self):
        termo = self.entry_busca.get().strip()
        produtos = self._listar_produtos(termo)
        self.atualizar_tabela(produtos)

    def _abrir_janela_dados(self, produto=None):
        janela = ctk.CTkToplevel(self)
        janela.title("Produto")
        janela.geometry("400x420")
        janela.attributes("-topmost", True)
        janela.grab_set()

        ctk.CTkLabel(janela, text="Nome:").pack(pady=(20, 5), padx=20, anchor="w")
        entry_nome = ctk.CTkEntry(janela)
        entry_nome.pack(fill="x", padx=20)

        ctk.CTkLabel(janela, text="Categoria:").pack(pady=(10, 5), padx=20, anchor="w")
        combo_cat = ctk.CTkOptionMenu(
            janela,
            values=["Sorvete", "Picolé", "Açaí", "Outros"]
        )
        combo_cat.pack(fill="x", padx=20)
        combo_cat.set("Sorvete")

        ctk.CTkLabel(janela, text="Preço (R$):").pack(pady=(10, 5), padx=20, anchor="w")
        entry_preco = ctk.CTkEntry(janela, placeholder_text="Ex: 10,00")
        entry_preco.pack(fill="x", padx=20)

        if produto:
            entry_nome.insert(0, produto["nome"])
            categoria = produto.get("categoria", "Outros")
            if categoria not in ["Sorvete", "Picolé", "Açaí", "Outros"]:
                categoria = "Outros"
            combo_cat.set(categoria)

            preco_txt = str(produto["preco"])
            try:
                preco_float = float(preco_txt)
                preco_txt = f"{preco_float:.2f}".replace(".", ",")
            except Exception:
                pass
            entry_preco.insert(0, preco_txt)

        def confirmar():
            nome = entry_nome.get().strip()
            cat = combo_cat.get().strip()
            preco_txt = entry_preco.get().strip()

            if not nome:
                CTkMessagebox(title="Erro", message="Informe o nome do produto.", icon="cancel")
                return

            if cat not in ["Sorvete", "Picolé", "Açaí", "Outros"]:
                CTkMessagebox(title="Erro", message="Categoria inválida.", icon="cancel")
                return

            try:
                self._parse_preco(preco_txt)
            except ValueError as e:
                CTkMessagebox(title="Erro", message=str(e), icon="cancel")
                return

            try:
                self.sistema.salvar_produto(
                    nome=nome,
                    categoria=cat,
                    preco=preco_txt,
                    produto_id=produto["id"] if produto else None
                )
            except Exception as e:
                CTkMessagebox(
                    title="Erro",
                    message=f"Não foi possível salvar o produto.\n\nDetalhes: {e}",
                    icon="cancel"
                )
                return

            self.entry_busca.delete(0, "end")
            self.atualizar_tabela()
            janela.destroy()

            CTkMessagebox(
                title="Sucesso",
                message="Produto atualizado!" if produto else "Produto criado!",
                icon="check"
            )

        ctk.CTkButton(janela, text="Salvar", command=confirmar).pack(pady=30)

    def acao_adicionar(self):
        self._abrir_janela_dados()

    def acao_editar(self):
        sel = self.tabela.selection()
        if not sel:
            CTkMessagebox(title="Aviso", message="Selecione um produto.", icon="warning")
            return

        values = self.tabela.item(sel[0], "values")
        if not values:
            CTkMessagebox(title="Aviso", message="Produto inválido.", icon="warning")
            return

        id_item = int(values[0])
        prod = self._obter_produto(id_item)

        if not prod:
            CTkMessagebox(title="Erro", message="Produto não encontrado.", icon="cancel")
            return

        self._abrir_janela_dados(prod)

    def acao_excluir(self):
        sel = self.tabela.selection()
        if not sel:
            CTkMessagebox(title="Aviso", message="Selecione um produto para excluir.", icon="warning")
            return

        values = self.tabela.item(sel[0], "values")
        if not values:
            CTkMessagebox(title="Aviso", message="Produto inválido.", icon="warning")
            return

        id_item = int(values[0])

        msg = CTkMessagebox(
            title="Excluir",
            message="Deseja excluir este produto?",
            icon="question",
            option_1="Não",
            option_2="Sim"
        )

        if msg.get() != "Sim":
            return

        try:
            self.sistema.excluir_produto(id_item)
        except Exception as e:
            CTkMessagebox(
                title="Erro",
                message=f"Não foi possível excluir o produto.\n\nDetalhes: {e}",
                icon="cancel"
            )
            return

        # Não reorganiza IDs.
        self.entry_busca.delete(0, "end")
        self.atualizar_tabela()

        CTkMessagebox(title="Sucesso", message="Produto excluído com sucesso!", icon="check")

    def acao_info(self):
        total = len(self._listar_produtos(""))
        CTkMessagebox(
            title="Resumo",
            message=f"Você possui {total} produto(s) cadastrado(s).",
            icon="info"
        )