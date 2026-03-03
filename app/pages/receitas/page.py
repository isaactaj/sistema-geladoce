import customtkinter as ctk
from tkinter import ttk
from CTkMessagebox import CTkMessagebox
from app.config import theme

class PaginaReceitas(ctk.CTkFrame):
    def __init__(self, master, chave="receitas"):
        super().__init__(master, fg_color=theme.COR_FUNDO)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) # Tabela na row 3

        self.lista_receitas = []
        self.proximo_id = 1

        # --- TÍTULO ---
        ctk.CTkLabel(
            self, text="Receitas & Fichas Técnicas",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=30, pady=(30, 10), sticky="w")
        
        # --- BARRA DE PESQUISA ---
        self.frame_busca = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_busca.grid(row=1, column=0, padx=30, pady=(0, 10), sticky="ew")

        self.entry_busca = ctk.CTkEntry(self.frame_busca, placeholder_text="Buscar receita...")
        self.entry_busca.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_buscar = ctk.CTkButton(
            self.frame_busca, text="Buscar", width=100,
            fg_color=theme.COR_BOTAO, hover_color=theme.COR_HOVER,
            command=self.acao_buscar, text_color=theme.COR_TEXTO_ALT
        )
        self.btn_buscar.pack(side="left")

        # --- BOTÕES ---
        self.frame_acoes = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_acoes.grid(row=2, column=0, padx=30, pady=(0, 20), sticky="w")

        btn_config = {
            "fg_color": theme.COR_BOTAO, "hover_color": theme.COR_HOVER,
            "font": ctk.CTkFont(family=theme.FONTE, size=13, weight="bold"), "height": 34, "text_color": theme.COR_TEXTO_ALT
        }
        pad_botoes = (0, 10)

        self.btn_adicionar = ctk.CTkButton(self.frame_acoes, text="Nova Receita", command=self.acao_adicionar, **btn_config)
        self.btn_adicionar.pack(side="left", padx=pad_botoes)

        self.btn_editar = ctk.CTkButton(self.frame_acoes, text="Editar", command=self.acao_editar, **btn_config)
        self.btn_editar.pack(side="left", padx=pad_botoes)

        self.btn_excluir = ctk.CTkButton(self.frame_acoes, text="Excluir", command=self.acao_excluir, **btn_config)
        self.btn_excluir.pack(side="left", padx=pad_botoes)

        self.btn_ver_desc = ctk.CTkButton(self.frame_acoes, text="Ver Descrição", command=self.acao_ver_descricao, **btn_config)
        self.btn_ver_desc.pack(side="left", padx=pad_botoes)

        self.btn_ver_preparo = ctk.CTkButton(self.frame_acoes, text="Ver Modo de Preparo", command=self.acao_ver_preparo, **btn_config)
        self.btn_ver_preparo.pack(side="left", padx=pad_botoes)

        # --- TABELA ---
        self.frame_tabela = ctk.CTkFrame(self)
        self.frame_tabela.grid(row=3, column=0, padx=30, pady=(0, 30), sticky="nsew")
        self.frame_tabela.grid_columnconfigure(0, weight=1)
        self.frame_tabela.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="white", foreground="black", rowheight=30, fieldbackground="white", font=(theme.FONTE, 11))
        style.configure("Treeview.Heading", background="#C1ECFD", foreground="black", font=(theme.FONTE, 12, "bold"))
        style.map('Treeview', background=[('selected', '#14375e')])

        colunas = ("id", "nome", "rendimento", "custo")
        self.tabela = ttk.Treeview(self.frame_tabela, columns=colunas, show="headings", style="Treeview")
        self.tabela.heading("id", text="ID")
        self.tabela.heading("nome", text="Nome da Receita")
        self.tabela.heading("rendimento", text="Rendimento")
        self.tabela.heading("custo", text="Custo Total")
        self.tabela.column("id", width=50, anchor="center")
        self.tabela.column("nome", width=300, anchor="w")
        self.tabela.column("rendimento", width=150, anchor="center")
        self.tabela.column("custo", width=100, anchor="center")

        self.tabela.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.frame_tabela, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.atualizar_tabela()

    # --- LÓGICA ---

    def atualizar_tabela(self, lista_para_exibir=None):
        if lista_para_exibir is None:
            lista_para_exibir = self.lista_receitas

        for item in self.tabela.get_children():
            self.tabela.delete(item)
        for r in lista_para_exibir:
            self.tabela.insert("", "end", iid=r["id"], values=(r["id"], r["nome"], r["rendimento"], r["custo"]))

    def acao_buscar(self):
        termo = self.entry_busca.get().lower().strip()
        if not termo:
            self.atualizar_tabela()
        else:
            filtrados = [r for r in self.lista_receitas if termo in r["nome"].lower()]
            self.atualizar_tabela(filtrados)

    def _reorganizar_ids(self):
        for index, receita in enumerate(self.lista_receitas):
            receita["id"] = index + 1
        self.proximo_id = len(self.lista_receitas) + 1

    def _abrir_janela_dados(self, receita=None):
        janela = ctk.CTkToplevel(self)
        janela.title("Ficha Técnica da Receita")
        janela.geometry("450x650") 
        janela.attributes("-topmost", True)
        
        scroll_frame = ctk.CTkScrollableFrame(janela, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(scroll_frame, text="Nome da Receita:").pack(pady=(10,5), padx=10, anchor="w")
        entry_nome = ctk.CTkEntry(scroll_frame)
        entry_nome.pack(fill="x", padx=10)
        
        ctk.CTkLabel(scroll_frame, text="Rendimento:").pack(pady=(10,5), padx=10, anchor="w")
        entry_rend = ctk.CTkEntry(scroll_frame)
        entry_rend.pack(fill="x", padx=10)

        ctk.CTkLabel(scroll_frame, text="Custo Estimado (R$):").pack(pady=(10,5), padx=10, anchor="w")
        entry_custo = ctk.CTkEntry(scroll_frame)
        entry_custo.pack(fill="x", padx=10)

        ctk.CTkLabel(scroll_frame, text="Descrição Geral:").pack(pady=(15,5), padx=10, anchor="w")
        textbox_desc = ctk.CTkTextbox(scroll_frame, height=80)
        textbox_desc.pack(fill="x", padx=10)

        ctk.CTkLabel(scroll_frame, text="Modo de Preparo:").pack(pady=(15,5), padx=10, anchor="w")
        textbox_preparo = ctk.CTkTextbox(scroll_frame, height=120)
        textbox_preparo.pack(fill="x", padx=10)

        if receita:
            entry_nome.insert(0, receita["nome"])
            entry_rend.insert(0, receita["rendimento"])
            entry_custo.insert(0, receita["custo"])
            textbox_desc.insert("1.0", receita.get("descricao", ""))
            textbox_preparo.insert("1.0", receita.get("preparo", ""))

        def confirmar():
            nome = entry_nome.get()
            rend = entry_rend.get()
            custo = entry_custo.get()
            desc = textbox_desc.get("1.0", "end-1c")
            preparo = textbox_preparo.get("1.0", "end-1c")

            if not nome:
                CTkMessagebox(title="Erro", message="O nome é obrigatório!", icon="cancel")
                return

            dados = {"nome": nome, "rendimento": rend, "custo": custo, "descricao": desc, "preparo": preparo}

            if receita:
                receita.update(dados)
                CTkMessagebox(title="Sucesso", message="Receita atualizada!", icon="check")
            else:
                dados["id"] = self.proximo_id
                self.lista_receitas.append(dados)
                self._reorganizar_ids()
                CTkMessagebox(title="Sucesso", message="Receita criada!", icon="check")

            self.entry_busca.delete(0, "end")
            self.atualizar_tabela()
            janela.destroy()

        ctk.CTkButton(scroll_frame, text="Salvar Receita", command=confirmar).pack(pady=30)

    def acao_adicionar(self): self._abrir_janela_dados()

    def acao_editar(self):
        sel = self.tabela.selection()
        if not sel:
            CTkMessagebox(title="Aviso", message="Selecione uma receita.", icon="warning")
            return
        id_item = int(sel[0])
        rec = next((r for r in self.lista_receitas if r["id"] == id_item), None)
        if rec: self._abrir_janela_dados(rec)

    def acao_excluir(self):
        sel = self.tabela.selection()
        if not sel: return
        if CTkMessagebox(title="Excluir", message="Remover receita?", icon="question", option_1="Não", option_2="Sim").get() == "Sim":
            id_item = int(sel[0])
            self.lista_receitas = [r for r in self.lista_receitas if r["id"] != id_item]
            self._reorganizar_ids()
            self.entry_busca.delete(0, "end")
            self.atualizar_tabela()

    def acao_ver_descricao(self):
        sel = self.tabela.selection()
        if not sel: return
        id_item = int(sel[0])
        rec = next((r for r in self.lista_receitas if r["id"] == id_item), None)
        if rec:
            CTkMessagebox(title=f"Descrição: {rec['nome']}", message=rec.get("descricao", "Vazio"), icon="info", width=400)

    def acao_ver_preparo(self):
        sel = self.tabela.selection()
        if not sel: return
        id_item = int(sel[0])
        rec = next((r for r in self.lista_receitas if r["id"] == id_item), None)
        if rec:
            CTkMessagebox(title=f"Preparo: {rec['nome']}", message=rec.get("preparo", "Vazio"), icon="info", width=500)