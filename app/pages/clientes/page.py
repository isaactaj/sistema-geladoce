import customtkinter as ctk
from tkinter import ttk
from CTkMessagebox import CTkMessagebox
from app.config import theme

# Página clientes
class PaginaClientes(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        # ===== CONFIGURAÇÃO DO LAYOUT =====
        self.grid_columnconfigure(0, weight=3)  # Coluna da tabela
        self.grid_columnconfigure(1, weight=2)  # Coluna do cadastro

        self.grid_rowconfigure(2, weight=0)  # busca NÃO cresce
        self.grid_rowconfigure(3, weight=1)  # tabela cresce

        # ===== "BANCO" SIMULADO =====
        self._proximo_id = 1
        self.clientes = []

        # ===== UI =====
        self._criar_topo()
        self._criar_busca()
        self._criar_tabela()
        self._criar_cadastro()

        self._popular_exemplo()

    # ==========================
    # UI
    # ==========================

    def _criar_topo(self):
        ctk.CTkLabel(
            self,
            text="Comercial • Clientes",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO,
            fg_color="transparent"
        ).grid(row=0, column=0, columnspan=2, padx=30, pady=(14, 6), sticky="w")


    def _criar_busca(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=2, column=0, padx=(30, 12), pady=(0, 10), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        self.busca_var = ctk.StringVar(value="")

        self._busca_entry = ctk.CTkEntry(
            frame,
            textvariable=self.busca_var,
            placeholder_text="🔎 Buscar",
            height=36,
        )
        self._busca_entry.grid(row=0, column=0, sticky="ew")
        self._busca_entry.bind("<KeyRelease>", lambda e: self._atualizar_tabela())

    def _criar_tabela(self):
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=3, column=0, padx=(30, 12), pady=(0, 20), sticky="nsew")
        box.grid_rowconfigure(0, weight=1)
        box.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            font=(theme.FONTE, 16),
            rowheight=37,
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
        )
        style.configure(
            "Treeview.Heading",
            font=(theme.FONTE, 16, "bold"),
        )
        style.map(
            "Treeview",
            background=[("selected", "#C1ECFD")],
            foreground=[("selected", "#000000")],
        )

        # Colunas com e-mail e campo unificado CPF/CNPJ
        colunas = ("id", "nome", "cpf_cnpj", "telefone", "email")
        self.tree = ttk.Treeview(box, columns=colunas, show="headings", selectmode="browse")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        self.tree.heading("id", text="ID")
        self.tree.heading("nome", text="Nome")
        self.tree.heading("cpf_cnpj", text="CPF/CNPJ")
        self.tree.heading("telefone", text="Telefone")
        self.tree.heading("email", text="E-mail")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("nome", width=240, anchor="w")
        self.tree.column("cpf_cnpj", width=160, anchor="center")
        self.tree.column("telefone", width=140, anchor="center")
        self.tree.column("email", width=220, anchor="w")

        scroll = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns", padx=(0, 12), pady=12)

        scroll_x = ttk.Scrollbar(box, orient="horizontal", command=self.tree.xview)
        scroll_x.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))

        self.tree.configure(yscrollcommand=scroll.set, xscrollcommand=scroll_x.set)

        self.tree.bind("<<TreeviewSelect>>", lambda e: self._carregar_selecionado_no_form())

    def _criar_cadastro(self):
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=2, column=1, rowspan=2, padx=(12, 30), pady=(0, 20), sticky="nsew")
        box.grid_rowconfigure(0, weight=1)
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(11, weight=1)

        ctk.CTkLabel(
            box,
            text="Cadastro de Cliente",
            font=ctk.CTkFont(family=theme.FONTE, size=16, weight="bold"),
            text_color=theme.COR_TEXTO,
            anchor="center",
        ).grid(row=1, column=0, padx=16, pady=(6, 4), sticky="ew")

        self.lbl_status = ctk.CTkLabel(
            box,
            text="",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC,
        )
        self.lbl_status.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="w")

        self.nome_var = ctk.StringVar()
        self.cpf_cnpj_var = ctk.StringVar()
        self.telefone_var = ctk.StringVar()
        self.email_var = ctk.StringVar()
        self.id_selecionado = None

        def label(texto, r):
            ctk.CTkLabel(
                box,
                text=texto,
                font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
                text_color=theme.COR_TEXTO_SEC,
            ).grid(row=r, column=0, padx=16, pady=(10, 4), sticky="w")

        label("Nome", 3)
        self.entry_nome = ctk.CTkEntry(box, textvariable=self.nome_var, height=36)
        self.entry_nome.grid(row=4, column=0, padx=16, pady=(0, 10), sticky="ew")

        label("CPF/CNPJ", 5)
        self.entry_doc = ctk.CTkEntry(box, textvariable=self.cpf_cnpj_var, height=36)
        self.entry_doc.grid(row=6, column=0, padx=16, sticky="ew")

        label("Telefone", 7)
        self.entry_tel = ctk.CTkEntry(box, textvariable=self.telefone_var, height=36)
        self.entry_tel.grid(row=8, column=0, padx=16, sticky="ew")

        label("E-mail", 9)
        self.entry_email = ctk.CTkEntry(box, textvariable=self.email_var, height=36)
        self.entry_email.grid(row=10, column=0, padx=16, sticky="ew")

        botoes = ctk.CTkFrame(box, fg_color="transparent")
        botoes.grid(row=11, column=0, padx=16, pady=(16, 16), sticky="ew")
        botoes.grid_columnconfigure((0, 1), weight=1)

        self.btn_salvar = ctk.CTkButton(
            botoes,
            text="Salvar",
            height=36,
            fg_color="#FFFFFF",
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._salvar
        )
        self.btn_salvar.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.btn_limpar = ctk.CTkButton(
            botoes,
            text="Limpar",
            height=36,
            fg_color="#FFFFFF",
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._limpar_form
        )
        self.btn_limpar.grid(row=0, column=1, padx=(8, 0), sticky="ew")

        self.btn_excluir = ctk.CTkButton(
            box,
            text="Excluir selecionado",
            height=36,
            fg_color="#FFFFFF",
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._excluir
        )
        self.btn_excluir.grid(row=12, column=0, padx=16, pady=(0, 16), sticky="ew")

    # ==========================
    # Lógica
    # ==========================

    def _popular_exemplo(self):
        self._inserir_cliente("Padaria Pão Quente", "12.345.678/0001-90", "(91) 99999-0001", "contato@paoquente.com")
        self._inserir_cliente("Rodrigo Araujo", "909.037.373-12", "(91) 99779-1031", "rodrigo@example.com")
        self._inserir_cliente("Carla Souza", "930.299.448-79", "(91) 98669-7773", "carla@example.com")
        self._atualizar_tabela()

    def _inserir_cliente(self, nome, cpf_cnpj, telefone, email):
        item = {
            "id": self._proximo_id,
            "nome": nome,
            "cpf_cnpj": cpf_cnpj,
            "telefone": telefone,
            "email": email
        }
        self._proximo_id += 1
        self.clientes.append(item)

    def _atualizar_tabela(self):
        filtro = self.busca_var.get().strip().lower()
        for i in self.tree.get_children():
            self.tree.delete(i)

        for c in self.clientes:
            texto = f'{c["nome"]} {c["cpf_cnpj"]} {c["telefone"]} {c["email"]}'.lower()
            if (not filtro) or (filtro in texto):
                self.tree.insert(
                    "",
                    "end",
                    values=(c["id"], c["nome"], c["cpf_cnpj"], c["telefone"], c["email"])
                )

    def _validar(self, nome, cpf_cnpj, telefone, email):
        if not nome.strip():
            return "Nome é obrigatório."

        # limpa apenas dígitos para validar comprimento
        doc_digits = "".join([ch for ch in cpf_cnpj if ch.isdigit()])
        if len(doc_digits) not in (11, 14):
            return "CPF/CNPJ inválido: informe 11 dígitos (CPF) ou 14 dígitos (CNPJ)."

        if not telefone.strip():
            return "Telefone é obrigatório."

        if email.strip():
            if ("@" not in email) or (email.count("@") != 1) or (email.startswith("@") or email.endswith("@")):
                return "E-mail inválido."
        # Se quiser obrigar e-mail, troque acima para: if not email.strip(): return "E-mail é obrigatório."
        return None

    def _salvar(self):
        nome = self.nome_var.get()
        cpf_cnpj = self.cpf_cnpj_var.get()
        telefone = self.telefone_var.get()
        email = self.email_var.get()

        erro = self._validar(nome, cpf_cnpj, telefone, email)
        if erro:
            CTkMessagebox(title="Campos inválidos", message=erro, icon="warning")
            return

        # Normaliza doc apenas com dígitos (você pode manter formatado se preferir)
        doc_digits = "".join([c for c in cpf_cnpj if c.isdigit()])

        # editar
        if self.id_selecionado is not None:
            for c in self.clientes:
                if c["id"] == self.id_selecionado:
                    c["nome"] = nome.strip()
                    c["cpf_cnpj"] = doc_digits
                    c["telefone"] = telefone.strip()
                    c["email"] = email.strip()
                    break

            self._limpar_form()
            self._atualizar_tabela()
            CTkMessagebox(title="Sucesso", message="Cliente atualizado com sucesso", icon="check")
            return

        # cadastrar novo
        self._inserir_cliente(nome.strip(), doc_digits, telefone.strip(), email.strip())
        self._limpar_form()
        self._atualizar_tabela()
        CTkMessagebox(title="Sucesso", message="Cliente adicionado com sucesso", icon="check")

    def _excluir(self):
        if self.id_selecionado is None:
            CTkMessagebox(title="Atenção", message="Selecione um cliente na tabela", icon="warning")
            return

        msg = CTkMessagebox(
            title="Confirmar exclusão",
            message="Tem certeza que quer excluir?",
            icon="question",
            option_1="Cancelar",
            option_2="Excluir",
        )

        if msg.get() != "Excluir":
            return

        self.clientes = [c for c in self.clientes if c["id"] != self.id_selecionado]
        self._limpar_form()
        self._atualizar_tabela()
        CTkMessagebox(title="Sucesso", message="Cliente excluído com sucesso", icon="check")

    def _limpar_form(self):
        self.id_selecionado = None
        self.nome_var.set("")
        self.cpf_cnpj_var.set("")
        self.telefone_var.set("")
        self.email_var.set("")
        self.tree.selection_remove(self.tree.selection())
        self.lbl_status.configure(text="")

    def _carregar_selecionado_no_form(self):
        sel = self.tree.selection()
        if not sel:
            return

        values = self.tree.item(sel[0], "values")
        if not values:
            return

        cid = int(values[0])
        self.id_selecionado = cid

        for c in self.clientes:
            if c["id"] == cid:
                self.nome_var.set(c["nome"])
                self.cpf_cnpj_var.set(c["cpf_cnpj"])
                self.telefone_var.set(c["telefone"])
                self.email_var.set(c["email"])
                break

        self.lbl_status.configure(text=f"Editando ID {cid}", text_color=theme.COR_TEXTO_SEC)