import customtkinter as ctk
from tkinter import ttk
from CTkMessagebox import CTkMessagebox
from app.config import theme

class PaginaFornecedores(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        # ===== Layout da página =====
        self.grid_columnconfigure(0, weight=0)  # sem lista na página, só o formulário (coluna 1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # ===== "Banco" em memória =====
        self._proximo_id = 1
        self.fornecedores = []
        self.id_selecionado = None  # id em edição no formulário

        # Referência da janela de listagem
        self._win_lista = None
        self._tree_lista = None
        self._busca_var = None

        # ===== UI (apenas topo + formulário) =====
        self._criar_topo()
        self._criar_cadastro()

        # Exemplos
        self._popular_exemplo()

    # ==========================
    # UI
    # ==========================

    def _criar_topo(self):
        ctk.CTkLabel(
            self,
            text="Comercial • Fornecedores",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, columnspan=2, padx=30, pady=(14, 6), sticky="w")

        ctk.CTkLabel(
            self,
            text="Cadastre fornecedores. Use o botão 'Listar' para visualizar/editar itens existentes.",
            font=ctk.CTkFont(family=theme.FONTE, size=13),
            text_color=theme.COR_TEXTO_SEC,
        ).grid(row=1, column=0, columnspan=2, padx=30, pady=(0, 12), sticky="w")

    def _criar_cadastro(self):
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        # Só o formulário à direita
        box.grid(row=2, column=1, padx=(12, 30), pady=(0, 20), sticky="nsew")
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(99, weight=1)

        ctk.CTkLabel(
            box,
            text="Cadastro de Fornecedor",
            font=ctk.CTkFont(family=theme.FONTE, size=16, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, padx=16, pady=(12, 6), sticky="ew")

        self.lbl_status = ctk.CTkLabel(
            box, text="", font=ctk.CTkFont(family=theme.FONTE, size=12), text_color=theme.COR_TEXTO_SEC
        )
        self.lbl_status.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="w")

        # Vars
        self.razao_var = ctk.StringVar()
        self.cnpj_var = ctk.StringVar()
        self.telefone_var = ctk.StringVar()

        def label(texto, r):
            ctk.CTkLabel(
                box, text=texto, font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
                text_color=theme.COR_TEXTO_SEC
            ).grid(row=r, column=0, padx=16, pady=(10, 4), sticky="w")

        # Identificação
        label("Razão Social *", 2)
        ctk.CTkEntry(box, textvariable=self.razao_var, height=36).grid(row=3, column=0, padx=16, sticky="ew")

        label("CNPJ *", 6)
        ctk.CTkEntry(box, textvariable=self.cnpj_var, height=36).grid(row=7, column=0, padx=16, sticky="ew")

        # Contato
        label("Telefone *", 10)
        ctk.CTkEntry(box, textvariable=self.telefone_var, height=36).grid(row=11, column=0, padx=16, sticky="ew")

        # Observações
        label("Observações", 19)
        self.txt_obs = ctk.CTkTextbox(box, height=80)
        self.txt_obs.grid(row=20, column=0, padx=16, sticky="ew")

        # Botões CRUD
        botoes = ctk.CTkFrame(box, fg_color="transparent")
        botoes.grid(row=21, column=0, padx=16, pady=(16, 10), sticky="ew")
        botoes.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            botoes, text="Salvar", height=36,
            fg_color="#FFFFFF", hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
            command=self._salvar
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            botoes, text="Limpar", height=36,
            fg_color="#FFFFFF", hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
            command=self._limpar_form
        ).grid(row=0, column=1, padx=(8, 0), sticky="ew")

        # Botões Listagem (TopLevel) + Excluir do formulário
        botoes_lista = ctk.CTkFrame(box, fg_color="transparent")
        botoes_lista.grid(row=22, column=0, padx=16, pady=(0, 10), sticky="ew")
        botoes_lista.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            botoes_lista, text="Listar", height=36,
            fg_color="#FFFFFF", hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
            command=self._abrir_lista_toplevel
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            botoes_lista, text="Excluir (formulário)", height=36,
            fg_color="#FFFFFF", hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
            command=self._excluir
        ).grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def _label_inline(self, parent, text, col):
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO_SEC
        ).grid(row=0, column=col, pady=(10, 4), sticky="w")

    # ==========================
    # TopLevel: Lista de Fornecedores
    # ==========================

    def _abrir_lista_toplevel(self):
        """Abre (ou foca) uma janela modal com Busca + Treeview."""
        # Se já existe e está viva, só traz à frente
        if self._win_lista is not None and self._win_lista.winfo_exists():
            self._win_lista.deiconify()
            self._win_lista.lift()
            self._win_lista.focus_force()
            self._atualizar_tabela_tl()
            return

        win = ctk.CTkToplevel(self)
        win.title("Lista de Fornecedores")
        win.geometry("900x520")
        win.transient(self.winfo_toplevel())  # comporta como janela dependente
        try:
            win.attributes("-topmost", True)
            win.after(100, lambda: win.attributes("-topmost", False))  # só para vir à frente
        except Exception:
            pass

        self._win_lista = win
        win.grid_rowconfigure(1, weight=1)
        win.grid_columnconfigure(0, weight=1)

        # ==== Busca ====
        barra = ctk.CTkFrame(win, fg_color="transparent")
        barra.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="ew")
        barra.grid_columnconfigure(0, weight=1)

        self._busca_var = ctk.StringVar(value="")
        ent = ctk.CTkEntry(barra, textvariable=self._busca_var, height=36, placeholder_text="🔎 Buscar...")
        ent.grid(row=0, column=0, sticky="ew")
        ent.bind("<KeyRelease>", lambda e: self._atualizar_tabela_tl())

        # ==== Tabela ====
        box = ctk.CTkFrame(win, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="nsew")
        box.grid_rowconfigure(0, weight=1)
        box.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=(theme.FONTE, 14), rowheight=34, background="#FFFFFF", fieldbackground="#FFFFFF")
        style.configure("Treeview.Heading", font=(theme.FONTE, 14, "bold"))
        style.map("Treeview", background=[("selected", "#C1ECFD")], foreground=[("selected", "#000000")])

        colunas = ("id", "razao", "cnpj", "telefone")
        tree = ttk.Treeview(box, columns=colunas, show="headings", selectmode="browse")
        tree.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        tree.heading("id", text="ID")
        tree.heading("razao", text="Razão Social")
        tree.heading("cnpj", text="CNPJ")
        tree.heading("telefone", text="Telefone")

        tree.column("id", width=60, anchor="center")
        tree.column("razao", width=260, anchor="w")
        tree.column("cnpj", width=160, anchor="center")
        tree.column("telefone", width=140, anchor="center")

        scrolly = ttk.Scrollbar(box, orient="vertical", command=tree.yview)
        scrolly.grid(row=0, column=1, sticky="ns", padx=(0, 12), pady=12)
        scrollx = ttk.Scrollbar(box, orient="horizontal", command=tree.xview)
        scrollx.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        tree.configure(yscrollcommand=scrolly.set, xscrollcommand=scrollx.set)

        # Duplo clique -> edita no formulário e fecha
        tree.bind("<Double-1>", lambda e: self._editar_selecionado_da_lista())

        # ==== Botões ====
        botoes = ctk.CTkFrame(win, fg_color="transparent")
        botoes.grid(row=2, column=0, padx=16, pady=(0, 14), sticky="ew")
        botoes.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            botoes, text="Editar selecionado", height=36,
            fg_color="#FFFFFF", hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
            command=self._editar_selecionado_da_lista
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            botoes, text="Excluir selecionado", height=36,
            fg_color="#FFFFFF", hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
            command=self._excluir_selecionado_da_lista
        ).grid(row=0, column=1, padx=8, sticky="ew")

        ctk.CTkButton(
            botoes, text="Fechar", height=36,
            fg_color="#FFFFFF", hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
            command=win.destroy
        ).grid(row=0, column=2, padx=(8, 0), sticky="ew")

        # Guarda referências
        self._tree_lista = tree

        # Popular
        self._atualizar_tabela_tl()
        ent.focus_set()

        # Ao fechar, limpar referências
        def _on_close():
            if self._win_lista is not None and self._win_lista.winfo_exists():
                self._win_lista.destroy()
            self._win_lista = None
            self._tree_lista = None
            self._busca_var = None

        win.protocol("WM_DELETE_WINDOW", _on_close)

    def _atualizar_tabela_tl(self):
        if not (self._tree_lista and self._tree_lista.winfo_exists()):
            return
        filtro = (self._busca_var.get().strip().lower() if self._busca_var else "")

        for iid in self._tree_lista.get_children():
            self._tree_lista.delete(iid)

        for f in self.fornecedores:
            texto = " ".join([
                f.get("razao",""), f.get("cnpj",""),
                f.get("telefone",""), f.get("observacoes","")
            ]).lower()

            if (not filtro) or (filtro in texto):
                self._tree_lista.insert(
                    "", "end",
                    values=(f["id"], f["razao"], self._formatar_cnpj(f["cnpj"]), f["telefone"])
                )

    def _editar_selecionado_da_lista(self):
        """Carrega o item selecionado da lista no formulário e fecha a janela."""
        if not (self._tree_lista and self._tree_lista.winfo_exists()):
            return
        sel = self._tree_lista.selection()
        if not sel:
            CTkMessagebox(title="Atenção", message="Selecione um fornecedor na lista.", icon="warning")
            return
        values = self._tree_lista.item(sel[0], "values")
        if not values:
            return

        fid = int(values[0])
        self.id_selecionado = fid

        for f in self.fornecedores:
            if f["id"] == fid:
                # Preenche formulário
                self.razao_var.set(f.get("razao",""))
                self.cnpj_var.set(self._formatar_cnpj(f.get("cnpj","")))
                self.telefone_var.set(f.get("telefone",""))
                self.txt_obs.delete("1.0", "end")
                self.txt_obs.insert("1.0", f.get("observacoes",""))
                break

        self.lbl_status.configure(text=f"Editando ID {fid}", text_color=theme.COR_TEXTO_SEC)

        # Fecha a janela de listagem
        if self._win_lista and self._win_lista.winfo_exists():
            self._win_lista.destroy()
            self._win_lista = None
            self._tree_lista = None
            self._busca_var = None

    def _excluir_selecionado_da_lista(self):
        if not (self._tree_lista and self._tree_lista.winfo_exists()):
            return
        sel = self._tree_lista.selection()
        if not sel:
            CTkMessagebox(title="Atenção", message="Selecione um fornecedor na lista.", icon="warning")
            return
        values = self._tree_lista.item(sel[0], "values")
        if not values:
            return

        fid = int(values[0])

        msg = CTkMessagebox(
            title="Confirmar exclusão", message=f"Deseja excluir o fornecedor ID {fid}?",
            icon="question", option_1="Cancelar", option_2="Excluir"
        )
        if msg.get() != "Excluir":
            return

        self.fornecedores = [f for f in self.fornecedores if f["id"] != fid]

        # Se estava sendo editado no formulário, limpa status
        if self.id_selecionado == fid:
            self._limpar_form()

        self._atualizar_tabela_tl()
        CTkMessagebox(title="Sucesso", message="Fornecedor excluído com sucesso", icon="check")

    # ==========================
    # CRUD
    # ==========================

    def _popular_exemplo(self):
        self._inserir_fornecedor(
            razao="Cia das Embalagens LTDA",
            cnpj="12.345.678/0001-90",
            telefone="(91) 99111-2222",
            observacoes="Fornecedor de potes e tampas."
        )
        self._inserir_fornecedor(
            razao="FrioMix Indústria de Alimentos S/A",
            cnpj="98.765.432/0001-10",
            telefone="(91) 99222-3333",
            observacoes="Fornece bases e sabores concentrados."
        )

    def _inserir_fornecedor(self, razao, cnpj, telefone,observacoes):
        item = {
            "id": self._proximo_id,
            "razao": razao,
            "cnpj": "".join(ch for ch in cnpj if ch.isdigit()),
            "telefone": telefone,
            "observacoes": observacoes,
        }
        self._proximo_id += 1
        self.fornecedores.append(item)

    def _validar(self, razao, cnpj, telefone):
        if not razao.strip():
            return "Razão Social é obrigatória."
        cnpj = "".join([c for c in cnpj if c.isdigit()])
        if len(cnpj) != 14:
            return "CNPJ inválido: informe 14 dígitos."
        if not telefone.strip():
            return "Telefone é obrigatório."
        return None

    def _salvar(self):
        razao = self.razao_var.get()
        cnpj = self.cnpj_var.get()
        telefone = self.telefone_var.get()
        observacoes = self.txt_obs.get("1.0", "end").strip()

        erro = self._validar(razao, cnpj, telefone)
        if erro:
            CTkMessagebox(title="Campos inválidos", message=erro, icon="warning")
            return

        cnpj_digits = "".join([c for c in cnpj if c.isdigit()])

        # editar
        if self.id_selecionado is not None:
            for f in self.fornecedores:
                if f["id"] == self.id_selecionado:
                    f.update({
                        "razao": razao.strip(),
                        "cnpj": cnpj_digits,
                        "telefone": telefone.strip(),
                        "observacoes": observacoes,
                    })
                    break

            self._limpar_form()
            # Se a janela de listagem estiver aberta, atualiza a tabela lá
            if self._win_lista and self._win_lista.winfo_exists():
                self._atualizar_tabela_tl()
            CTkMessagebox(title="Sucesso", message="Fornecedor atualizado com sucesso", icon="check")
            return

        # cadastrar novo
        self._inserir_fornecedor(
            razao.strip(), cnpj,telefone.strip(), observacoes
        )
        self._limpar_form()
        if self._win_lista and self._win_lista.winfo_exists():
            self._atualizar_tabela_tl()
        CTkMessagebox(title="Sucesso", message="Fornecedor adicionado com sucesso", icon="check")

    def _excluir(self):
        if self.id_selecionado is None:
            CTkMessagebox(title="Atenção", message="Carregue um fornecedor para excluir (via 'Listar').", icon="warning")
            return

        msg = CTkMessagebox(
            title="Confirmar exclusão",
            message=f"Tem certeza que quer excluir o fornecedor ID {self.id_selecionado}?",
            icon="question", option_1="Cancelar", option_2="Excluir",
        )
        if msg.get() != "Excluir":
            return

        self.fornecedores = [f for f in self.fornecedores if f["id"] != self.id_selecionado]
        self._limpar_form()
        if self._win_lista and self._win_lista.winfo_exists():
            self._atualizar_tabela_tl()
        CTkMessagebox(title="Sucesso", message="Fornecedor excluído com sucesso", icon="check")

    def _limpar_form(self):
        self.id_selecionado = None
        self.razao_var.set("")
        self.cnpj_var.set("")
        self.telefone_var.set("")
        self.txt_obs.delete("1.0", "end")
        self.lbl_status.configure(text="")

    # ==========================
    # Utilitários
    # ==========================

    def _formatar_cnpj(self, digits):
        d = "".join(ch for ch in digits if ch.isdigit())
        if len(d) != 14:
            return digits.strip()
        return f"{d[0:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:14]}"
