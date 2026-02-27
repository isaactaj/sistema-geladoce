# -*- coding: utf-8 -*-
"""
Página com abas:
  - Agendamentos de carrinhos de picolé
  - Delivery

Requisitos: customtkinter, tkinter
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
import datetime as dt

# ===========================================================
# TEMA
# Tenta usar seu tema; se não existir, aplica um tema padrão.
# ===========================================================
try:
    from app.config import theme  # seu tema
except Exception:
    class _DefaultTheme:
        FONTE = "Segoe UI"
        COR_FUNDO = "#F5F7FA"
        COR_PAINEL = "#EDF2F7"
        COR_TEXTO = "#1F2937"
        COR_TEXTO_SEC = "#6B7280"
        COR_HOVER = "#E5E7EB"

        @staticmethod
        def fmt_dinheiro(valor: float) -> str:
            # Formato brasileiro com vírgula decimal
            s = f"{valor:,.2f}"
            return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")
    theme = _DefaultTheme()


# ===========================================================
# ABA 1: AGENDAMENTOS
# ===========================================================
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
        style.configure("Treeview", font=(theme.FONTE, 12), rowheight=55)
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
        return max([a["id"] for a in self.agendamentos], default=0) + 1

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


# ===========================================================
# ABA 2: DELIVERY
# ===========================================================
class PaginaDelivery(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        # Layout: esquerda (pedido) / direita (lista do dia)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # -------- Estado --------
        # Cliente / endereço
        self.cli_nome_var = ctk.StringVar(value="")
        self.cli_tel_var = ctk.StringVar(value="")
        self.end_rua_var = ctk.StringVar(value="")
        self.end_num_var = ctk.StringVar(value="")
        self.end_bairro_var = ctk.StringVar(value="")
        self.end_cidade_var = ctk.StringVar(value="Belém")
        self.end_comp_var = ctk.StringVar(value="")

        # Pedido
        self.data_var = ctk.StringVar(value=dt.date.today().strftime("%Y-%m-%d"))
        self.prev_saida_var = ctk.StringVar(value="00:30")  # HH:MM
        self.pag_var = ctk.StringVar(value="Pix")
        self.status_var = ctk.StringVar(value="Pendente")
        self.taxa_var = ctk.StringVar(value="5.00")

        # Itens
        self.produto_var = ctk.StringVar(value="")
        self.qtd_var = ctk.StringVar(value="1")
        self.carrinho_itens = []  # [{id, nome, preco, qtd}]

        # Entregador
        self.entregador_var = ctk.StringVar(value="")

        # Observações
        self.obs_widget = None

        # Edição
        self._pedido_em_edicao_id = None

        # Data mock
        self.produtos = self._mock_produtos()
        self.entregadores = self._mock_entregadores()
        self.entregas = []  # lista de pedidos

        # UI
        self._titulo()
        self._pedido_form()
        self._lista_dia()

        self._render_itens()
        self._render_entregas_dia()

    # ---------- UI ----------
    def _titulo(self):
        ctk.CTkLabel(
            self, text="Delivery", 
            font=ctk.CTkFont(family=theme.FONTE, size=16, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        ctk.CTkLabel(
            self,
            text="Cadastre pedidos, calcule total, atribua entregador e acompanhe o status.",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC
        ).grid(row=0, column=1, padx=16, pady=(16, 8), sticky="w")

    def _pedido_form(self):
        # Container esquerda (form + itens + total + salvar)
        left = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        left.grid(row=1, column=0, padx=(16, 8), pady=(0, 16), sticky="nsew")
        left.grid_columnconfigure(0, weight=1)

        # --- Cliente ---
        box_cli = ctk.CTkFrame(left, fg_color="#FFFFFF", corner_radius=12)
        box_cli.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="ew")
        for c in range(2):
            box_cli.grid_columnconfigure(c, weight=1)

        ctk.CTkLabel(box_cli, text="Cliente", text_color=theme.COR_TEXTO,
                     font=ctk.CTkFont(family=theme.FONTE, size=13, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=10, pady=(10, 4), sticky="w")

        ctk.CTkEntry(box_cli, textvariable=self.cli_nome_var, height=34, placeholder_text="Nome").grid(
            row=1, column=0, padx=(10, 5), pady=(0, 8), sticky="ew")
        ctk.CTkEntry(box_cli, textvariable=self.cli_tel_var, height=34, placeholder_text="Telefone").grid(
            row=1, column=1, padx=(5, 10), pady=(0, 8), sticky="ew")

        # --- Endereço ---
        box_end = ctk.CTkFrame(left, fg_color="#FFFFFF", corner_radius=12)
        box_end.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        for c in range(4):
            box_end.grid_columnconfigure(c, weight=1)

        ctk.CTkLabel(box_end, text="Endereço de entrega", text_color=theme.COR_TEXTO,
                     font=ctk.CTkFont(family=theme.FONTE, size=13, weight="bold")).grid(
            row=0, column=0, columnspan=4, padx=10, pady=(10, 4), sticky="w")

        ctk.CTkEntry(box_end, textvariable=self.end_rua_var, height=34, placeholder_text="Rua / Avenida").grid(
            row=1, column=0, columnspan=3, padx=(10, 5), pady=(0, 6), sticky="ew")
        ctk.CTkEntry(box_end, textvariable=self.end_num_var, height=34, placeholder_text="Número").grid(
            row=1, column=3, padx=(5, 10), pady=(0, 6), sticky="ew")

        ctk.CTkEntry(box_end, textvariable=self.end_bairro_var, height=34, placeholder_text="Bairro").grid(
            row=2, column=0, padx=(10, 5), pady=(0, 6), sticky="ew")
        ctk.CTkEntry(box_end, textvariable=self.end_cidade_var, height=34, placeholder_text="Cidade").grid(
            row=2, column=1, padx=(5, 5), pady=(0, 6), sticky="ew")
        ctk.CTkEntry(box_end, textvariable=self.end_comp_var, height=34, placeholder_text="Complemento / Referência").grid(
            row=2, column=2, columnspan=2, padx=(5, 10), pady=(0, 6), sticky="ew")

        # --- Pedido / Config ---
        box_cfg = ctk.CTkFrame(left, fg_color="#FFFFFF", corner_radius=12)
        box_cfg.grid(row=2, column=0, padx=12, pady=(0, 8), sticky="ew")
        for c in range(4):
            box_cfg.grid_columnconfigure(c, weight=1)

        ctk.CTkLabel(box_cfg, text="Pedido", text_color=theme.COR_TEXTO,
                     font=ctk.CTkFont(family=theme.FONTE, size=13, weight="bold")).grid(
            row=0, column=0, columnspan=4, padx=10, pady=(10, 4), sticky="w")

        ctk.CTkLabel(box_cfg, text="Data", text_color=theme.COR_TEXTO).grid(row=1, column=0, padx=10, sticky="w")
        ctk.CTkEntry(box_cfg, textvariable=self.data_var, height=34, placeholder_text="AAAA-MM-DD").grid(
            row=2, column=0, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(box_cfg, text="Previsão de saída (HH:MM)", text_color=theme.COR_TEXTO).grid(row=1, column=1, padx=10, sticky="w")
        ctk.CTkEntry(box_cfg, textvariable=self.prev_saida_var, height=34, placeholder_text="Ex.: 00:30").grid(
            row=2, column=1, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(box_cfg, text="Entregador", text_color=theme.COR_TEXTO).grid(row=1, column=2, padx=10, sticky="w")
        self.combo_entregador = ctk.CTkComboBox(
            box_cfg,
            values=[f'{e["nome"]} • {e["telefone"]}' for e in self.entregadores],
            variable=self.entregador_var
        )
        self.combo_entregador.grid(row=2, column=2, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(box_cfg, text="Pagamento", text_color=theme.COR_TEXTO).grid(row=1, column=3, padx=10, sticky="w")
        self.combo_pag = ctk.CTkComboBox(box_cfg, values=["Pix", "Dinheiro", "Cartão"], variable=self.pag_var)
        self.combo_pag.grid(row=2, column=3, padx=10, pady=(0, 8), sticky="ew")

        # Status + Taxa
        ctk.CTkLabel(box_cfg, text="Status", text_color=theme.COR_TEXTO).grid(row=3, column=0, padx=10, sticky="w")
        self.combo_status = ctk.CTkComboBox(box_cfg, values=["Pendente", "Em preparo", "Em rota", "Entregue", "Cancelado"], variable=self.status_var)
        self.combo_status.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(box_cfg, text="Taxa de entrega (R$)", text_color=theme.COR_TEXTO).grid(row=3, column=1, padx=10, sticky="w")
        ctk.CTkEntry(box_cfg, textvariable=self.taxa_var, height=34).grid(row=4, column=1, padx=10, pady=(0, 10), sticky="ew")

        # Observações
        ctk.CTkLabel(box_cfg, text="Observações", text_color=theme.COR_TEXTO).grid(row=3, column=2, padx=10, sticky="w")
        self.obs_widget = ctk.CTkTextbox(box_cfg, height=60)
        self.obs_widget.grid(row=4, column=2, columnspan=2, padx=10, pady=(0, 10), sticky="ew")

        # --- Itens ---
        box_it = ctk.CTkFrame(left, fg_color="#FFFFFF", corner_radius=12)
        box_it.grid(row=3, column=0, padx=12, pady=(0, 8), sticky="nsew")
        box_it.grid_columnconfigure(0, weight=1)
        box_it.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(box_it, text="Itens do pedido", text_color=theme.COR_TEXTO,
                     font=ctk.CTkFont(family=theme.FONTE, size=13, weight="bold")).grid(
            row=0, column=0, columnspan=3, padx=10, pady=(10, 4), sticky="w")

        linha_add = ctk.CTkFrame(box_it, fg_color="transparent")
        linha_add.grid(row=1, column=0, padx=10, pady=(0, 6), sticky="ew")
        linha_add.grid_columnconfigure(0, weight=1)

        self.combo_prod = ctk.CTkComboBox(
            linha_add,
            values=[f'{p["nome"]} • {theme.fmt_dinheiro(p["preco"])}' for p in self.produtos],
            variable=self.produto_var
        )
        self.combo_prod.grid(row=0, column=0, sticky="ew")

        self.entry_qtd = ctk.CTkEntry(linha_add, textvariable=self.qtd_var, width=80, placeholder_text="Qtd")
        self.entry_qtd.grid(row=0, column=1, padx=(8, 8))

        ctk.CTkButton(linha_add, text="Adicionar", width=100, command=self._adicionar_item).grid(row=0, column=2)

        # Lista de itens
        self.lista_itens = ctk.CTkScrollableFrame(box_it, fg_color="transparent", height=160)
        self.lista_itens.grid(row=2, column=0, padx=10, pady=(4, 10), sticky="nsew")

        # Total + botões
        linha_total = ctk.CTkFrame(left, fg_color="transparent")
        linha_total.grid(row=4, column=0, padx=12, pady=(0, 12), sticky="ew")
        linha_total.grid_columnconfigure(0, weight=1)
        linha_total.grid_columnconfigure(1, weight=1)

        self.lbl_total = ctk.CTkLabel(
            linha_total, text="Total: R$ 0,00",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO
        )
        self.lbl_total.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(linha_total, text="Salvar pedido", fg_color="#FFFFFF",
                      hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
                      command=self._salvar_pedido).grid(row=0, column=1, padx=(8, 0), sticky="e")

    def _lista_dia(self):
        # Container direita (entregas do dia)
        right = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        right.grid(row=1, column=1, padx=(8, 16), pady=(0, 16), sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            right, text="Entregas do dia",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        box_tab = ctk.CTkFrame(right, fg_color="#FFFFFF", corner_radius=12)
        box_tab.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="nsew")
        box_tab.grid_rowconfigure(0, weight=1)
        box_tab.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            box_tab,
            columns=("hora", "cliente", "endereco", "pagamento", "valor", "status", "entregador"),
            show="headings"
        )
        self.tree.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self.tree.heading("hora", text="Previsão")
        self.tree.heading("cliente", text="Cliente")
        self.tree.heading("endereco", text="Endereço")
        self.tree.heading("pagamento", text="Pagamento")
        self.tree.heading("valor", text="Total")
        self.tree.heading("status", text="Status")
        self.tree.heading("entregador", text="Entregador")

        self.tree.column("hora", width=90, anchor="center")
        self.tree.column("cliente", width=160, anchor="w")
        self.tree.column("endereco", width=260, anchor="w")
        self.tree.column("pagamento", width=90, anchor="center")
        self.tree.column("valor", width=90, anchor="e")
        self.tree.column("status", width=110, anchor="center")
        self.tree.column("entregador", width=140, anchor="w")

        scroll = ttk.Scrollbar(box_tab, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
        self.tree.configure(yscrollcommand=scroll.set)

        # Duplo clique para editar
        self.tree.bind("<Double-1>", lambda e: self._editar_pedido_sel())

        # Remover
        ctk.CTkButton(
            right, text="Remover pedido selecionado", height=36,
            fg_color="#FFFFFF", hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
            command=self._remover_pedido_sel
        ).grid(row=2, column=0, padx=12, pady=(0, 12), sticky="ew")

    # ---------- MOCK ----------
    def _mock_produtos(self):
        return [
            {"id": 1, "nome": "Açaí 500ml", "preco": 18.00},
            {"id": 2, "nome": "Copo 300ml (Chocolate)", "preco": 12.00},
            {"id": 3, "nome": "Picolé (Limão)", "preco": 5.00},
            {"id": 4, "nome": "Casquinha", "preco": 7.50},
        ]

    def _mock_entregadores(self):
        return [
            {"id": 1, "nome": "Diego Motoboy", "telefone": "(91) 99999-1010"},
            {"id": 2, "nome": "Larissa Entregas", "telefone": "(91) 98888-2020"},
        ]

    # ---------- Itens ----------
    def _adicionar_item(self):
        txt = self.combo_prod.get().strip()
        if not txt:
            messagebox.showwarning("Itens", "Selecione um produto.")
            return
        # resolve produto por nome antes do " • "
        nome = txt.split("•")[0].strip()
        prod = next((p for p in self.produtos if p["nome"] == nome), None)
        if not prod:
            messagebox.showwarning("Itens", "Produto inválido.")
            return
        try:
            qtd = int(self.qtd_var.get())
            if qtd <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Itens", "Quantidade inválida.")
            return

        existente = next((i for i in self.carrinho_itens if i["id"] == prod["id"]), None)
        if existente:
            existente["qtd"] += qtd
        else:
            self.carrinho_itens.append({
                "id": prod["id"], "nome": prod["nome"], "preco": prod["preco"], "qtd": qtd
            })

        self._render_itens()

    def _remover_item(self, pid):
        self.carrinho_itens = [i for i in self.carrinho_itens if i["id"] != pid]
        self._render_itens()

    def _render_itens(self):
        for w in self.lista_itens.winfo_children():
            w.destroy()

        total = 0.0
        for item in self.carrinho_itens:
            total += item["preco"] * item["qtd"]
            linha = ctk.CTkFrame(self.lista_itens, fg_color="#FFFFFF", corner_radius=8)
            linha.pack(fill="x", pady=4)

            ctk.CTkLabel(linha, text=item["nome"],
                         font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
                         text_color=theme.COR_TEXTO).pack(anchor="w", padx=10, pady=(6, 0))

            ctk.CTkLabel(linha, text=f'{item["qtd"]} x {theme.fmt_dinheiro(item["preco"])}',
                         font=ctk.CTkFont(family=theme.FONTE, size=12),
                         text_color=theme.COR_TEXTO_SEC).pack(anchor="w", padx=10, pady=(0, 6))

            ctk.CTkButton(linha, text="Remover", width=90,
                          command=lambda pid=item["id"]: self._remover_item(pid)).pack(anchor="e", padx=8, pady=(0, 8))

        # Aplica taxa de entrega
        try:
            taxa = float(self.taxa_var.get().replace(",", "."))
        except ValueError:
            taxa = 0.0
        total += taxa
        self.lbl_total.configure(text=f"Total: {theme.fmt_dinheiro(total)}")

    def _get_obs(self):
        return self.obs_widget.get("1.0", "end").strip()

    def _set_obs(self, txt):
        self.obs_widget.delete("1.0", "end")
        if txt:
            self.obs_widget.insert("1.0", txt)

    # ---------- Pedidos ----------
    def _validar(self):
        if not self.cli_nome_var.get().strip():
            return False, "Informe o nome do cliente."
        if not self.cli_tel_var.get().strip():
            return False, "Informe o telefone do cliente."
        if not self.end_rua_var.get().strip() or not self.end_bairro_var.get().strip():
            return False, "Informe pelo menos Rua e Bairro."
        if not self.carrinho_itens:
            return False, "Adicione pelo menos 1 item ao pedido."
        try:
            dt.date.fromisoformat(self.data_var.get().strip())
        except ValueError:
            return False, "Data inválida (use AAAA-MM-DD)."
        # Previsão HH:MM simples (opcional)
        prev = self.prev_saida_var.get().strip()
        if prev:
            if not self._parse_hora(prev):
                return False, "Previsão de saída inválida (use HH:MM)."
        return True, ""

    def _parse_hora(self, s):
        try:
            h, m = s.split(":")
            h, m = int(h), int(m)
            if 0 <= h <= 23 and 0 <= m <= 59:
                return h * 60 + m
        except Exception:
            pass
        return None

    def _calcular_total(self, itens, taxa):
        subtotal = sum(i["preco"] * i["qtd"] for i in itens)
        return subtotal + taxa

    def _salvar_pedido(self):
        ok, msg = self._validar()
        if not ok:
            messagebox.showwarning("Validação", msg)
            return

        try:
            taxa = float(self.taxa_var.get().replace(",", "."))
        except ValueError:
            taxa = 0.0

        total = self._calcular_total(self.carrinho_itens, taxa)

        ent = self._resolver_entregador(self.combo_entregador.get().strip())

        pedido = {
            "id": self._pedido_em_edicao_id or self._prox_id(),
            "data": dt.date.fromisoformat(self.data_var.get().strip()),
            "prev": self.prev_saida_var.get().strip(),
            "cliente": {
                "nome": self.cli_nome_var.get().strip(),
                "telefone": self.cli_tel_var.get().strip()
            },
            "endereco": {
                "rua": self.end_rua_var.get().strip(),
                "numero": self.end_num_var.get().strip(),
                "bairro": self.end_bairro_var.get().strip(),
                "cidade": self.end_cidade_var.get().strip(),
                "comp": self.end_comp_var.get().strip()
            },
            "itens": [dict(i) for i in self.carrinho_itens],
            "taxa": taxa,
            "total": total,
            "pagamento": self.combo_pag.get().strip(),
            "status": self.combo_status.get().strip(),
            "entregador_id": ent["id"] if ent else None,
            "entregador_nome": ent["nome"] if ent else "",
            "obs": self._get_obs()
        }

        if self._pedido_em_edicao_id is None:
            self.entregas.append(pedido)
        else:
            for i, p in enumerate(self.entregas):
                if p["id"] == self._pedido_em_edicao_id:
                    self.entregas[i] = pedido
                    break

        self._limpar_form()
        self._render_entregas_dia()
        messagebox.showinfo("Delivery", "Pedido salvo com sucesso!")

    def _resolver_entregador(self, txt):
        if not txt:
            return None
        nome = txt.split("•")[0].strip()
        return next((e for e in self.entregadores if e["nome"] == nome), None)

    def _prox_id(self):
        return max([p["id"] for p in self.entregas], default=0) + 1

    def _limpar_form(self):
        self._pedido_em_edicao_id = None
        # Mantém data e taxa; limpa o restante
        self.cli_nome_var.set("")
        self.cli_tel_var.set("")
        self.end_rua_var.set("")
        self.end_num_var.set("")
        self.end_bairro_var.set("")
        # cidade mantém
        self.end_comp_var.set("")
        self.prev_saida_var.set("00:30")
        self.pag_var.set("Pix")
        self.status_var.set("Pendente")
        self.carrinho_itens = []
        self._set_obs("")
        self._render_itens()

    def _render_entregas_dia(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        try:
            dia = dt.date.fromisoformat(self.data_var.get().strip())
        except ValueError:
            dia = dt.date.today()

        do_dia = [p for p in self.entregas if p["data"] == dia]

        # Ordena por previsão
        def key_prev(p):
            m = self._parse_hora(p["prev"]) if p["prev"] else 9999
            return m
        do_dia.sort(key=key_prev)

        for p in do_dia:
            end = f'{p["endereco"]["rua"]}, {p["endereco"]["numero"]} - {p["endereco"]["bairro"]}'
            self.tree.insert(
                "", "end",
                values=(
                    p["prev"],
                    f'{p["cliente"]["nome"]}',
                    end,
                    p["pagamento"],
                    theme.fmt_dinheiro(p["total"]),
                    p["status"],
                    p["entregador_nome"]
                ),
                tags=(f'pd-{p["id"]}',)
            )

    def _pedido_por_tag(self, tag):
        if not tag.startswith("pd-"):
            return None
        pid = int(tag.split("-")[1])
        return next((x for x in self.entregas if x["id"] == pid), None)

    def _editar_pedido_sel(self):
        sel = self.tree.selection()
        if not sel:
            return
        tags = self.tree.item(sel[0], "tags")
        if not tags:
            return
        p = self._pedido_por_tag(tags[0])
        if not p:
            return

        # Carrega form
        self._pedido_em_edicao_id = p["id"]
        self.data_var.set(p["data"].strftime("%Y-%m-%d"))
        self.prev_saida_var.set(p["prev"])
        self.cli_nome_var.set(p["cliente"]["nome"])
        self.cli_tel_var.set(p["cliente"]["telefone"])
        self.end_rua_var.set(p["endereco"]["rua"])
        self.end_num_var.set(p["endereco"]["numero"])
        self.end_bairro_var.set(p["endereco"]["bairro"])
        self.end_cidade_var.set(p["endereco"]["cidade"])
        self.end_comp_var.set(p["endereco"]["comp"])
        self.pag_var.set(p["pagamento"])
        self.status_var.set(p["status"])
        self.taxa_var.set(f'{p["taxa"]:.2f}')

        # Entregador (recompõe com telefone se existir)
        if p["entregador_nome"]:
            ent = next((e for e in self.entregadores if e["nome"] == p["entregador_nome"]), None)
            if ent:
                self.combo_entregador.set(f'{ent["nome"]} • {ent["telefone"]}')
            else:
                self.combo_entregador.set(p["entregador_nome"])

        self._set_obs(p.get("obs", ""))

        # Itens
        self.carrinho_itens = [dict(i) for i in p["itens"]]
        self._render_itens()
        messagebox.showinfo("Editar", "Pedido carregado para edição.")

    def _remover_pedido_sel(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Remover", "Selecione um pedido.")
            return
        tags = self.tree.item(sel[0], "tags")
        if not tags:
            return
        p = self._pedido_por_tag(tags[0])
        if not p:
            return
        if not messagebox.askyesno("Confirmar", "Deseja remover este pedido?"):
            return
        self.entregas = [x for x in self.entregas if x["id"] != p["id"]]
        self._render_entregas_dia()
        if self._pedido_em_edicao_id == p["id"]:
            self._limpar_form()
        messagebox.showinfo("Removido", "Pedido removido.")


# ===========================================================
# WRAPPER: ABA "AGENDAMENTOS" + "DELIVERY"
# ===========================================================
class PaginaOperacaoCarrinhos(ctk.CTkFrame):
    """
    Página com abas:
      - Agendamentos de carrinhos
      - Delivery
    """
    def __init__(self, master):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        # Título geral
        ctk.CTkLabel(
            self,
            text="Operação • Carrinhos de Picolé",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=30, pady=(14, 6), sticky="w")

        ctk.CTkLabel(
            self,
            text="Agende saídas de carrinhos e gerencie pedidos de delivery.",
            font=ctk.CTkFont(family=theme.FONTE, size=13),
            text_color=theme.COR_TEXTO_SEC
        ).grid(row=1, column=0, padx=30, pady=(0, 10), sticky="w")

        # TabView
        tabs = ctk.CTkTabview(self)
        tabs.grid(row=2, column=0, padx=24, pady=(0, 20), sticky="nsew")

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Abas
        tab_ag = tabs.add("Agendamentos")
        tab_dl = tabs.add("Delivery")

        # Instancia as páginas específicas dentro de cada aba
        self.pg_ag = PaginaAgendamentoCarrinhos(tab_ag)
        self.pg_ag.pack(fill="both", expand=True, padx=6, pady=6)

        self.pg_dl = PaginaDelivery(tab_dl)
        self.pg_dl.pack(fill="both", expand=True, padx=6, pady=6)