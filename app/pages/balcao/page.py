import customtkinter as ctk
from tkinter import ttk
from CTkMessagebox import CTkMessagebox
from app.config import theme


class PaginaVendasBalcao(ctk.CTkFrame):
    def __init__(self, master, sistema=None):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        self.sistema = sistema

        # Layout geral (catálogo + carrinho)
        self.grid_columnconfigure(0, weight=3)  # catálogo
        self.grid_columnconfigure(1, weight=2)  # carrinho

        self.grid_rowconfigure(0, weight=0)  # topo
        self.grid_rowconfigure(1, weight=0)  # subtítulo
        self.grid_rowconfigure(2, weight=0)  # filtros
        self.grid_rowconfigure(3, weight=1)  # catálogo cresce

        # Estado (catálogo + carrinho)
        self.busca_var = ctk.StringVar(value="")
        self.tipo_var = ctk.StringVar(value="Todos")
        self.carrinho = []  # lista de dicts: {id, nome, preco, qtd, categoria}

        # Estado (cliente opcional)
        self.vincular_cliente_var = ctk.BooleanVar(value=False)
        self.cliente_busca_var = ctk.StringVar(value="")
        self.cliente_selecionado = None
        self._clientes_filtrados = []

        # UI
        self._topo()
        self._filtros()
        self._catalogo()
        self._carrinho_ui()

        self._render_catalogo()
        self._toggle_cliente()  # deixa o bloco de cliente desabilitado por padrão

    # =========================================================
    # HELPERS
    # =========================================================
    def _listar_clientes(self, termo=""):
        try:
            return self.sistema.listar_clientes(termo=termo)
        except TypeError:
            try:
                return self.sistema.listar_clientes(termo)
            except TypeError:
                return self.sistema.listar_clientes()

    def _listar_produtos_catalogo(self, termo="", categoria="Todos"):
        try:
            return self.sistema.listar_catalogo(termo=termo, categoria=categoria)
        except TypeError:
            try:
                if categoria != "Todos":
                    return self.sistema.listar_catalogo(termo, categoria)
                return self.sistema.listar_catalogo(termo)
            except TypeError:
                return self.sistema.listar_catalogo()

    def _obter_produto_catalogo(self, produto_id):
        produtos = self._listar_produtos_catalogo("", "Todos")
        for p in produtos:
            if p["id"] == produto_id:
                return p
        return None

    def _qtd_no_carrinho(self, produto_id):
        item = next((c for c in self.carrinho if c["id"] == produto_id), None)
        return item["qtd"] if item else 0

    def _estoque_disponivel(self, produto):
        estoque_real = int(produto.get("estoque", 0))
        reservado = self._qtd_no_carrinho(produto["id"])
        return max(estoque_real - reservado, 0)

    def _extrair_subgrupo(self, produto):
        """
        Mantém a ideia visual de hierarquia (tipo -> subgrupo -> produto),
        mesmo com catálogo central sem campo 'sabor'.
        """
        nome = str(produto.get("nome", "")).strip()

        if "•" in nome:
            partes = [p.strip() for p in nome.split("•") if p.strip()]
            if len(partes) >= 2:
                return partes[-1]

        if "(" in nome and ")" in nome:
            ini = nome.rfind("(")
            fim = nome.rfind(")")
            if ini != -1 and fim != -1 and fim > ini:
                conteudo = nome[ini + 1:fim].strip()
                if conteudo:
                    return conteudo

        return "Itens"

    # ---------------- UI ----------------
    def _topo(self):
        ctk.CTkLabel(
            self,
            text="Vendas • Balcão",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, columnspan=2, padx=30, pady=(14, 6), sticky="w")

        ctk.CTkLabel(
            self,
            text="Selecione produtos, confira estoque e finalize a venda.",
            font=ctk.CTkFont(family=theme.FONTE, size=13),
            text_color=theme.COR_TEXTO_SEC
        ).grid(row=1, column=0, columnspan=2, padx=30, pady=(0, 12), sticky="w")

    def _filtros(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=2, column=0, padx=(30, 12), pady=(0, 10), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        self.entry_busca = ctk.CTkEntry(
            frame,
            textvariable=self.busca_var,
            placeholder_text="🔎 Buscar produto/sabor…",
            height=36
        )
        self.entry_busca.grid(row=0, column=0, sticky="ew")
        self.entry_busca.bind("<KeyRelease>", lambda e: self._render_catalogo())

        self.combo_tipo = ctk.CTkComboBox(
            frame,
            values=["Todos", "Sorvete", "Picolé", "Açaí", "Outros"],
            width=160,
            command=lambda _: self._render_catalogo()
        )
        self.combo_tipo.set("Todos")
        self.combo_tipo.grid(row=0, column=1, padx=(10, 0))

    def _catalogo(self):
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=3, column=0, padx=(30, 12), pady=(0, 20), sticky="nsew")
        box.grid_rowconfigure(0, weight=1)
        box.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=(theme.FONTE, 12), rowheight=30)
        style.configure("Treeview.Heading", font=(theme.FONTE, 12, "bold"))
        style.map("Treeview", background=[("selected", theme.COR_HOVER)])

        # Treeview com hierarquia (tipo -> subgrupo -> produto)
        self.tree = ttk.Treeview(
            box,
            columns=("preco", "estoque"),
            show="tree headings"
        )
        self.tree.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        self.tree.heading("#0", text="Produto")
        self.tree.heading("preco", text="Preço")
        self.tree.heading("estoque", text="Estoque")

        self.tree.column("#0", width=280, anchor="w")
        self.tree.column("preco", width=100, anchor="e")
        self.tree.column("estoque", width=80, anchor="center")

        scroll_y = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        scroll_y.grid(row=0, column=1, sticky="ns", padx=(0, 12), pady=12)
        self.tree.configure(yscrollcommand=scroll_y.set)

        # Duplo clique no produto para adicionar ao carrinho
        self.tree.bind("<Double-1>", lambda e: self._adicionar_selecionado())

        # destaque item sem estoque
        self.tree.tag_configure("sem_estoque", foreground="#888888")

    def _carrinho_ui(self):
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=2, column=1, rowspan=2, padx=(12, 30), pady=(0, 20), sticky="nsew")
        box.grid_columnconfigure(0, weight=1)

        # rows do carrinho
        box.grid_rowconfigure(0, weight=0)  # título
        box.grid_rowconfigure(1, weight=0)  # cliente
        box.grid_rowconfigure(2, weight=0)  # total
        box.grid_rowconfigure(3, weight=1)  # lista carrinho (cresce)
        box.grid_rowconfigure(4, weight=0)  # pagamento
        box.grid_rowconfigure(5, weight=0)  # finalizar

        ctk.CTkLabel(
            box,
            text="Carrinho",
            font=ctk.CTkFont(family=theme.FONTE, size=16, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        # ===== Cliente (opcional) =====
        self.cliente_box = ctk.CTkFrame(box, fg_color="#FFFFFF", corner_radius=14)
        self.cliente_box.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")
        self.cliente_box.grid_columnconfigure(0, weight=1)

        top_line = ctk.CTkFrame(self.cliente_box, fg_color="transparent")
        top_line.grid(row=0, column=0, padx=12, pady=(10, 6), sticky="ew")
        top_line.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top_line,
            text="Cliente (opcional)",
            font=ctk.CTkFont(family=theme.FONTE, size=13, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, sticky="w")

        self.switch_cliente = ctk.CTkSwitch(
            top_line,
            text="Vincular",
            variable=self.vincular_cliente_var,
            command=self._toggle_cliente
        )
        self.switch_cliente.grid(row=0, column=1, sticky="e")

        self.entry_cliente = ctk.CTkEntry(
            self.cliente_box,
            textvariable=self.cliente_busca_var,
            placeholder_text="Buscar cliente por nome/telefone/CPF…",
            height=34
        )
        self.entry_cliente.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        self.entry_cliente.bind("<KeyRelease>", lambda e: self._atualizar_lista_clientes())

        self.combo_cliente = ctk.CTkComboBox(
            self.cliente_box,
            values=["(nenhum)"],
            command=lambda _: self._selecionar_cliente()
        )
        self.combo_cliente.grid(row=2, column=0, padx=12, pady=(0, 8), sticky="ew")

        self.lbl_cliente_sel = ctk.CTkLabel(
            self.cliente_box,
            text="Nenhum cliente vinculado",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC
        )
        self.lbl_cliente_sel.grid(row=3, column=0, padx=12, pady=(0, 10), sticky="w")

        self.btn_remover_cliente = ctk.CTkButton(
            self.cliente_box,
            text="Remover cliente",
            height=32,
            fg_color="#FFFFFF",
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._remover_cliente
        )
        self.btn_remover_cliente.grid(row=4, column=0, padx=12, pady=(0, 12), sticky="ew")

        # ===== Total =====
        self.lbl_total = ctk.CTkLabel(
            box,
            text="Total: R$ 0,00",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO
        )
        self.lbl_total.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="w")

        # ===== Lista carrinho =====
        self.lista_carrinho = ctk.CTkScrollableFrame(box, fg_color="transparent", height=260)
        self.lista_carrinho.grid(row=3, column=0, padx=16, pady=(0, 12), sticky="nsew")

        # ===== Pagamento =====
        self.combo_pag = ctk.CTkComboBox(
            box, values=["Dinheiro", "Pix", "Cartão"], width=180
        )
        self.combo_pag.set("Pix")
        self.combo_pag.grid(row=4, column=0, padx=16, pady=(0, 10), sticky="w")

        # ===== Finalizar =====
        self.btn_finalizar = ctk.CTkButton(
            box,
            text="Finalizar venda",
            height=40,
            fg_color="#FFFFFF",
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._finalizar
        )
        self.btn_finalizar.grid(row=5, column=0, padx=16, pady=(0, 16), sticky="ew")

        self._render_carrinho()

    # ---------------- Cliente (opcional) ----------------
    def _toggle_cliente(self):
        ligado = self.vincular_cliente_var.get()
        estado = "normal" if ligado else "disabled"

        self.entry_cliente.configure(state=estado)
        self.combo_cliente.configure(state=estado)
        self.btn_remover_cliente.configure(state=estado)

        if not ligado:
            self._remover_cliente()
        else:
            self._atualizar_lista_clientes()

    def _atualizar_lista_clientes(self):
        termo = self.cliente_busca_var.get().strip().lower()

        opcoes = []
        self._clientes_filtrados = []

        for c in self._listar_clientes(termo):
            texto = f'{c.get("nome", "")} {c.get("cpf_cnpj", "")} {c.get("telefone", "")}'.lower()
            if not termo or termo in texto:
                opcoes.append(f'{c.get("nome", "")} • {c.get("telefone", "")}')
                self._clientes_filtrados.append(c)

        if not opcoes:
            opcoes = ["(nenhum encontrado)"]
            self._clientes_filtrados = []

        self.combo_cliente.configure(values=opcoes)
        self.combo_cliente.set(opcoes[0])

        if self._clientes_filtrados:
            self._selecionar_cliente()
        else:
            self.cliente_selecionado = None
            self.lbl_cliente_sel.configure(text="Nenhum cliente vinculado")

    def _selecionar_cliente(self):
        if not self._clientes_filtrados:
            return

        escolhido = self.combo_cliente.get()
        idx = 0

        for i, c in enumerate(self._clientes_filtrados):
            nome = c.get("nome", "")
            if escolhido.startswith(nome):
                idx = i
                break

        self.cliente_selecionado = self._clientes_filtrados[idx]
        c = self.cliente_selecionado
        self.lbl_cliente_sel.configure(text=f'Vinculado: {c.get("nome", "")} ({c.get("telefone", "")})')

    def _remover_cliente(self):
        self.cliente_selecionado = None
        self.cliente_busca_var.set("")
        self.combo_cliente.configure(values=["(nenhum)"])
        self.combo_cliente.set("(nenhum)")
        self.lbl_cliente_sel.configure(text="Nenhum cliente vinculado")

    # ---------------- Catálogo ----------------
    def _render_catalogo(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        filtro = self.busca_var.get().strip()
        tipo = self.combo_tipo.get()

        produtos = self._listar_produtos_catalogo(filtro, tipo)

        # agrupa categoria -> subgrupo
        grupos = {}
        for p in produtos:
            categoria = p.get("categoria", "Outros")
            subgrupo = self._extrair_subgrupo(p)
            grupos.setdefault(categoria, {}).setdefault(subgrupo, []).append(p)

        for tipo_nome, subgrupos in grupos.items():
            tipo_node = self.tree.insert("", "end", text=tipo_nome, open=True)

            for subgrupo_nome, itens in subgrupos.items():
                sub_node = self.tree.insert(tipo_node, "end", text=subgrupo_nome, open=True)

                for p in itens:
                    preco = theme.fmt_dinheiro(float(p["preco"])) if not isinstance(p["preco"], str) else p["preco"]
                    estoque = self._estoque_disponivel(p)
                    tag = "sem_estoque" if estoque <= 0 else "ok"

                    self.tree.insert(
                        sub_node,
                        "end",
                        text=p["nome"],
                        values=(preco, estoque),
                        tags=(tag, str(p["id"]))
                    )

        # destaque item sem estoque
        self.tree.tag_configure("sem_estoque", foreground="#888888")

    def _adicionar_selecionado(self):
        sel = self.tree.selection()
        if not sel:
            return

        item_id = sel[0]

        # pega o id do produto nas tags
        tags = self.tree.item(item_id, "tags")
        pid = None
        for t in tags:
            if str(t).isdigit():
                pid = int(t)
                break

        if pid is None:
            return  # clicou em grupo/subgrupo

        produto = self._obter_produto_catalogo(pid)
        if not produto:
            self._render_catalogo()
            return

        estoque_disponivel = self._estoque_disponivel(produto)
        if estoque_disponivel <= 0:
            self._render_catalogo()
            return

        # adiciona/incrementa no carrinho (sem baixar estoque ainda)
        existente = next((c for c in self.carrinho if c["id"] == pid), None)
        if existente:
            existente["qtd"] += 1
        else:
            self.carrinho.append(
                {
                    "id": pid,
                    "nome": produto["nome"],
                    "preco": float(produto["preco"]),
                    "qtd": 1,
                    "categoria": produto.get("categoria", "Outros")
                }
            )

        self._render_catalogo()
        self._render_carrinho()

    # ---------------- Carrinho ----------------
    def _render_carrinho(self):
        for w in self.lista_carrinho.winfo_children():
            w.destroy()

        total = 0.0
        for item in self.carrinho:
            total += item["preco"] * item["qtd"]

            linha = ctk.CTkFrame(self.lista_carrinho, fg_color="#FFFFFF", corner_radius=10)
            linha.pack(fill="x", pady=6)

            ctk.CTkLabel(
                linha, text=item["nome"],
                font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
                text_color=theme.COR_TEXTO
            ).pack(anchor="w", padx=10, pady=(8, 0))

            ctk.CTkLabel(
                linha,
                text=f'{item["qtd"]} x {theme.fmt_dinheiro(item["preco"])}',
                font=ctk.CTkFont(family=theme.FONTE, size=12),
                text_color=theme.COR_TEXTO_SEC
            ).pack(anchor="w", padx=10, pady=(0, 8))

        self.lbl_total.configure(text=f"Total: {theme.fmt_dinheiro(total)}")

    def _finalizar(self):
        if not self.carrinho:
            return

        itens = [{"produto_id": item["id"], "qtd": item["qtd"]} for item in self.carrinho]
        cliente_id = self.cliente_selecionado["id"] if self.cliente_selecionado else None

        try:
            self.sistema.registrar_venda(
                tipo="BALCAO",
                cliente_id=cliente_id,
                itens=itens,
                forma_pagamento=self.combo_pag.get(),
            )
        except Exception as e:
            CTkMessagebox(
                title="Erro ao finalizar",
                message=f"Não foi possível concluir a venda.\n\nDetalhes: {e}",
                icon="cancel"
            )
            self._render_catalogo()
            return

        self.carrinho = []
        self._remover_cliente()
        self._render_catalogo()
        self._render_carrinho()

        CTkMessagebox(
            title="Sucesso",
            message="Venda registrada com sucesso!",
            icon="check"
        )