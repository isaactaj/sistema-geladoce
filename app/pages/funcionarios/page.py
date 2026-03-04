import customtkinter as ctk
from tkinter import ttk
from CTkMessagebox import CTkMessagebox
from app.config import theme


class PaginaFuncionarios(ctk.CTkFrame):
    def __init__(self, master, sistema):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        self.sistema = sistema
        self.id_selecionado = None

        # ===== CONFIGURAÇÃO DO LAYOUT =====
        self.grid_columnconfigure(0, weight=3)  # Coluna da tabela
        self.grid_columnconfigure(1, weight=2)  # Coluna do cadastro

        self.grid_rowconfigure(2, weight=0)  # busca NÃO cresce
        self.grid_rowconfigure(3, weight=1)  # tabela cresce

        # ===== UI =====
        self._criar_topo()
        self._criar_busca()
        self._criar_tabela()
        self._criar_cadastro()

        self._popular_exemplo()
        self._atualizar_tabela()

    # ==========================
    # UI
    # ==========================
    def _criar_topo(self):
        ctk.CTkLabel(
            self,
            text="Administrativo • Funcionários",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO,
            fg_color="transparent"
        ).grid(row=0, column=0, columnspan=2, padx=30, pady=(14, 6), sticky="w")

        ctk.CTkLabel(
            self,
            text="Gerencie os funcionários da empresa, adicione novos membros à equipe e mantenha as informações atualizadas.",
            font=ctk.CTkFont(family=theme.FONTE, size=13),
            text_color=theme.COR_TEXTO_SEC
        ).grid(row=1, column=0, columnspan=2, padx=30, pady=(0, 12), sticky="w")

    def _criar_busca(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=2, column=0, padx=(30, 12), pady=(0, 10), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        self.busca_var = ctk.StringVar(value="")

        self._busca_entry = ctk.CTkEntry(
            frame,
            textvariable=self.busca_var,
            placeholder_text="🔎 Buscar por nome, CPF, telefone ou tipo",
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
            font=(theme.FONTE, 14),
            rowheight=36,
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
        )
        style.configure(
            "Treeview.Heading",
            font=(theme.FONTE, 14, "bold"),
        )
        style.map(
            "Treeview",
            background=[("selected", "#C1ECFD")],
            foreground=[("selected", "#000000")],
        )

        colunas = ("id", "nome", "cpf", "telefone", "tipo")
        self.tree = ttk.Treeview(box, columns=colunas, show="headings", selectmode="browse")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        self.tree.heading("id", text="ID")
        self.tree.heading("nome", text="Nome")
        self.tree.heading("cpf", text="CPF")
        self.tree.heading("telefone", text="Telefone")
        self.tree.heading("tipo", text="Tipo")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("nome", width=220, anchor="w")
        self.tree.column("cpf", width=140, anchor="center")
        self.tree.column("telefone", width=140, anchor="center")
        self.tree.column("tipo", width=130, anchor="center")

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
        box.grid_rowconfigure(13, weight=1)

        ctk.CTkLabel(
            box,
            text="Cadastro de Funcionário",
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
        self.cpf_var = ctk.StringVar()
        self.telefone_var = ctk.StringVar()
        self.tipo_acesso_var = ctk.StringVar(value="Colaborador")

        def label(texto, r):
            ctk.CTkLabel(
                box,
                text=texto,
                font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
                text_color=theme.COR_TEXTO_SEC,
            ).grid(row=r, column=0, padx=16, pady=(10, 4), sticky="w")

        label("Nome *", 3)
        self.entry_nome = ctk.CTkEntry(box, textvariable=self.nome_var, height=36)
        self.entry_nome.grid(row=4, column=0, padx=16, pady=(0, 10), sticky="ew")

        label("CPF *", 5)
        self.entry_cpf = ctk.CTkEntry(box, textvariable=self.cpf_var, height=36)
        self.entry_cpf.grid(row=6, column=0, padx=16, pady=(0, 10), sticky="ew")

        label("Telefone *", 7)
        self.entry_tel = ctk.CTkEntry(box, textvariable=self.telefone_var, height=36)
        self.entry_tel.grid(row=8, column=0, padx=16, pady=(0, 10), sticky="ew")

        label("Tipo de acesso *", 9)
        self.combo_tipo_acesso = ctk.CTkComboBox(
            box,
            values=["Colaborador", "Administrador"],
            variable=self.tipo_acesso_var,
            height=36,
            state="readonly",
        )
        self.combo_tipo_acesso.grid(row=10, column=0, padx=16, pady=(0, 10), sticky="ew")
        self.combo_tipo_acesso.set("Colaborador")

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
    # Integração com SistemaService
    # ==========================
    def _listar_funcionarios_service(self, termo=""):
        if not hasattr(self.sistema, "listar_funcionarios"):
            return []

        try:
            return self.sistema.listar_funcionarios(termo=termo)
        except TypeError:
            return self.sistema.listar_funcionarios(termo)

    def _obter_funcionario_service(self, funcionario_id):
        if not hasattr(self.sistema, "obter_funcionario"):
            return None
        return self.sistema.obter_funcionario(funcionario_id)

    # ==========================
    # Lógica
    # ==========================
    def _popular_exemplo(self):
        """
        Popula exemplos apenas se o serviço estiver vazio.
        """
        try:
            existentes = self._listar_funcionarios_service()
            if existentes:
                return

            exemplos = [
                {
                    "nome": "Augusto Junior",
                    "cpf": "12345678901",
                    "telefone": "(91) 99999-0001",
                    "tipo_acesso": "Administrador",
                },
                {
                    "nome": "Maria Souza",
                    "cpf": "90903737312",
                    "telefone": "(91) 99779-1031",
                    "tipo_acesso": "Colaborador",
                },
                {
                    "nome": "Tercio Anjos",
                    "cpf": "93029944879",
                    "telefone": "(91) 98669-7773",
                    "tipo_acesso": "Colaborador",
                },
            ]

            for item in exemplos:
                self.sistema.salvar_funcionario(
                    nome=item["nome"],
                    cpf=item["cpf"],
                    telefone=item["telefone"],
                    tipo_acesso=item["tipo_acesso"],
                )

        except TypeError:
            self.lbl_status.configure(
                text="Atualize o SistemaService para suportar cpf e tipo_acesso.",
                text_color=theme.COR_TEXTO_SEC,
            )
        except Exception:
            pass

    def _atualizar_tabela(self):
        filtro = self.busca_var.get().strip().lower()

        for i in self.tree.get_children():
            self.tree.delete(i)

        funcionarios = self._listar_funcionarios_service(termo=filtro)

        for f in funcionarios:
            cpf = self._formatar_cpf(f.get("cpf", ""))
            tipo = f.get("tipo_acesso", "Colaborador")

            self.tree.insert(
                "",
                "end",
                values=(
                    f.get("id", ""),
                    f.get("nome", ""),
                    cpf,
                    f.get("telefone", ""),
                    tipo,
                )
            )

    def _validar(self, nome, cpf, telefone, tipo_acesso):
        if not nome.strip():
            return "Nome é obrigatório."

        cpf_digits = "".join([c for c in cpf if c.isdigit()])
        if len(cpf_digits) != 11:
            return "CPF deve ter 11 números."

        if not telefone.strip():
            return "Telefone é obrigatório."

        if tipo_acesso not in ("Colaborador", "Administrador"):
            return "Tipo de acesso inválido."

        return None

    def _salvar(self):
        nome = self.nome_var.get()
        cpf = self.cpf_var.get()
        telefone = self.telefone_var.get()
        tipo_acesso = self.tipo_acesso_var.get()

        erro = self._validar(nome, cpf, telefone, tipo_acesso)
        if erro:
            CTkMessagebox(title="Campos inválidos", message=erro, icon="warning")
            return

        cpf_digits = "".join([c for c in cpf if c.isdigit()])

        if not hasattr(self.sistema, "salvar_funcionario"):
            CTkMessagebox(
                title="Erro",
                message="SistemaService não possui o método salvar_funcionario.",
                icon="warning"
            )
            return

        try:
            self.sistema.salvar_funcionario(
                nome=nome.strip(),
                cpf=cpf_digits,
                telefone=telefone.strip(),
                tipo_acesso=tipo_acesso,
                funcionario_id=self.id_selecionado,
            )

            editando = self.id_selecionado is not None
            self._limpar_form()
            self._atualizar_tabela()

            CTkMessagebox(
                title="Sucesso",
                message="Funcionário atualizado com sucesso" if editando else "Funcionário adicionado com sucesso",
                icon="check"
            )

        except TypeError:
            CTkMessagebox(
                title="Sistema desatualizado",
                message="Atualize o SistemaService para aceitar os campos: cpf e tipo_acesso.",
                icon="warning"
            )
        except ValueError as e:
            CTkMessagebox(title="Atenção", message=str(e), icon="warning")
        except Exception as e:
            CTkMessagebox(title="Erro", message=f"Erro ao salvar funcionário: {e}", icon="cancel")

    def _excluir(self):
        if self.id_selecionado is None:
            CTkMessagebox(title="Atenção", message="Selecione um funcionário na tabela", icon="warning")
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

        if not hasattr(self.sistema, "excluir_funcionario"):
            CTkMessagebox(
                title="Erro",
                message="SistemaService não possui o método excluir_funcionario.",
                icon="warning"
            )
            return

        try:
            self.sistema.excluir_funcionario(self.id_selecionado)
            self._limpar_form()
            self._atualizar_tabela()
            CTkMessagebox(title="Sucesso", message="Funcionário excluído com sucesso", icon="check")
        except Exception as e:
            CTkMessagebox(title="Erro", message=f"Erro ao excluir funcionário: {e}", icon="cancel")

    def _limpar_form(self):
        self.id_selecionado = None
        self.nome_var.set("")
        self.cpf_var.set("")
        self.telefone_var.set("")
        self.tipo_acesso_var.set("Colaborador")
        self.combo_tipo_acesso.set("Colaborador")
        self.tree.selection_remove(self.tree.selection())
        self.lbl_status.configure(text="")

    def _carregar_selecionado_no_form(self):
        sel = self.tree.selection()
        if not sel:
            return

        values = self.tree.item(sel[0], "values")
        if not values:
            return

        fid = int(values[0])
        self.id_selecionado = fid

        f = self._obter_funcionario_service(fid)
        if not f:
            return

        self.nome_var.set(f.get("nome", ""))
        self.cpf_var.set(self._formatar_cpf(f.get("cpf", "")))
        self.telefone_var.set(f.get("telefone", ""))
        self.tipo_acesso_var.set(f.get("tipo_acesso", "Colaborador"))
        self.combo_tipo_acesso.set(f.get("tipo_acesso", "Colaborador"))

        self.lbl_status.configure(text=f"Editando ID {fid}", text_color=theme.COR_TEXTO_SEC)

    # ==========================
    # Utilitários
    # ==========================
    def _formatar_cpf(self, digits):
        d = "".join(ch for ch in str(digits) if ch.isdigit())
        if len(d) != 11:
            return str(digits).strip()
        return f"{d[0:3]}.{d[3:6]}.{d[6:9]}-{d[9:11]}"