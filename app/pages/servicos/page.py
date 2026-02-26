import customtkinter as ctk
from tkinter import ttk, messagebox
from app.config import theme
import datetime as dt


class PaginaAgendamentoCarrinhos(ctk.CTkFrame):
    """
    Tela de agendamento de carrinhos de picolé.

    - Esquerda: filtros + lista de carrinhos
    - Direita: formulário de agendamento + agenda do dia
    """

    def __init__(self, master):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        # Layout geral
        self.grid_columnconfigure(0, weight=3)  # lista carrinhos
        self.grid_columnconfigure(1, weight=2)  # formulário + agenda

        self.grid_rowconfigure(0, weight=0)  # topo
        self.grid_rowconfigure(1, weight=0)  # subtítulo
        self.grid_rowconfigure(2, weight=0)  # filtros carrinho
        self.grid_rowconfigure(3, weight=1)  # lista carrinhos cresce

        # --------- Estado ---------
        # Filtros carrinhos
        self.busca_carrinho_var = ctk.StringVar(value="")
        self.status_carrinho_var = ctk.StringVar(value="Todos")

        # Form agendamento
        hoje = dt.date.today().strftime("%Y-%m-%d")
        self.data_var = ctk.StringVar(value=hoje)
        self.hora_ini_var = ctk.StringVar(value="08:00")
        self.hora_fim_var = ctk.StringVar(value="12:00")
        self.local_var = ctk.StringVar(value="")
        self.status_ag_var = ctk.StringVar(value="Agendado")
        self.carrinho_escolhido = None
        self.motorista_var = ctk.StringVar(value="")
        self.observacoes_widget = None  # CTkTextbox

        # Estado de edição
        self._agendamento_em_edicao_id = None  # quando não for None, está editando

        # Dados (mock)
        self.carrinhos = self._mock_carrinhos()
        self.funcionarios = self._mock_funcionarios()
        self.agendamentos = self._mock_agendamentos()

        # UI
        self._topo()
        self._filtros_carrinhos()
        self._lista_carrinhos_ui()
        self._form_agendamento_ui()

        # Render inicial
        self._render_lista_carrinhos()
        self._render_agenda_do_dia()

    # -------------------- UI TOPO --------------------
    def _topo(self):
        ctk.CTkLabel(
            self,
            text="Agendamentos • Carrinhos de Picolé",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, columnspan=2, padx=30, pady=(14, 6), sticky="w")

        ctk.CTkLabel(
            self,
            text="Programe saídas, horários, responsáveis e locais por carrinho.",
            font=ctk.CTkFont(family=theme.FONTE, size=13),
            text_color=theme.COR_TEXTO_SEC
        ).grid(row=1, column=0, columnspan=2, padx=30, pady=(0, 12), sticky="w")

    # -------------------- UI FILTROS LISTA (ESQ) --------------------
    def _filtros_carrinhos(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=2, column=0, padx=(30, 12), pady=(0, 10), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        self.entry_busca_car = ctk.CTkEntry(
            frame,
            textvariable=self.busca_carrinho_var,
            placeholder_text="🔎 Buscar carrinho por nome/ID…",
            height=36
        )
        self.entry_busca_car.grid(row=0, column=0, sticky="ew")
        self.entry_busca_car.bind("<KeyRelease>", lambda e: self._render_lista_carrinhos())

        self.combo_status_car = ctk.CTkComboBox(
            frame,
            values=["Todos", "Disponível", "Em rota", "Manutenção"],
            width=160,
            command=lambda _: self._render_lista_carrinhos()
        )
        self.combo_status_car.set("Todos")
        self.combo_status_car.grid(row=0, column=1, padx=(10, 0))

    def _lista_carrinhos_ui(self):
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=3, column=0, padx=(30, 12), pady=(0, 20), sticky="nsew")
        box.grid_rowconfigure(0, weight=1)
        box.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=(theme.FONTE, 12), rowheight=30)
        style.configure("Treeview.Heading", font=(theme.FONTE, 12, "bold"))
        style.map("Treeview", background=[("selected", theme.COR_HOVER)])

        ctk.CTkLabel(
            box,
            text="Carrinhos",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=12, pady=(12, 0), sticky="w")

        self.tree_carrinhos = ttk.Treeview(
            box,
            columns=("status", "capacidade"),
            show="tree headings"
        )
        self.tree_carrinhos.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 12))

        self.tree_carrinhos.heading("#0", text="Identificação")
        self.tree_carrinhos.heading("status", text="Status")
        self.tree_carrinhos.heading("capacidade", text="Capacidade")

        self.tree_carrinhos.column("#0", width=240, anchor="w")
        self.tree_carrinhos.column("status", width=120, anchor="center")
        self.tree_carrinhos.column("capacidade", width=110, anchor="center")

        scroll_y = ttk.Scrollbar(box, orient="vertical", command=self.tree_carrinhos.yview)
        scroll_y.grid(row=1, column=1, sticky="ns", padx=(0, 12), pady=(6, 12))
        self.tree_carrinhos.configure(yscrollcommand=scroll_y.set)

        # Duplo clique: seleciona carrinho no formulário
        self.tree_carrinhos.bind("<Double-1>", lambda e: self._usar_carrinho_selecionado())

        # Tags para cores de status
        self.tree_carrinhos.tag_configure("Disponível", foreground="#2E7D32")   # verde
        self.tree_carrinhos.tag_configure("Em rota", foreground="#EF6C00")       # laranja
        self.tree_carrinhos.tag_configure("Manutenção", foreground="#757575")    # cinza

    # -------------------- UI FORM + AGENDA (DIR) --------------------
    def _form_agendamento_ui(self):
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=2, column=1, rowspan=2, padx=(12, 30), pady=(0, 20), sticky="nsew")
        box.grid_columnconfigure(0, weight=1)
        # rows: título, data/nav, form, botoes, agenda título, agenda lista, remover
        for r in range(7):
            box.grid_rowconfigure(r, weight=0)
        box.grid_rowconfigure(5, weight=1)  # agenda lista cresce

        # Título
        ctk.CTkLabel(
            box,
            text="Novo agendamento",
            font=ctk.CTkFont(family=theme.FONTE, size=16, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        # Data + navegação
        linha_data = ctk.CTkFrame(box, fg_color="transparent")
        linha_data.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="ew")
        linha_data.grid_columnconfigure(1, weight=1)

        btn_prev = ctk.CTkButton(linha_data, text="←", width=38, command=lambda: self._navegar_data(-1))
        btn_prev.grid(row=0, column=0, padx=(0, 6))

        entry_data = ctk.CTkEntry(linha_data, textvariable=self.data_var, height=34, placeholder_text="AAAA-MM-DD")
        entry_data.grid(row=0, column=1, sticky="ew")

        btn_next = ctk.CTkButton(linha_data, text="→", width=38, command=lambda: self._navegar_data(1))
        btn_next.grid(row=0, column=2, padx=(6, 0))

        btn_hoje = ctk.CTkButton(linha_data, text="Hoje", width=70, command=lambda: self._set_data(dt.date.today()))
        btn_hoje.grid(row=0, column=3, padx=(8, 0))

        btn_amanha = ctk.CTkButton(linha_data, text="Amanhã", width=70,
                                   command=lambda: self._set_data(dt.date.today() + dt.timedelta(days=1)))
        btn_amanha.grid(row=0, column=4, padx=(6, 0))

        # Formulário
        form = ctk.CTkFrame(box, fg_color="#FFFFFF", corner_radius=12)
        form.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="ew")
        for c in range(4):
            form.grid_columnconfigure(c, weight=1)

        # Horários
        ctk.CTkLabel(form, text="Início (HH:MM)", text_color=theme.COR_TEXTO).grid(row=0, column=0, padx=10, pady=(12, 4), sticky="w")
        combo_ini = ctk.CTkComboBox(form, values=self._horarios_padrao(), variable=self.hora_ini_var)
        combo_ini.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(form, text="Fim (HH:MM)", text_color=theme.COR_TEXTO).grid(row=0, column=1, padx=10, pady=(12, 4), sticky="w")
        combo_fim = ctk.CTkComboBox(form, values=self._horarios_padrao(), variable=self.hora_fim_var)
        combo_fim.grid(row=1, column=1, padx=10, pady=(0, 8), sticky="ew")

        # Carrinho
        ctk.CTkLabel(form, text="Carrinho", text_color=theme.COR_TEXTO).grid(row=0, column=2, padx=10, pady=(12, 4), sticky="w")
        self.combo_carrinho = ctk.CTkComboBox(
            form,
            values=[f'{c["nome"]} ({c["id_externo"]})' for c in self.carrinhos]
        )
        self.combo_carrinho.grid(row=1, column=2, padx=10, pady=(0, 8), sticky="ew")

        # Motorista/Responsável
        ctk.CTkLabel(form, text="Responsável", text_color=theme.COR_TEXTO).grid(row=0, column=3, padx=10, pady=(12, 4), sticky="w")
        self.combo_motorista = ctk.CTkComboBox(
            form,
            values=[f'{f["nome"]} • {f["telefone"]}' for f in self.funcionarios],
            variable=self.motorista_var
        )
        self.combo_motorista.grid(row=1, column=3, padx=10, pady=(0, 8), sticky="ew")

        # Local/Evento
        ctk.CTkLabel(form, text="Local / Evento", text_color=theme.COR_TEXTO).grid(row=2, column=0, columnspan=2, padx=10, pady=(6, 4), sticky="w")
        entry_local = ctk.CTkEntry(form, textvariable=self.local_var, height=34, placeholder_text="Ex.: Escola Alfa, Praça X, Bairro Y…")
        entry_local.grid(row=3, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="ew")

        # Status
        ctk.CTkLabel(form, text="Status", text_color=theme.COR_TEXTO).grid(row=2, column=2, padx=10, pady=(6, 4), sticky="w")
        self.combo_status_ag = ctk.CTkComboBox(form, values=["Agendado", "Confirmado", "Cancelado"])
        self.combo_status_ag.set("Agendado")
        self.combo_status_ag.grid(row=3, column=2, padx=10, pady=(0, 8), sticky="ew")

        # Observações
        ctk.CTkLabel(form, text="Observações", text_color=theme.COR_TEXTO).grid(row=2, column=3, padx=10, pady=(6, 4), sticky="w")
        self.observacoes_widget = ctk.CTkTextbox(form, height=64)
        self.observacoes_widget.grid(row=3, column=3, padx=10, pady=(0, 10), sticky="ew")

        # Botões salvar/limpar
        linha_btns = ctk.CTkFrame(box, fg_color="transparent")
        linha_btns.grid(row=3, column=0, padx=16, pady=(2, 10), sticky="ew")
        linha_btns.grid_columnconfigure(0, weight=1)
        linha_btns.grid_columnconfigure(1, weight=1)

        self.btn_salvar = ctk.CTkButton(linha_btns, text="Salvar agendamento", height=38, fg_color="#FFFFFF",
                                        hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
                                        command=self._salvar_agendamento)
        self.btn_salvar.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        btn_limpar = ctk.CTkButton(linha_btns, text="Limpar", height=38, command=self._limpar_form)
        btn_limpar.grid(row=0, column=1, padx=(6, 0), sticky="ew")

        # Agenda do dia (título)
        ctk.CTkLabel(
            box,
            text="Agenda do dia",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=4, column=0, padx=16, pady=(8, 6), sticky="w")

        # Agenda do dia (lista)
        box_agenda = ctk.CTkFrame(box, fg_color="#FFFFFF", corner_radius=12)
        box_agenda.grid(row=5, column=0, padx=16, pady=(0, 10), sticky="nsew")
        box_agenda.grid_rowconfigure(0, weight=1)
        box_agenda.grid_columnconfigure(0, weight=1)

        self.tree_agenda = ttk.Treeview(
            box_agenda,
            columns=("hora", "carrinho", "motorista", "local", "status"),
            show="headings"
        )
        self.tree_agenda.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self.tree_agenda.heading("hora", text="Horário")
        self.tree_agenda.heading("carrinho", text="Carrinho")
        self.tree_agenda.heading("motorista", text="Responsável")
        self.tree_agenda.heading("local", text="Local/Evento")
        self.tree_agenda.heading("status", text="Status")

        self.tree_agenda.column("hora", width=120, anchor="center")
        self.tree_agenda.column("carrinho", width=160, anchor="w")
        self.tree_agenda.column("motorista", width=180, anchor="w")
        self.tree_agenda.column("local", width=220, anchor="w")
        self.tree_agenda.column("status", width=110, anchor="center")

        scroll_ag = ttk.Scrollbar(box_agenda, orient="vertical", command=self.tree_agenda.yview)
        scroll_ag.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
        self.tree_agenda.configure(yscrollcommand=scroll_ag.set)

        # Duplo clique: carregar para edição
        self.tree_agenda.bind("<Double-1>", lambda e: self._editar_agendamento_selecionado())

        # Remover
        self.btn_remover = ctk.CTkButton(
            box,
            text="Remover agendamento selecionado",
            height=36,
            fg_color="#FFFFFF",
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._remover_agendamento_sel
        )
        self.btn_remover.grid(row=6, column=0, padx=16, pady=(0, 16), sticky="ew")

    # -------------------- MOCK DATA --------------------
    def _mock_carrinhos(self):
        return [
            {"id": 1, "id_externo": "CAR-01", "nome": "Carrinho 01", "capacidade": 250, "status": "Disponível"},
            {"id": 2, "id_externo": "CAR-02", "nome": "Carrinho 02", "capacidade": 220, "status": "Em rota"},
            {"id": 3, "id_externo": "CAR-03", "nome": "Carrinho 03", "capacidade": 260, "status": "Disponível"},
            {"id": 4, "id_externo": "CAR-04", "nome": "Carrinho 04", "capacidade": 210, "status": "Manutenção"},
        ]

    def _mock_funcionarios(self):
        return [
            {"id": 1, "nome": "Carlos Lima", "telefone": "(91) 99999-0001"},
            {"id": 2, "nome": "Ana Paula", "telefone": "(91) 98888-0002"},
            {"id": 3, "nome": "Rogério Silva", "telefone": "(91) 97777-0003"},
        ]

    def _mock_agendamentos(self):
        # Começa vazio; você pode inserir exemplos se quiser.
        return []

    # -------------------- LISTA CARRINHOS (ESQ) --------------------
    def _render_lista_carrinhos(self):
        for i in self.tree_carrinhos.get_children():
            self.tree_carrinhos.delete(i)

        termo = self.busca_carrinho_var.get().strip().lower()
        status = self.combo_status_car.get()

        for c in self.carrinhos:
            if status != "Todos" and c["status"] != status:
                continue
            texto = f'{c["nome"]} {c["id_externo"]}'.lower()
            if termo and termo not in texto:
                continue
            tag = c["status"]
            self.tree_carrinhos.insert(
                "", "end",
                text=f'{c["nome"]} ({c["id_externo"]})',
                values=(c["status"], c["capacidade"]),
                tags=(tag, f'id-{c["id"]}')
            )

    def _usar_carrinho_selecionado(self):
        sel = self.tree_carrinhos.selection()
        if not sel:
            return
        item_id = sel[0]
        tags = self.tree_carrinhos.item(item_id, "tags")

        cid = None
        for t in tags:
            if str(t).startswith("id-"):
                cid = int(t.split("-")[1])
                break
        if cid is None:
            return

        car = next((x for x in self.carrinhos if x["id"] == cid), None)
        if not car:
            return

        # Preenche combo do carrinho
        self.combo_carrinho.set(f'{car["nome"]} ({car["id_externo"]})')

        # Suggest responsável disponível (se quiser)
        if self.funcionarios:
            self.combo_motorista.set(f'{self.funcionarios[0]["nome"]} • {self.funcionarios[0]["telefone"]}')

    # -------------------- FORMULÁRIO --------------------
    def _set_data(self, date_obj: dt.date):
        self.data_var.set(date_obj.strftime("%Y-%m-%d"))
        self._render_agenda_do_dia()

    def _navegar_data(self, delta_days: int):
        try:
            d = dt.date.fromisoformat(self.data_var.get())
        except ValueError:
            d = dt.date.today()
        self._set_data(d + dt.timedelta(days=delta_days))

    def _horarios_padrao(self):
        # Gera faixas de 30 em 30 min
        horarios = []
        h, m = 6, 0
        while h < 23 or (h == 23 and m == 0):
            horarios.append(f"{h:02d}:{m:02d}")
            m += 30
            if m >= 60:
                m = 0
                h += 1
        return horarios

    def _pegar_obs(self):
        return self.observacoes_widget.get("1.0", "end").strip()

    def _set_obs(self, text: str):
        self.observacoes_widget.delete("1.0", "end")
        if text:
            self.observacoes_widget.insert("1.0", text)

    def _parse_hora(self, s: str):
        try:
            h, m = s.split(":")
            return int(h) * 60 + int(m)
        except Exception:
            return None

    def _validar_inputs(self):
        # Data
        try:
            data = dt.date.fromisoformat(self.data_var.get().strip())
        except ValueError:
            return False, "Data inválida. Use o formato AAAA-MM-DD."

        # Horas
        ini = self._parse_hora(self.hora_ini_var.get().strip())
        fim = self._parse_hora(self.hora_fim_var.get().strip())
        if ini is None or fim is None:
            return False, "Horários inválidos. Use HH:MM (ex.: 08:00)."
        if fim <= ini:
            return False, "Hora de fim deve ser maior que a de início."

        # Carrinho
        carrinho_txt = self.combo_carrinho.get().strip()
        if not carrinho_txt:
            return False, "Selecione um carrinho."

        carrinho = self._resolver_carrinho_por_texto(carrinho_txt)
        if not carrinho:
            return False, "Carrinho selecionado não encontrado."

        # Motorista
        motorista_txt = self.combo_motorista.get().strip()
        if not motorista_txt:
            return False, "Selecione um responsável."
        mot = self._resolver_motorista_por_texto(motorista_txt)
        if not mot:
            return False, "Responsável selecionado não encontrado."

        # Local
        if not self.local_var.get().strip():
            return False, "Informe o local/evento."

        return True, ""

    def _resolver_carrinho_por_texto(self, txt: str):
        # Formato: "Carrinho 01 (CAR-01)"
        for c in self.carrinhos:
            if txt.startswith(c["nome"]) and c["id_externo"] in txt:
                return c
        return None

    def _resolver_motorista_por_texto(self, txt: str):
        # Formato: "Nome • (telefone)"
        nome = txt.split("•")[0].strip()
        for f in self.funcionarios:
            if f["nome"] == nome:
                return f
        return None

    # -------------------- AGENDA --------------------
    def _render_agenda_do_dia(self):
        for i in self.tree_agenda.get_children():
            self.tree_agenda.delete(i)

        try:
            data = dt.date.fromisoformat(self.data_var.get().strip())
        except ValueError:
            return

        do_dia = [a for a in self.agendamentos if a["data"] == data]

        # Ordena por início
        do_dia.sort(key=lambda x: x["inicio_min"])

        for a in do_dia:
            horario = f'{a["inicio"]}–{a["fim"]}'
            carrinho_txt = f'{a["carrinho_nome"]} ({a["carrinho_id_externo"]})'
            motorista_txt = a["motorista_nome"]
            local = a["local"]
            status = a["status"]

            self.tree_agenda.insert("", "end",
                                    values=(horario, carrinho_txt, motorista_txt, local, status),
                                    tags=(f'ag-{a["id"]}',))

    def _conflito(self, novo):
        """
        Verifica conflito com agendamentos existentes:
        - mesmo carrinho no intervalo
        - mesmo motorista no intervalo
        """
        def overlap(a1, a2, b1, b2):
            return a1 < b2 and a2 > b1  # interseção de intervalos abertos

        conflitos = []
        for a in self.agendamentos:
            # Ignora o próprio ao editar
            if self._agendamento_em_edicao_id is not None and a["id"] == self._agendamento_em_edicao_id:
                continue
            if a["data"] != novo["data"]:
                continue

            if overlap(novo["inicio_min"], novo["fim_min"], a["inicio_min"], a["fim_min"]):
                if a["carrinho_id"] == novo["carrinho_id"]:
                    conflitos.append(f'Conflito: Carrinho já agendado {a["inicio"]}–{a["fim"]} em {a["local"]}.')
                if a["motorista_id"] == novo["motorista_id"]:
                    conflitos.append(f'Conflito: Responsável já alocado {a["inicio"]}–{a["fim"]} no {a["local"]}.')
        return conflitos

    def _salvar_agendamento(self):
        ok, msg = self._validar_inputs()
        if not ok:
            messagebox.showwarning("Validação", msg)
            return

        data = dt.date.fromisoformat(self.data_var.get().strip())
        ini_txt = self.hora_ini_var.get().strip()
        fim_txt = self.hora_fim_var.get().strip()
        ini_min = self._parse_hora(ini_txt)
        fim_min = self._parse_hora(fim_txt)

        car = self._resolver_carrinho_por_texto(self.combo_carrinho.get().strip())
        mot = self._resolver_motorista_por_texto(self.combo_motorista.get().strip())

        novo = {
            "id": self._agendamento_em_edicao_id or (self._prox_id()),
            "data": data,
            "inicio": ini_txt,
            "fim": fim_txt,
            "inicio_min": ini_min,
            "fim_min": fim_min,
            "carrinho_id": car["id"],
            "carrinho_nome": car["nome"],
            "carrinho_id_externo": car["id_externo"],
            "motorista_id": mot["id"],
            "motorista_nome": mot["nome"],
            "local": self.local_var.get().strip(),
            "status": self.combo_status_ag.get().strip(),
            "obs": self._pegar_obs()
        }

        conflitos = self._conflito(novo)
        if conflitos:
            messagebox.showerror("Conflito de horário", "\n".join(conflitos))
            return

        if self._agendamento_em_edicao_id is None:
            # Novo
            self.agendamentos.append(novo)
        else:
            # Atualiza existente
            for i, a in enumerate(self.agendamentos):
                if a["id"] == self._agendamento_em_edicao_id:
                    self.agendamentos[i] = novo
                    break

        self._limpar_form()
        self._render_agenda_do_dia()
        messagebox.showinfo("Agendamento", "Agendamento salvo com sucesso!")

    def _prox_id(self):
        return (max([a["id"] for a in self.agendamentos], default=0) + 1) or 1

    def _limpar_form(self):
        self._agendamento_em_edicao_id = None
        # Mantém a mesma data; limpa demais campos
        self.hora_ini_var.set("08:00")
        self.hora_fim_var.set("12:00")
        self.local_var.set("")
        self.combo_status_ag.set("Agendado")
        self._set_obs("")
        # Não limpa seleção de carrinho/motorista para facilitar cadastros em lote

    def _agendamento_por_tag(self, tag):
        if not tag.startswith("ag-"):
            return None
        aid = int(tag.split("-")[1])
        return next((a for a in self.agendamentos if a["id"] == aid), None)

    def _editar_agendamento_selecionado(self):
        sel = self.tree_agenda.selection()
        if not sel:
            return
        item_id = sel[0]
        # Pega o id pelo valor horário e/ou tags
        tags = self.tree_agenda.item(item_id, "tags")
        if not tags:
            return
        a = self._agendamento_por_tag(tags[0])
        if not a:
            return

        # Carrega no form
        self._agendamento_em_edicao_id = a["id"]
        self.data_var.set(a["data"].strftime("%Y-%m-%d"))
        self.hora_ini_var.set(a["inicio"])
        self.hora_fim_var.set(a["fim"])
        self.combo_carrinho.set(f'{a["carrinho_nome"]} ({a["carrinho_id_externo"]})')
        mot = next((f for f in self.funcionarios if f["id"] == a["motorista_id"]), None)
        if mot:
            self.combo_motorista.set(f'{mot["nome"]} • {mot["telefone"]}')
        self.local_var.set(a["local"])
        self.combo_status_ag.set(a["status"])
        self._set_obs(a.get("obs", ""))

        messagebox.showinfo("Edição", "Agendamento carregado para edição.\nAltere os campos e clique em Salvar.")

    def _remover_agendamento_sel(self):
        sel = self.tree_agenda.selection()
        if not sel:
            messagebox.showwarning("Remover", "Selecione um agendamento na lista.")
            return
        tags = self.tree_agenda.item(sel[0], "tags")
        if not tags:
            return
        a = self._agendamento_por_tag(tags[0])
        if not a:
            return
        if not messagebox.askyesno("Confirmar", "Deseja remover este agendamento?"):
            return
        self.agendamentos = [x for x in self.agendamentos if x["id"] != a["id"]]
        self._render_agenda_do_dia()
        # Se estiver editando o mesmo, limpa form
        if self._agendamento_em_edicao_id == a["id"]:
            self._limpar_form()
        messagebox.showinfo("Removido", "Agendamento removido.")

# FIM DA CLASSE