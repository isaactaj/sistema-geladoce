import customtkinter as ctk
from tkinter import ttk
from CTkMessagebox import CTkMessagebox
from app.config import theme

class PaginaEstoque(ctk.CTkFrame):
    def __init__(self, master, chave="estoque"):
        super().__init__(master, fg_color=theme.COR_FUNDO)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) # Tabela na Row 3

        self.lista_estoque = []
        self.proximo_id = 1

        # --- TÍTULO ---
        ctk.CTkLabel(
            self, text="Gerenciamento de Estoque",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=30, pady=(30, 10), sticky="w")
        
        # --- BARRA DE PESQUISA (Linha 1) ---
        self.frame_busca = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_busca.grid(row=1, column=0, padx=30, pady=(0, 10), sticky="ew")

        self.entry_busca = ctk.CTkEntry(self.frame_busca, placeholder_text="Buscar item no estoque...")
        self.entry_busca.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_buscar = ctk.CTkButton(
            self.frame_busca, text="Buscar", width=100,
            fg_color=theme.COR_BOTAO, hover_color=theme.COR_HOVER,
            command=self.acao_buscar, text_color=theme.COR_TEXTO_ALT
        )
        self.btn_buscar.pack(side="left")

        # --- BOTÕES DE AÇÃO (Linha 2) ---
        self.frame_acoes = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_acoes.grid(row=2, column=0, padx=30, pady=(0, 20), sticky="w")

        btn_config = {
            "fg_color": theme.COR_BOTAO, "hover_color": theme.COR_HOVER,
            "font": ctk.CTkFont(family=theme.FONTE, size=13, weight="bold"), "height": 34, "text_color": theme.COR_TEXTO_ALT
        }
        pad_botoes = (0, 10)

        self.btn_salvar = ctk.CTkButton(self.frame_acoes, text="Adicionar Item", command=self.acao_salvar, **btn_config)
        self.btn_salvar.pack(side="left", padx=pad_botoes)

        self.btn_editar = ctk.CTkButton(self.frame_acoes, text="Editar Item", command=self.acao_editar, **btn_config)
        self.btn_editar.pack(side="left", padx=pad_botoes)

        self.btn_excluir = ctk.CTkButton(self.frame_acoes, text="Excluir", command=self.acao_excluir, **btn_config)
        self.btn_excluir.pack(side="left", padx=pad_botoes)

        self.btn_alerta = ctk.CTkButton(self.frame_acoes, text="Verificar Alertas", command=self.acao_alerta, **btn_config)
        self.btn_alerta.pack(side="left", padx=pad_botoes)

        # --- TABELA (Linha 3) ---
        self.frame_tabela = ctk.CTkFrame(self)
        self.frame_tabela.grid(row=3, column=0, padx=30, pady=(0, 30), sticky="nsew")
        self.frame_tabela.grid_columnconfigure(0, weight=1)
        self.frame_tabela.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="white", foreground="black", rowheight=30, fieldbackground="white", font=(theme.FONTE, 11))
        style.configure("Treeview.Heading", background="#C1ECFD", foreground="black", font=(theme.FONTE, 12, "bold"))
        style.map('Treeview', background=[('selected', '#14375e')])

        colunas = ("id", "nome", "qtd", "status")
        self.tabela = ttk.Treeview(self.frame_tabela, columns=colunas, show="headings", style="Treeview")
        self.tabela.heading("id", text="ID")
        self.tabela.heading("nome", text="Nome do Item")
        self.tabela.heading("qtd", text="Quantidade")
        self.tabela.heading("status", text="Status")
        self.tabela.column("id", width=50, anchor="center")
        self.tabela.column("nome", width=300, anchor="w")
        self.tabela.column("qtd", width=100, anchor="center")
        self.tabela.column("status", width=150, anchor="center")

        self.tabela.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.frame_tabela, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.atualizar_tabela()

    # --- LÓGICA ---

    def atualizar_tabela(self, lista_para_exibir=None):
        if lista_para_exibir is None:
            lista_para_exibir = self.lista_estoque

        for item in self.tabela.get_children():
            self.tabela.delete(item)
        for p in lista_para_exibir:
            self.tabela.insert("", "end", iid=p["id"], values=(p["id"], p["nome"], p["qtd"], p["status"]))

    def acao_buscar(self):
        termo = self.entry_busca.get().lower().strip()
        if not termo:
            self.atualizar_tabela()
        else:
            filtrados = [item for item in self.lista_estoque if termo in item["nome"].lower()]
            self.atualizar_tabela(filtrados)

    def _reorganizar_ids(self):
        for index, item in enumerate(self.lista_estoque):
            item["id"] = index + 1
        self.proximo_id = len(self.lista_estoque) + 1

    def acao_salvar(self):
        janela = ctk.CTkToplevel(self)
        janela.title("Novo Item de Estoque")
        janela.geometry("400x420")
        janela.attributes("-topmost", True)

        ctk.CTkLabel(janela, text="Nome do Item:").pack(pady=(20, 5), padx=20, anchor="w")
        entry_nome = ctk.CTkEntry(janela)
        entry_nome.pack(fill="x", padx=20)

        ctk.CTkLabel(janela, text="Quantidade:").pack(pady=(10, 5), padx=20, anchor="w")
        entry_qtd = ctk.CTkEntry(janela)
        entry_qtd.pack(fill="x", padx=20)

        ctk.CTkLabel(janela, text="Status:").pack(pady=(10, 5), padx=20, anchor="w")
        combo_status = ctk.CTkOptionMenu(janela, values=["Cheio", "Normal", "Crítico"])
        combo_status.pack(fill="x", padx=20)

        def confirmar():
            nome = entry_nome.get()
            qtd_str = entry_qtd.get()
            status = combo_status.get()
            if not nome or not qtd_str:
                CTkMessagebox(title="Erro", message="Preencha os campos.", icon="cancel")
                return
            try:
                qtd = int(qtd_str)
            except ValueError:
                CTkMessagebox(title="Erro", message="Quantidade deve ser número.", icon="cancel")
                return

            self.lista_estoque.append({"id": self.proximo_id, "nome": nome, "qtd": qtd, "status": status})
            self._reorganizar_ids()
            self.entry_busca.delete(0, "end")
            self.atualizar_tabela()
            janela.destroy()
            CTkMessagebox(title="Sucesso", message="Item adicionado!", icon="check")

        ctk.CTkButton(janela, text="Salvar", command=confirmar).pack(pady=30)

    def acao_editar(self):
        sel = self.tabela.selection()
        if not sel:
            CTkMessagebox(title="Aviso", message="Selecione um item.", icon="warning")
            return
        id_item = int(sel[0])
        item_atual = next((i for i in self.lista_estoque if i["id"] == id_item), None)
        if not item_atual: return

        janela = ctk.CTkToplevel(self)
        janela.title("Editar Estoque")
        janela.geometry("400x420")
        janela.attributes("-topmost", True)

        ctk.CTkLabel(janela, text="Nome:").pack(pady=(20, 5), padx=20, anchor="w")
        entry_nome = ctk.CTkEntry(janela)
        entry_nome.insert(0, item_atual["nome"])
        entry_nome.pack(fill="x", padx=20)

        ctk.CTkLabel(janela, text="Qtd:").pack(pady=(10, 5), padx=20, anchor="w")
        entry_qtd = ctk.CTkEntry(janela)
        entry_qtd.insert(0, str(item_atual["qtd"]))
        entry_qtd.pack(fill="x", padx=20)

        ctk.CTkLabel(janela, text="Status:").pack(pady=(10, 5), padx=20, anchor="w")
        combo_status = ctk.CTkOptionMenu(janela, values=["Cheio", "Normal", "Crítico"])
        combo_status.set(item_atual["status"])
        combo_status.pack(fill="x", padx=20)

        def confirmar():
            nome = entry_nome.get()
            qtd_str = entry_qtd.get()
            status = combo_status.get()
            if not nome or not qtd_str: return
            try:
                qtd = int(qtd_str)
            except ValueError: return

            item_atual["nome"] = nome
            item_atual["qtd"] = qtd
            item_atual["status"] = status
            self.atualizar_tabela()
            janela.destroy()
            CTkMessagebox(title="Sucesso", message="Item atualizado!", icon="check")

        ctk.CTkButton(janela, text="Salvar Alterações", command=confirmar).pack(pady=30)

    def acao_excluir(self):
        sel = self.tabela.selection()
        if not sel: return
        if CTkMessagebox(title="Excluir", message="Remover item?", icon="question", option_1="Não", option_2="Sim").get() == "Sim":
            id_item = int(sel[0])
            self.lista_estoque = [i for i in self.lista_estoque if i["id"] != id_item]
            self._reorganizar_ids()
            self.entry_busca.delete(0, "end")
            self.atualizar_tabela()

    def acao_alerta(self):
        criticos = [i["nome"] for i in self.lista_estoque if i["status"] == "Crítico"]
        if criticos:
            lista = "\n- ".join(criticos)
            CTkMessagebox(title="Alerta", message=f"Itens CRÍTICOS:\n\n- {lista}", icon="cancel")
        else:
            CTkMessagebox(title="OK", message="Nenhum item crítico.", icon="check")