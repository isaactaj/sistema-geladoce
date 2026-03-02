import customtkinter as ctk
from tkinter import ttk
from CTkMessagebox import CTkMessagebox
from app.config import theme

class PaginaProdutos(ctk.CTkFrame):
    def __init__(self, master, chave="produtos"):
        super().__init__(master, fg_color=theme.COR_FUNDO)
        self.grid_columnconfigure(0, weight=1)
        # Ajustamos para a tabela crescer na linha 3 agora
        self.grid_rowconfigure(3, weight=1)

        self.lista_produtos = []
        self.proximo_id = 1

        # --- 1. TÍTULO (Linha 0) ---
        ctk.CTkLabel(
            self, text="Catálogo de Produtos",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=30, pady=(30, 10), sticky="w")
        
        # --- 2. BARRA DE PESQUISA (Linha 1) ---
        self.frame_busca = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_busca.grid(row=1, column=0, padx=30, pady=(0, 10), sticky="ew")

        self.entry_busca = ctk.CTkEntry(self.frame_busca, placeholder_text="Buscar por nome...")
        self.entry_busca.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_buscar = ctk.CTkButton(
            self.frame_busca, text="Buscar", width=100,
            fg_color=theme.COR_BOTAO, hover_color=theme.COR_HOVER,
            command=self.acao_buscar
        )
        self.btn_buscar.pack(side="left")

        # --- 3. BOTÕES DE AÇÃO (Linha 2) ---
        self.frame_acoes = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_acoes.grid(row=2, column=0, padx=30, pady=(0, 20), sticky="w")

        btn_config = {
            "fg_color": theme.COR_BOTAO, "hover_color": theme.COR_HOVER,
            "font": ctk.CTkFont(family=theme.FONTE, size=13, weight="bold"), "height": 34
        }
        pad_botoes = (0, 10)

        self.btn_adicionar = ctk.CTkButton(self.frame_acoes, text="Novo Produto", command=self.acao_adicionar, **btn_config)
        self.btn_adicionar.pack(side="left", padx=pad_botoes)

        self.btn_editar = ctk.CTkButton(self.frame_acoes, text="Editar Produto", command=self.acao_editar, **btn_config)
        self.btn_editar.pack(side="left", padx=pad_botoes)

        self.btn_excluir = ctk.CTkButton(self.frame_acoes, text="Excluir Selecionado", command=self.acao_excluir, **btn_config)
        self.btn_excluir.pack(side="left", padx=pad_botoes)

        self.btn_info = ctk.CTkButton(self.frame_acoes, text="Resumo", command=self.acao_info, **btn_config)
        self.btn_info.pack(side="left", padx=pad_botoes)

        # --- 4. TABELA (Linha 3) ---
        self.frame_tabela = ctk.CTkFrame(self)
        self.frame_tabela.grid(row=3, column=0, padx=30, pady=(0, 30), sticky="nsew")
        self.frame_tabela.grid_columnconfigure(0, weight=1)
        self.frame_tabela.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="white", foreground="black", rowheight=30, fieldbackground="white", font=(theme.FONTE, 11))
        style.configure("Treeview.Heading", background="#C1ECFD", foreground="black", font=(theme.FONTE, 12, "bold"))
        style.map('Treeview', background=[('selected', '#14375e')])

        colunas = ("id", "nome", "categoria", "preco")
        self.tabela = ttk.Treeview(self.frame_tabela, columns=colunas, show="headings", style="Treeview")
        self.tabela.heading("id", text="ID")
        self.tabela.heading("nome", text="Nome do Produto")
        self.tabela.heading("categoria", text="Categoria")
        self.tabela.heading("preco", text="Preço Venda")
        self.tabela.column("id", width=50, anchor="center")
        self.tabela.column("nome", width=250, anchor="w")
        self.tabela.column("categoria", width=150, anchor="center")
        self.tabela.column("preco", width=100, anchor="center")

        self.tabela.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.frame_tabela, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.atualizar_tabela()

    # --- LÓGICA ---

    def atualizar_tabela(self, lista_para_exibir=None):
        # Se nenhuma lista específica for passada, usa a lista completa
        if lista_para_exibir is None:
            lista_para_exibir = self.lista_produtos

        for item in self.tabela.get_children():
            self.tabela.delete(item)
        
        for p in lista_para_exibir:
            self.tabela.insert("", "end", iid=p["id"], values=(p["id"], p["nome"], p["categoria"], p["preco"]))

    def acao_buscar(self):
        termo = self.entry_busca.get().lower().strip()
        if not termo:
            self.atualizar_tabela() # Mostra tudo
        else:
            # Filtra por nome
            filtrados = [p for p in self.lista_produtos if termo in p["nome"].lower()]
            self.atualizar_tabela(filtrados)

    def _abrir_janela_dados(self, produto=None):
        janela = ctk.CTkToplevel(self)
        janela.title("Produto")
        janela.geometry("400x420")
        janela.attributes("-topmost", True)
        
        ctk.CTkLabel(janela, text="Nome:").pack(pady=(20,5), padx=20, anchor="w")
        entry_nome = ctk.CTkEntry(janela)
        entry_nome.pack(fill="x", padx=20)
        
        ctk.CTkLabel(janela, text="Categoria:").pack(pady=(10,5), padx=20, anchor="w")
        combo_cat = ctk.CTkOptionMenu(janela, values=["Massa", "Picolé", "Outros"])
        combo_cat.pack(fill="x", padx=20)

        ctk.CTkLabel(janela, text="Preço (R$):").pack(pady=(10,5), padx=20, anchor="w")
        entry_preco = ctk.CTkEntry(janela, placeholder_text="Ex: 10,00")
        entry_preco.pack(fill="x", padx=20)

        if produto:
            entry_nome.insert(0, produto["nome"])
            combo_cat.set(produto["categoria"])
            entry_preco.insert(0, produto["preco"])

        def confirmar():
            nome = entry_nome.get()
            cat = combo_cat.get()
            preco = entry_preco.get()

            if not nome or not preco:
                CTkMessagebox(title="Erro", message="Preencha todos os campos!", icon="cancel")
                return

            if produto:
                produto["nome"] = nome
                produto["categoria"] = cat
                produto["preco"] = preco
                CTkMessagebox(title="Sucesso", message="Produto atualizado!", icon="check")
            else:
                novo = {"id": self.proximo_id, "nome": nome, "categoria": cat, "preco": preco}
                self.lista_produtos.append(novo)
                self._reorganizar_ids()
                CTkMessagebox(title="Sucesso", message="Produto criado!", icon="check")

            # Limpa a busca e atualiza
            self.entry_busca.delete(0, "end")
            self.atualizar_tabela()
            janela.destroy()

        ctk.CTkButton(janela, text="Salvar", command=confirmar).pack(pady=30)

    def _reorganizar_ids(self):
        for index, p in enumerate(self.lista_produtos):
            p["id"] = index + 1
        self.proximo_id = len(self.lista_produtos) + 1

    def acao_adicionar(self): self._abrir_janela_dados()

    def acao_editar(self):
        sel = self.tabela.selection()
        if not sel:
            CTkMessagebox(title="Aviso", message="Selecione um produto.", icon="warning")
            return
        id_item = int(sel[0])
        prod = next((p for p in self.lista_produtos if p["id"] == id_item), None)
        if prod: self._abrir_janela_dados(prod)

    def acao_excluir(self):
        sel = self.tabela.selection()
        if not sel: 
            CTkMessagebox(title="Aviso", message="Selecione um produto para excluir.", icon="warning")
            return
        
        msg = CTkMessagebox(title="Excluir", message="Deseja excluir este produto?", icon="question", option_1="Não", option_2="Sim")
        if msg.get() == "Sim":
            id_item = int(sel[0])
            self.lista_produtos = [p for p in self.lista_produtos if p["id"] != id_item]
            self._reorganizar_ids()
            self.entry_busca.delete(0, "end") # Limpa filtro para evitar confusão visual
            self.atualizar_tabela()

    def acao_info(self):
        total = len(self.lista_produtos)
        CTkMessagebox(title="Resumo", message=f"Você possui {total} produtos cadastrados.", icon="info")