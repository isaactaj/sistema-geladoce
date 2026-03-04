# -*- coding: utf-8 -*-
"""
Página com abas:
  - Agendamentos de carrinhos de picolé
  - Agenda do dia
  - Delivery

Requisitos: customtkinter, tkinter
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
import datetime as dt

from app.config import theme


# ===========================================================
# ABA 1: AGENDAMENTOS
# ===========================================================
class PaginaAgendamentoCarrinhos(ctk.CTkFrame):
    """
    Tela de agendamento de carrinhos de picolé.

    - Esquerda: filtros + lista de carrinhos
    - Direita: formulário de agendamento
    """

    def __init__(self, master, sistema=None, on_open_agenda=None, on_agenda_changed=None):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        self.sistema = sistema
        self.on_open_agenda = on_open_agenda
        self.on_agenda_changed = on_agenda_changed

        self.grid_columnconfigure(0, weight=3, uniform="ag_cols")
        self.grid_columnconfigure(1, weight=2, uniform="ag_cols")
        self.grid_rowconfigure(0, weight=1)

        # --------- Estado ---------
        self.busca_carrinho_var = ctk.StringVar(value="")
        self.status_carrinho_var = ctk.StringVar(value="Todos")

        hoje = dt.date.today().strftime("%Y-%m-%d")
        self.data_var = ctk.StringVar(value=hoje)
        self.hora_ini_var = ctk.StringVar(value="08:00")
        self.hora_fim_var = ctk.StringVar(value="12:00")
        self.local_var = ctk.StringVar(value="")
        self.status_ag_var = ctk.StringVar(value="Agendado")
        self.motorista_var = ctk.StringVar(value="")
        self.observacoes_widget = None

        self._agendamento_em_edicao_id = None

        # Dados operacionais
        self.carrinhos = []
        self.funcionarios = []
        self.agendamentos = []

        self.tree_carrinhos = None
        self._frame_tree_carrinhos = None

        self._carregar_dados_operacionais()

        self._painel_carrinhos_ui()
        self._form_agendamento_ui()

        self._atualizar_combos_operacionais()
        self._render_lista_carrinhos()

    # -------------------- SISTEMA --------------------
    def _obter_metodo_sistema(self, *nomes):
        if not self.sistema:
            return None
        for nome in nomes:
            metodo = getattr(self.sistema, nome, None)
            if callable(metodo):
                return metodo
        return None

    def _listar_carrinhos_sistema(self):
        metodo = self._obter_metodo_sistema("listar_carrinhos")
        if not metodo:
            return False, []

        try:
            itens = metodo()
        except TypeError:
            try:
                itens = metodo(termo="")
            except Exception:
                return True, []
        except Exception:
            return True, []

        if not isinstance(itens, list):
            return True, []

        normalizados = []
        for c in itens:
            if not isinstance(c, dict):
                continue

            try:
                cid = int(c.get("id"))
            except Exception:
                continue

            normalizados.append({
                "id": cid,
                "id_externo": str(
                    c.get("id_externo")
                    or c.get("codigo")
                    or c.get("identificacao")
                    or f"CAR-{cid:02d}"
                ),
                "nome": str(c.get("nome") or f"Carrinho {cid}"),
                "capacidade": int(c.get("capacidade", 0) or 0),
                "status": str(c.get("status") or "Disponível"),
            })

        return True, normalizados

    def _listar_funcionarios_sistema(self):
        metodo = self._obter_metodo_sistema("listar_funcionarios")
        if not metodo:
            return False, []

        try:
            itens = metodo()
        except TypeError:
            try:
                itens = metodo(termo="")
            except Exception:
                return True, []
        except Exception:
            return True, []

        if not isinstance(itens, list):
            return True, []

        normalizados = []
        for f in itens:
            if not isinstance(f, dict):
                continue

            try:
                fid = int(f.get("id"))
            except Exception:
                continue

            normalizados.append({
                "id": fid,
                "nome": str(f.get("nome") or f"Funcionário {fid}"),
                "telefone": str(f.get("telefone") or ""),
                "cargo": str(f.get("cargo") or ""),
            })

        return True, normalizados

    def _parse_data_agendamento(self, valor):
        if isinstance(valor, dt.date):
            return valor

        if isinstance(valor, str):
            txt = valor.strip()
            for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                try:
                    return dt.datetime.strptime(txt, fmt).date()
                except ValueError:
                    pass

        return None

    def _listar_agendamentos_sistema(self):
        metodo = self._obter_metodo_sistema("listar_agendamentos")
        if not metodo:
            return False, []

        try:
            itens = metodo()
        except TypeError:
            try:
                itens = metodo(data=self.data_var.get().strip())
            except Exception:
                return True, []
        except Exception:
            return True, []

        if not isinstance(itens, list):
            return True, []

        normalizados = []
        for a in itens:
            if not isinstance(a, dict):
                continue

            data_obj = self._parse_data_agendamento(
                a.get("data") or a.get("data_agendamento")
            )
            if not data_obj:
                continue

            inicio = str(a.get("inicio") or a.get("hora_inicio") or "08:00")
            fim = str(a.get("fim") or a.get("hora_fim") or "12:00")

            inicio_min = self._parse_hora(inicio)
            fim_min = self._parse_hora(fim)
            if inicio_min is None or fim_min is None:
                continue

            try:
                aid = int(a.get("id"))
            except Exception:
                continue

            try:
                carrinho_id = int(a.get("carrinho_id"))
            except Exception:
                carrinho_id = None

            try:
                motorista_id = int(
                    a.get("motorista_id")
                    or a.get("funcionario_id")
                    or a.get("responsavel_id")
                )
            except Exception:
                motorista_id = None

            carrinho = next((c for c in self.carrinhos if c["id"] == carrinho_id), None)
            funcionario = next((f for f in self.funcionarios if f["id"] == motorista_id), None)

            normalizados.append({
                "id": aid,
                "data": data_obj,
                "inicio": inicio,
                "fim": fim,
                "inicio_min": inicio_min,
                "fim_min": fim_min,
                "carrinho_id": carrinho_id,
                "carrinho_nome": str(
                    a.get("carrinho_nome")
                    or (carrinho["nome"] if carrinho else "")
                ),
                "carrinho_id_externo": str(
                    a.get("carrinho_id_externo")
                    or a.get("carrinho_codigo")
                    or (carrinho["id_externo"] if carrinho else "")
                ),
                "motorista_id": motorista_id,
                "motorista_nome": str(
                    a.get("motorista_nome")
                    or a.get("funcionario_nome")
                    or a.get("responsavel_nome")
                    or (funcionario["nome"] if funcionario else "")
                ),
                "local": str(a.get("local") or ""),
                "status": str(a.get("status") or "Agendado"),
                "obs": str(a.get("obs") or a.get("observacao") or ""),
            })

        return True, normalizados

    def _carregar_dados_operacionais(self):
        suportado_carrinhos, carrinhos = self._listar_carrinhos_sistema()
        if suportado_carrinhos or not self.carrinhos:
            self.carrinhos = carrinhos

        suportado_func, funcs = self._listar_funcionarios_sistema()
        if suportado_func or not self.funcionarios:
            self.funcionarios = funcs

        suportado_ag, ags = self._listar_agendamentos_sistema()
        if suportado_ag or not self.agendamentos:
            self.agendamentos = ags

    def _atualizar_combos_operacionais(self):
        if hasattr(self, "combo_carrinho"):
            atual = self.combo_carrinho.get().strip()
            opcoes = [f'{c["nome"]} ({c["id_externo"]})' for c in self.carrinhos] or ["(nenhum carrinho)"]
            self.combo_carrinho.configure(values=opcoes)
            self.combo_carrinho.set(atual if atual in opcoes else opcoes[0])

        if hasattr(self, "combo_motorista"):
            atual = self.combo_motorista.get().strip()
            opcoes = [f'{f["nome"]} • {f["telefone"]}' for f in self.funcionarios] or ["(nenhum responsável)"]
            self.combo_motorista.configure(values=opcoes)
            self.combo_motorista.set(atual if atual in opcoes else opcoes[0])

    def _salvar_agendamento_no_sistema(self, novo):
        metodo = self._obter_metodo_sistema("salvar_agendamento")
        if not metodo:
            return False

        data_txt = novo["data"].strftime("%Y-%m-%d")

        try:
            metodo(
                data=data_txt,
                hora_inicio=novo["inicio"],
                hora_fim=novo["fim"],
                carrinho_id=novo["carrinho_id"],
                funcionario_id=novo["motorista_id"],
                local=novo["local"],
                status=novo["status"],
                observacao=novo["obs"],
                agendamento_id=self._agendamento_em_edicao_id,
            )
            return True
        except TypeError:
            try:
                metodo(
                    data=data_txt,
                    inicio=novo["inicio"],
                    fim=novo["fim"],
                    carrinho_id=novo["carrinho_id"],
                    motorista_id=novo["motorista_id"],
                    local=novo["local"],
                    status=novo["status"],
                    obs=novo["obs"],
                    agendamento_id=self._agendamento_em_edicao_id,
                )
                return True
            except Exception:
                return False
        except Exception:
            return False

    def _remover_agendamento_do_sistema(self, aid):
        metodo = self._obter_metodo_sistema("excluir_agendamento", "remover_agendamento")
        if not metodo:
            return False

        try:
            metodo(aid)
            return True
        except TypeError:
            try:
                metodo(agendamento_id=aid)
                return True
            except Exception:
                return False
        except Exception:
            return False

    # -------------------- PAINEL ESQ --------------------
    def _painel_carrinhos_ui(self):
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=0, column=0, padx=(30, 12), pady=(10, 20), sticky="nsew")
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(2, weight=1)

        filtros = ctk.CTkFrame(box, fg_color="transparent")
        filtros.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="ew")
        filtros.grid_columnconfigure(0, weight=1)
        filtros.grid_columnconfigure(1, weight=0)

        self.entry_busca_car = ctk.CTkEntry(
            filtros,
            textvariable=self.busca_carrinho_var,
            placeholder_text="🔎 Buscar carrinho por nome/ID…",
            height=36,
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        )
        self.entry_busca_car.grid(row=0, column=0, sticky="ew")
        self.entry_busca_car.bind("<KeyRelease>", lambda e: self._render_lista_carrinhos())

        self.combo_status_car = ctk.CTkComboBox(
            filtros,
            values=["Todos", "Disponível", "Em rota", "Manutenção"],
            width=170,
            command=lambda _: self._render_lista_carrinhos(),
            fg_color=theme.COR_BOTAO,
            button_color=theme.COR_SELECIONADO,
            button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_BOTAO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        )
        self.combo_status_car.set("Todos")
        self.combo_status_car.grid(row=0, column=1, padx=(10, 0))

        ctk.CTkLabel(
            box,
            text="Carrinhos",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=1, column=0, padx=12, pady=(0, 4), sticky="w")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Geladoce.Treeview",
            font=(theme.FONTE, 11),
            rowheight=34,
            background=theme.COR_BOTAO,
            fieldbackground=theme.COR_BOTAO,
            foreground=theme.COR_TEXTO,
            borderwidth=0,
            relief="flat"
        )
        style.configure(
            "Geladoce.Treeview.Heading",
            font=(theme.FONTE, 11, "bold"),
            background=theme.COR_PAINEL,
            foreground=theme.COR_TEXTO,
            borderwidth=0,
            relief="flat"
        )
        style.map(
            "Geladoce.Treeview",
            background=[("selected", theme.COR_SELECIONADO)],
            foreground=[("selected", theme.COR_TEXTO)]
        )

        self._frame_tree_carrinhos = ctk.CTkFrame(box, fg_color=theme.COR_BOTAO, corner_radius=12)
        self._frame_tree_carrinhos.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self._frame_tree_carrinhos.grid_rowconfigure(0, weight=1)
        self._frame_tree_carrinhos.grid_columnconfigure(0, weight=1)
        self._frame_tree_carrinhos.bind("<Configure>", self._ajustar_colunas_tree_carrinhos)

        self.tree_carrinhos = ttk.Treeview(
            self._frame_tree_carrinhos,
            columns=("status", "capacidade"),
            show="tree headings",
            style="Geladoce.Treeview"
        )
        self.tree_carrinhos.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)

        self.tree_carrinhos.heading("#0", text="Identificação", anchor="w")
        self.tree_carrinhos.heading("status", text="Status", anchor="w")
        self.tree_carrinhos.heading("capacidade", text="Capacidade", anchor="w")

        scroll_y = ttk.Scrollbar(self._frame_tree_carrinhos, orient="vertical", command=self.tree_carrinhos.yview)
        scroll_y.grid(row=0, column=1, sticky="ns", padx=(8, 8), pady=8)
        self.tree_carrinhos.configure(yscrollcommand=scroll_y.set)

        self.tree_carrinhos.bind("<Double-1>", lambda e: self._usar_carrinho_selecionado())

        self.tree_carrinhos.tag_configure("Disponível", foreground=theme.COR_SUCESSO)
        self.tree_carrinhos.tag_configure("Em rota", foreground="#EF6C00")
        self.tree_carrinhos.tag_configure("Manutenção", foreground=theme.COR_TEXTO_SEC)

    # -------------------- FORMULÁRIO --------------------
    def _form_agendamento_ui(self):
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=0, column=1, padx=(12, 30), pady=(10, 24), sticky="nsew")

        box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            box,
            text="Novo agendamento",
            font=ctk.CTkFont(family=theme.FONTE, size=16, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=16, pady=(16, 10), sticky="w")

        linha_data = ctk.CTkFrame(box, fg_color="transparent")
        linha_data.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")
        linha_data.grid_columnconfigure(1, weight=1)

        btn_prev = ctk.CTkButton(
            linha_data,
            text="←",
            width=38,
            height=34,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=lambda: self._navegar_data(-1)
        )
        btn_prev.grid(row=0, column=0, padx=(0, 6))

        entry_data = ctk.CTkEntry(
            linha_data,
            textvariable=self.data_var,
            height=34,
            placeholder_text="AAAA-MM-DD",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        )
        entry_data.grid(row=0, column=1, sticky="ew")

        btn_next = ctk.CTkButton(
            linha_data,
            text="→",
            width=38,
            height=34,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=lambda: self._navegar_data(1)
        )
        btn_next.grid(row=0, column=2, padx=(6, 0))

        btn_hoje = ctk.CTkButton(
            linha_data,
            text="Hoje",
            width=70,
            height=34,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=lambda: self._set_data(dt.date.today())
        )
        btn_hoje.grid(row=0, column=3, padx=(8, 0))

        btn_amanha = ctk.CTkButton(
            linha_data,
            text="Amanhã",
            width=80,
            height=34,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=lambda: self._set_data(dt.date.today() + dt.timedelta(days=1))
        )
        btn_amanha.grid(row=0, column=4, padx=(6, 0))

        form = ctk.CTkFrame(box, fg_color=theme.COR_BOTAO, corner_radius=12)
        form.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="ew")
        form.grid_columnconfigure(0, weight=1, uniform="form_ag_2x2")
        form.grid_columnconfigure(1, weight=1, uniform="form_ag_2x2")

        ctk.CTkLabel(form, text="Início (HH:MM)", text_color=theme.COR_TEXTO).grid(row=0, column=0, padx=10, pady=(12, 4), sticky="w")
        ctk.CTkLabel(form, text="Fim (HH:MM)", text_color=theme.COR_TEXTO).grid(row=0, column=1, padx=10, pady=(12, 4), sticky="w")

        combo_ini = ctk.CTkComboBox(
            form,
            values=self._horarios_padrao(),
            variable=self.hora_ini_var,
            height=34,
            fg_color=theme.COR_BOTAO,
            button_color=theme.COR_SELECIONADO,
            button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_BOTAO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        )
        combo_ini.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="ew")

        combo_fim = ctk.CTkComboBox(
            form,
            values=self._horarios_padrao(),
            variable=self.hora_fim_var,
            height=34,
            fg_color=theme.COR_BOTAO,
            button_color=theme.COR_SELECIONADO,
            button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_BOTAO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        )
        combo_fim.grid(row=1, column=1, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(form, text="Carrinho", text_color=theme.COR_TEXTO).grid(row=2, column=0, padx=10, pady=(6, 4), sticky="w")
        ctk.CTkLabel(form, text="Responsável", text_color=theme.COR_TEXTO).grid(row=2, column=1, padx=10, pady=(6, 4), sticky="w")

        self.combo_carrinho = ctk.CTkComboBox(
            form,
            values=["(nenhum carrinho)"],
            height=34,
            fg_color=theme.COR_BOTAO,
            button_color=theme.COR_SELECIONADO,
            button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_BOTAO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        )
        self.combo_carrinho.grid(row=3, column=0, padx=10, pady=(0, 8), sticky="ew")

        self.combo_motorista = ctk.CTkComboBox(
            form,
            values=["(nenhum responsável)"],
            variable=self.motorista_var,
            height=34,
            fg_color=theme.COR_BOTAO,
            button_color=theme.COR_SELECIONADO,
            button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_BOTAO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        )
        self.combo_motorista.grid(row=3, column=1, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(form, text="Local / Evento", text_color=theme.COR_TEXTO).grid(row=4, column=0, padx=10, pady=(6, 4), sticky="w")
        ctk.CTkLabel(form, text="Status", text_color=theme.COR_TEXTO).grid(row=4, column=1, padx=10, pady=(6, 4), sticky="w")

        entry_local = ctk.CTkEntry(
            form,
            textvariable=self.local_var,
            height=34,
            placeholder_text="Ex.: Escola Alfa, Praça X, Bairro Y…",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        )
        entry_local.grid(row=5, column=0, padx=10, pady=(0, 8), sticky="ew")

        self.combo_status_ag = ctk.CTkComboBox(
            form,
            values=["Agendado", "Confirmado", "Cancelado"],
            height=34,
            fg_color=theme.COR_BOTAO,
            button_color=theme.COR_SELECIONADO,
            button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_BOTAO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        )
        self.combo_status_ag.set("Agendado")
        self.combo_status_ag.grid(row=5, column=1, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(form, text="Observações", text_color=theme.COR_TEXTO).grid(row=6, column=0, columnspan=2, padx=10, pady=(6, 4), sticky="w")

        self.observacoes_widget = ctk.CTkTextbox(
            form,
            height=60,
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        )
        self.observacoes_widget.grid(row=7, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")

        # Botões
        linha_btns = ctk.CTkFrame(box, fg_color="transparent")
        linha_btns.grid(row=3, column=0, padx=16, pady=(12, 24), sticky="ew")
        linha_btns.grid_columnconfigure(0, weight=1)
        linha_btns.grid_columnconfigure(1, weight=1)

        self.btn_salvar = ctk.CTkButton(
            linha_btns,
            text="Salvar agendamento",
            height=38,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._salvar_agendamento
        )
        self.btn_salvar.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        btn_limpar = ctk.CTkButton(
            linha_btns,
            text="Limpar",
            height=38,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._limpar_form
        )
        btn_limpar.grid(row=0, column=1, padx=(6, 0), sticky="ew")

        # Botão para ir à aba da agenda
        ctk.CTkButton(
            box,
            text="Ir para aba Agenda do dia",
            height=38,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._abrir_aba_agenda
        ).grid(row=4, column=0, padx=16, pady=(0, 16), sticky="ew")

    # -------------------- AJUSTES DINÂMICOS TREEVIEWS --------------------
    def _ajustar_colunas_tree_carrinhos(self, event=None):
        if not self.tree_carrinhos or not self._frame_tree_carrinhos:
            return

        largura = max(self._frame_tree_carrinhos.winfo_width() - 28, 220)
        col0 = int(largura * 0.52)
        col1 = int(largura * 0.26)
        col2 = max(largura - col0 - col1, 80)

        self.tree_carrinhos.column("#0", width=col0, anchor="w")
        self.tree_carrinhos.column("status", width=col1, anchor="w")
        self.tree_carrinhos.column("capacidade", width=col2, anchor="w")

    # -------------------- LISTA DE CARRINHOS --------------------
    def _render_lista_carrinhos(self):
        if not self.tree_carrinhos:
            return

        self._carregar_dados_operacionais()
        self._atualizar_combos_operacionais()

        for item in self.tree_carrinhos.get_children():
            self.tree_carrinhos.delete(item)

        termo = self.busca_carrinho_var.get().strip().lower()
        status_filtro = self.combo_status_car.get().strip() if self.combo_status_car else "Todos"

        for carrinho in self.carrinhos:
            if status_filtro != "Todos" and carrinho["status"] != status_filtro:
                continue

            texto_busca = f'{carrinho["nome"]} {carrinho["id_externo"]}'.lower()
            if termo and termo not in texto_busca:
                continue

            self.tree_carrinhos.insert(
                "",
                "end",
                text=f'{carrinho["nome"]} ({carrinho["id_externo"]})',
                values=(carrinho["status"], carrinho["capacidade"]),
                tags=(carrinho["status"], f'id-{carrinho["id"]}')
            )

    def _usar_carrinho_selecionado(self):
        sel = self.tree_carrinhos.selection()
        if not sel:
            return

        tags = self.tree_carrinhos.item(sel[0], "tags")
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

        self.combo_carrinho.set(f'{car["nome"]} ({car["id_externo"]})')
        if self.funcionarios:
            self.combo_motorista.set(f'{self.funcionarios[0]["nome"]} • {self.funcionarios[0]["telefone"]}')

    def _abrir_aba_agenda(self):
        if callable(self.on_open_agenda):
            self.on_open_agenda()

    def _notificar_agenda(self):
        if callable(self.on_agenda_changed):
            self.on_agenda_changed()

    # -------------------- FORMULÁRIO --------------------
    def _set_data(self, date_obj: dt.date):
        self.data_var.set(date_obj.strftime("%Y-%m-%d"))
        self._notificar_agenda()

    def _navegar_data(self, delta_days: int):
        try:
            d = dt.date.fromisoformat(self.data_var.get())
        except ValueError:
            d = dt.date.today()
        self._set_data(d + dt.timedelta(days=delta_days))

    def _horarios_padrao(self):
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
            h = int(h)
            m = int(m)
            if 0 <= h <= 23 and 0 <= m <= 59:
                return h * 60 + m
        except Exception:
            return None
        return None

    def _validar_inputs(self):
        try:
            dt.date.fromisoformat(self.data_var.get().strip())
        except ValueError:
            return False, "Data inválida. Use o formato AAAA-MM-DD."

        ini = self._parse_hora(self.hora_ini_var.get().strip())
        fim = self._parse_hora(self.hora_fim_var.get().strip())
        if ini is None or fim is None:
            return False, "Horários inválidos. Use HH:MM (ex.: 08:00)."
        if fim <= ini:
            return False, "Hora de fim deve ser maior que a de início."

        carrinho_txt = self.combo_carrinho.get().strip()
        if not carrinho_txt or carrinho_txt == "(nenhum carrinho)":
            return False, "Selecione um carrinho."

        carrinho = self._resolver_carrinho_por_texto(carrinho_txt)
        if not carrinho:
            return False, "Carrinho selecionado não encontrado."

        motorista_txt = self.combo_motorista.get().strip()
        if not motorista_txt or motorista_txt == "(nenhum responsável)":
            return False, "Selecione um responsável."

        mot = self._resolver_motorista_por_texto(motorista_txt)
        if not mot:
            return False, "Responsável selecionado não encontrado."

        if not self.local_var.get().strip():
            return False, "Informe o local/evento."

        return True, ""

    def _resolver_carrinho_por_texto(self, txt: str):
        for c in self.carrinhos:
            if txt.startswith(c["nome"]) and c["id_externo"] in txt:
                return c
        return None

    def _resolver_motorista_por_texto(self, txt: str):
        nome = txt.split("•")[0].strip()
        for f in self.funcionarios:
            if f["nome"] == nome:
                return f
        return None

    def _conflito(self, novo):
        def overlap(a1, a2, b1, b2):
            return a1 < b2 and a2 > b1

        conflitos = []
        for a in self.agendamentos:
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
        self._carregar_dados_operacionais()
        self._atualizar_combos_operacionais()

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
            "id": self._agendamento_em_edicao_id or self._prox_id(),
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

        salvo_no_sistema = self._salvar_agendamento_no_sistema(novo)

        if not salvo_no_sistema:
            if self._agendamento_em_edicao_id is None:
                self.agendamentos.append(novo)
            else:
                for i, a in enumerate(self.agendamentos):
                    if a["id"] == self._agendamento_em_edicao_id:
                        self.agendamentos[i] = novo
                        break

        self._carregar_dados_operacionais()
        self._limpar_form()
        self._notificar_agenda()
        self._render_lista_carrinhos()
        messagebox.showinfo("Agendamento", "Agendamento salvo com sucesso!")

    def _prox_id(self):
        return max([a["id"] for a in self.agendamentos], default=0) + 1

    def _limpar_form(self):
        self._agendamento_em_edicao_id = None
        self.hora_ini_var.set("08:00")
        self.hora_fim_var.set("12:00")
        self.local_var.set("")
        self.combo_status_ag.set("Agendado")
        self._set_obs("")

    def _editar_agendamento_por_id(self, aid: int):
        self._carregar_dados_operacionais()
        a = next((x for x in self.agendamentos if x["id"] == aid), None)
        if not a:
            return

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

    def remover_agendamento_por_id(self, aid: int):
        removido_no_sistema = self._remover_agendamento_do_sistema(aid)

        if not removido_no_sistema:
            self.agendamentos = [x for x in self.agendamentos if x["id"] != aid]

        self._carregar_dados_operacionais()

        if self._agendamento_em_edicao_id == aid:
            self._limpar_form()

        self._notificar_agenda()

    def obter_agendamentos_do_dia(self):
        self._carregar_dados_operacionais()

        try:
            data = dt.date.fromisoformat(self.data_var.get().strip())
        except ValueError:
            return []

        do_dia = [a for a in self.agendamentos if a["data"] == data]
        do_dia.sort(key=lambda x: x["inicio_min"])
        return do_dia


# ===========================================================
# ABA 2: AGENDA DO DIA
# ===========================================================
class PaginaAgendaDoDia(ctk.CTkFrame):
    def __init__(self, master, pagina_agendamento: PaginaAgendamentoCarrinhos, on_back_to_agendamento=None):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        self.pagina_agendamento = pagina_agendamento
        self.on_back_to_agendamento = on_back_to_agendamento

        self.tree_agenda = None
        self._frame_tree_agenda = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._montar_ui()
        self.renderizar()

    def _montar_ui(self):
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.grid(row=0, column=0, padx=24, pady=(14, 8), sticky="ew")
        topo.grid_columnconfigure(0, weight=1)

        self.lbl_titulo = ctk.CTkLabel(
            topo,
            text="Agenda do dia",
            font=ctk.CTkFont(family=theme.FONTE, size=20, weight="bold"),
            text_color=theme.COR_TEXTO
        )
        self.lbl_titulo.grid(row=0, column=0, sticky="w")

        self.lbl_sub = ctk.CTkLabel(
            topo,
            text="Agendamentos da data selecionada na aba Agendamentos.",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC
        )
        self.lbl_sub.grid(row=1, column=0, pady=(2, 0), sticky="w")

        linha_btns = ctk.CTkFrame(self, fg_color="transparent")
        linha_btns.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="ew")
        linha_btns.grid_columnconfigure(0, weight=1)
        linha_btns.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            linha_btns,
            text="Atualizar agenda",
            height=36,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self.renderizar
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            linha_btns,
            text="Voltar para Agendamentos",
            height=36,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._voltar_para_agendamentos
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Agenda.Treeview",
            font=(theme.FONTE, 11),
            rowheight=34,
            background=theme.COR_BOTAO,
            fieldbackground=theme.COR_BOTAO,
            foreground=theme.COR_TEXTO,
            borderwidth=0,
            relief="flat"
        )
        style.configure(
            "Agenda.Treeview.Heading",
            font=(theme.FONTE, 11, "bold"),
            background=theme.COR_PAINEL,
            foreground=theme.COR_TEXTO,
            borderwidth=0,
            relief="flat"
        )
        style.map(
            "Agenda.Treeview",
            background=[("selected", theme.COR_SELECIONADO)],
            foreground=[("selected", theme.COR_TEXTO)]
        )

        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=2, column=0, padx=24, pady=(0, 20), sticky="nsew")
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(0, weight=1)

        self._frame_tree_agenda = ctk.CTkFrame(box, fg_color=theme.COR_BOTAO, corner_radius=12)
        self._frame_tree_agenda.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="nsew")
        self._frame_tree_agenda.grid_rowconfigure(0, weight=1)
        self._frame_tree_agenda.grid_columnconfigure(0, weight=1)
        self._frame_tree_agenda.bind("<Configure>", self._ajustar_colunas_tree_agenda)

        self.tree_agenda = ttk.Treeview(
            self._frame_tree_agenda,
            columns=("hora", "carrinho", "motorista", "local", "status"),
            show="headings",
            style="Agenda.Treeview"
        )
        self.tree_agenda.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)

        self.tree_agenda.heading("hora", text="Horário", anchor="w")
        self.tree_agenda.heading("carrinho", text="Carrinho", anchor="w")
        self.tree_agenda.heading("motorista", text="Responsável", anchor="w")
        self.tree_agenda.heading("local", text="Local/Evento", anchor="w")
        self.tree_agenda.heading("status", text="Status", anchor="w")

        scroll = ttk.Scrollbar(self._frame_tree_agenda, orient="vertical", command=self.tree_agenda.yview)
        scroll.grid(row=0, column=1, sticky="ns", padx=(8, 8), pady=8)
        self.tree_agenda.configure(yscrollcommand=scroll.set)

        self.tree_agenda.bind("<Double-1>", lambda e: self._carregar_para_edicao())

        ctk.CTkButton(
            box,
            text="Remover agendamento selecionado",
            height=36,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._remover_selecionado
        ).grid(row=1, column=0, padx=12, pady=(0, 12), sticky="ew")

    def _ajustar_colunas_tree_agenda(self, event=None):
        if not self.tree_agenda or not self._frame_tree_agenda:
            return

        largura = max(self._frame_tree_agenda.winfo_width() - 28, 420)
        c1 = int(largura * 0.14)
        c2 = int(largura * 0.22)
        c3 = int(largura * 0.22)
        c4 = int(largura * 0.28)
        c5 = max(largura - c1 - c2 - c3 - c4, 70)

        self.tree_agenda.column("hora", width=c1, anchor="w")
        self.tree_agenda.column("carrinho", width=c2, anchor="w")
        self.tree_agenda.column("motorista", width=c3, anchor="w")
        self.tree_agenda.column("local", width=c4, anchor="w")
        self.tree_agenda.column("status", width=c5, anchor="w")

    def renderizar(self):
        if not self.tree_agenda:
            return

        for item in self.tree_agenda.get_children():
            self.tree_agenda.delete(item)

        data_txt = self.pagina_agendamento.data_var.get().strip()
        self.lbl_titulo.configure(text=f"Agenda do dia • {data_txt}")

        do_dia = self.pagina_agendamento.obter_agendamentos_do_dia()

        for a in do_dia:
            self.tree_agenda.insert(
                "",
                "end",
                values=(
                    f'{a["inicio"]}–{a["fim"]}',
                    f'{a["carrinho_nome"]} ({a["carrinho_id_externo"]})',
                    a["motorista_nome"],
                    a["local"],
                    a["status"]
                ),
                tags=(f'ag-{a["id"]}',)
            )

    def _voltar_para_agendamentos(self):
        if callable(self.on_back_to_agendamento):
            self.on_back_to_agendamento()

    def _obter_id_selecionado(self):
        sel = self.tree_agenda.selection()
        if not sel:
            return None

        tags = self.tree_agenda.item(sel[0], "tags")
        if not tags:
            return None

        tag = tags[0]
        if not str(tag).startswith("ag-"):
            return None

        return int(str(tag).split("-")[1])

    def _carregar_para_edicao(self):
        aid = self._obter_id_selecionado()
        if aid is None:
            return

        self.pagina_agendamento._editar_agendamento_por_id(aid)
        if callable(self.on_back_to_agendamento):
            self.on_back_to_agendamento()
        messagebox.showinfo("Edição", "Agendamento carregado para edição na aba Agendamentos.")

    def _remover_selecionado(self):
        aid = self._obter_id_selecionado()
        if aid is None:
            messagebox.showwarning("Remover", "Selecione um agendamento na lista.")
            return

        if not messagebox.askyesno("Confirmar", "Deseja remover este agendamento?"):
            return

        self.pagina_agendamento.remover_agendamento_por_id(aid)
        self.renderizar()
        messagebox.showinfo("Removido", "Agendamento removido.")


# ===========================================================
# ABA 3: DELIVERY
# ===========================================================
class PaginaDelivery(ctk.CTkFrame):
    def __init__(self, master, sistema):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        self.sistema = sistema

        self.grid_columnconfigure(0, weight=4, uniform="dl_cols")
        self.grid_columnconfigure(1, weight=3, uniform="dl_cols")
        self.grid_columnconfigure(2, weight=2, uniform="dl_cols")
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self.cli_nome_var = ctk.StringVar(value="")
        self.cli_tel_var = ctk.StringVar(value="")
        self.end_rua_var = ctk.StringVar(value="")
        self.end_num_var = ctk.StringVar(value="")
        self.end_bairro_var = ctk.StringVar(value="")
        self.end_cidade_var = ctk.StringVar(value="Belém")
        self.end_comp_var = ctk.StringVar(value="")

        self.data_var = ctk.StringVar(value=dt.date.today().strftime("%Y-%m-%d"))
        self.prev_saida_var = ctk.StringVar(value="00:30")
        self.pag_var = ctk.StringVar(value="Pix")
        self.status_var = ctk.StringVar(value="Pendente")
        self.taxa_var = ctk.StringVar(value="5.00")

        self.produto_var = ctk.StringVar(value="")
        self.qtd_var = ctk.StringVar(value="1")
        self.carrinho_itens = []

        self.entregador_var = ctk.StringVar(value="")
        self.obs_widget = None
        self._pedido_em_edicao_id = None

        self.produtos = []
        self._mapa_produtos_combo = {}

        self.entregadores = self._carregar_entregadores()
        self.entregas = []

        self.tree_itens = None
        self.tree = None
        self.lbl_total = None
        self._frame_tree_itens = None
        self._frame_tree_delivery = None

        self._titulo()
        self._pedido_form()
        self._painel_itens()
        self._lista_dia()

        self._carregar_produtos_combo()
        self._render_itens()
        self._render_entregas_dia()

    def _obter_metodo_sistema(self, *nomes):
        if not self.sistema:
            return None
        for nome in nomes:
            metodo = getattr(self.sistema, nome, None)
            if callable(metodo):
                return metodo
        return None

    def _titulo(self):
        ctk.CTkLabel(
            self,
            text="Delivery",
            font=ctk.CTkFont(family=theme.FONTE, size=16, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        ctk.CTkLabel(
            self,
            text="Cadastre pedidos, organize itens e acompanhe as entregas.",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC
        ).grid(row=0, column=1, columnspan=2, padx=16, pady=(16, 8), sticky="w")

    def _pedido_form(self):
        left = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        left.grid(row=1, column=0, padx=(16, 8), pady=(0, 16), sticky="nsew")
        left.grid_columnconfigure(0, weight=1)

        box_cli = ctk.CTkFrame(left, fg_color=theme.COR_BOTAO, corner_radius=12)
        box_cli.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="ew")
        for c in range(2):
            box_cli.grid_columnconfigure(c, weight=1)

        ctk.CTkLabel(
            box_cli,
            text="Cliente",
            text_color=theme.COR_TEXTO,
            font=ctk.CTkFont(family=theme.FONTE, size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 4), sticky="w")

        ctk.CTkEntry(
            box_cli,
            textvariable=self.cli_nome_var,
            height=34,
            placeholder_text="Nome",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        ).grid(row=1, column=0, padx=(10, 5), pady=(0, 8), sticky="ew")

        ctk.CTkEntry(
            box_cli,
            textvariable=self.cli_tel_var,
            height=34,
            placeholder_text="Telefone",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        ).grid(row=1, column=1, padx=(5, 10), pady=(0, 8), sticky="ew")

        box_end = ctk.CTkFrame(left, fg_color=theme.COR_BOTAO, corner_radius=12)
        box_end.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        for c in range(4):
            box_end.grid_columnconfigure(c, weight=1)

        ctk.CTkLabel(
            box_end,
            text="Endereço de entrega",
            text_color=theme.COR_TEXTO,
            font=ctk.CTkFont(family=theme.FONTE, size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=4, padx=10, pady=(10, 4), sticky="w")

        ctk.CTkEntry(
            box_end,
            textvariable=self.end_rua_var,
            height=34,
            placeholder_text="Rua / Avenida",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        ).grid(row=1, column=0, columnspan=3, padx=(10, 5), pady=(0, 6), sticky="ew")

        ctk.CTkEntry(
            box_end,
            textvariable=self.end_num_var,
            height=34,
            placeholder_text="Número",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        ).grid(row=1, column=3, padx=(5, 10), pady=(0, 6), sticky="ew")

        ctk.CTkEntry(
            box_end,
            textvariable=self.end_bairro_var,
            height=34,
            placeholder_text="Bairro",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        ).grid(row=2, column=0, padx=(10, 5), pady=(0, 6), sticky="ew")

        ctk.CTkEntry(
            box_end,
            textvariable=self.end_cidade_var,
            height=34,
            placeholder_text="Cidade",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        ).grid(row=2, column=1, padx=5, pady=(0, 6), sticky="ew")

        ctk.CTkEntry(
            box_end,
            textvariable=self.end_comp_var,
            height=34,
            placeholder_text="Complemento / Referência",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        ).grid(row=2, column=2, columnspan=2, padx=(5, 10), pady=(0, 6), sticky="ew")

        box_cfg = ctk.CTkFrame(left, fg_color=theme.COR_BOTAO, corner_radius=12)
        box_cfg.grid(row=2, column=0, padx=12, pady=(0, 8), sticky="ew")
        for c in range(4):
            box_cfg.grid_columnconfigure(c, weight=1)

        ctk.CTkLabel(
            box_cfg,
            text="Pedido",
            text_color=theme.COR_TEXTO,
            font=ctk.CTkFont(family=theme.FONTE, size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=4, padx=10, pady=(10, 4), sticky="w")

        ctk.CTkLabel(box_cfg, text="Data", text_color=theme.COR_TEXTO).grid(row=1, column=0, padx=10, sticky="w")
        ctk.CTkEntry(
            box_cfg,
            textvariable=self.data_var,
            height=34,
            placeholder_text="AAAA-MM-DD",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        ).grid(row=2, column=0, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(box_cfg, text="Previsão de saída", text_color=theme.COR_TEXTO).grid(row=1, column=1, padx=10, sticky="w")
        ctk.CTkEntry(
            box_cfg,
            textvariable=self.prev_saida_var,
            height=34,
            placeholder_text="00:30",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        ).grid(row=2, column=1, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(box_cfg, text="Entregador", text_color=theme.COR_TEXTO).grid(row=1, column=2, padx=10, sticky="w")
        self.combo_entregador = ctk.CTkComboBox(
            box_cfg,
            values=[f'{e["nome"]} • {e["telefone"]}' for e in self.entregadores] or ["(nenhum entregador)"],
            variable=self.entregador_var,
            fg_color=theme.COR_BOTAO,
            button_color=theme.COR_SELECIONADO,
            button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_BOTAO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        )
        self.combo_entregador.grid(row=2, column=2, padx=10, pady=(0, 8), sticky="ew")
        if self.entregadores:
            self.combo_entregador.set(f'{self.entregadores[0]["nome"]} • {self.entregadores[0]["telefone"]}')
        else:
            self.combo_entregador.set("(nenhum entregador)")

        ctk.CTkLabel(box_cfg, text="Pagamento", text_color=theme.COR_TEXTO).grid(row=1, column=3, padx=10, sticky="w")
        self.combo_pag = ctk.CTkComboBox(
            box_cfg,
            values=["Pix", "Dinheiro", "Cartão"],
            variable=self.pag_var,
            fg_color=theme.COR_BOTAO,
            button_color=theme.COR_SELECIONADO,
            button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_BOTAO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        )
        self.combo_pag.grid(row=2, column=3, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(box_cfg, text="Status", text_color=theme.COR_TEXTO).grid(row=3, column=0, padx=10, sticky="w")
        self.combo_status = ctk.CTkComboBox(
            box_cfg,
            values=["Pendente", "Em preparo", "Em rota", "Entregue", "Cancelado"],
            variable=self.status_var,
            fg_color=theme.COR_BOTAO,
            button_color=theme.COR_SELECIONADO,
            button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_BOTAO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        )
        self.combo_status.grid(row=4, column=0, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(box_cfg, text="Taxa de entrega (R$)", text_color=theme.COR_TEXTO).grid(row=3, column=1, padx=10, sticky="w")
        ctk.CTkEntry(
            box_cfg,
            textvariable=self.taxa_var,
            height=34,
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        ).grid(row=4, column=1, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(box_cfg, text="Produto", text_color=theme.COR_TEXTO).grid(row=5, column=0, columnspan=2, padx=10, sticky="w")
        self.combo_prod = ctk.CTkComboBox(
            box_cfg,
            values=["(sem produtos)"],
            variable=self.produto_var,
            fg_color=theme.COR_BOTAO,
            button_color=theme.COR_SELECIONADO,
            button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_BOTAO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        )
        self.combo_prod.grid(row=6, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(box_cfg, text="Qtd", text_color=theme.COR_TEXTO).grid(row=5, column=2, padx=10, sticky="w")
        self.entry_qtd = ctk.CTkEntry(
            box_cfg,
            textvariable=self.qtd_var,
            height=34,
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        )
        self.entry_qtd.grid(row=6, column=2, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkButton(
            box_cfg,
            text="Adicionar item",
            height=34,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._adicionar_item
        ).grid(row=6, column=3, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(box_cfg, text="Observações", text_color=theme.COR_TEXTO).grid(row=7, column=0, columnspan=4, padx=10, sticky="w")
        self.obs_widget = ctk.CTkTextbox(
            box_cfg,
            height=58,
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        )
        self.obs_widget.grid(row=8, column=0, columnspan=4, padx=10, pady=(0, 10), sticky="ew")

        linha_total = ctk.CTkFrame(left, fg_color="transparent")
        linha_total.grid(row=3, column=0, padx=12, pady=(0, 12), sticky="ew")
        linha_total.grid_columnconfigure(0, weight=1)

        self.lbl_total = ctk.CTkLabel(
            linha_total,
            text="Total: R$ 0,00",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO
        )
        self.lbl_total.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            linha_total,
            text="Salvar pedido",
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._salvar_pedido
        ).grid(row=1, column=0, pady=(8, 0), sticky="ew")

    def _painel_itens(self):
        middle = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        middle.grid(row=1, column=1, padx=8, pady=(0, 16), sticky="nsew")
        middle.grid_columnconfigure(0, weight=1)
        middle.grid_rowconfigure(1, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Itens.Treeview",
            font=(theme.FONTE, 11),
            rowheight=30,
            background=theme.COR_BOTAO,
            fieldbackground=theme.COR_BOTAO,
            foreground=theme.COR_TEXTO,
            borderwidth=0,
            relief="flat"
        )
        style.configure(
            "Itens.Treeview.Heading",
            font=(theme.FONTE, 11, "bold"),
            background=theme.COR_PAINEL,
            foreground=theme.COR_TEXTO,
            borderwidth=0,
            relief="flat"
        )
        style.map(
            "Itens.Treeview",
            background=[("selected", theme.COR_SELECIONADO)],
            foreground=[("selected", theme.COR_TEXTO)]
        )

        ctk.CTkLabel(
            middle,
            text="Itens do pedido",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        self._frame_tree_itens = ctk.CTkFrame(middle, fg_color=theme.COR_BOTAO, corner_radius=12)
        self._frame_tree_itens.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="nsew")
        self._frame_tree_itens.grid_rowconfigure(0, weight=1)
        self._frame_tree_itens.grid_columnconfigure(0, weight=1)
        self._frame_tree_itens.bind("<Configure>", self._ajustar_colunas_tree_itens)

        self.tree_itens = ttk.Treeview(
            self._frame_tree_itens,
            columns=("produto", "qtd", "unitario", "subtotal"),
            show="headings",
            style="Itens.Treeview"
        )
        self.tree_itens.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)

        self.tree_itens.heading("produto", text="Produto", anchor="w")
        self.tree_itens.heading("qtd", text="Qtd", anchor="w")
        self.tree_itens.heading("unitario", text="Unitário", anchor="w")
        self.tree_itens.heading("subtotal", text="Subtotal", anchor="w")

        scroll = ttk.Scrollbar(self._frame_tree_itens, orient="vertical", command=self.tree_itens.yview)
        scroll.grid(row=0, column=1, sticky="ns", padx=(8, 8), pady=8)
        self.tree_itens.configure(yscrollcommand=scroll.set)

        ctk.CTkButton(
            middle,
            text="Remover item selecionado",
            height=36,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._remover_item_sel
        ).grid(row=2, column=0, padx=12, pady=(0, 12), sticky="ew")

    def _lista_dia(self):
        right = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        right.grid(row=1, column=2, padx=(8, 16), pady=(0, 16), sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Delivery.Treeview",
            font=(theme.FONTE, 11),
            rowheight=34,
            background=theme.COR_BOTAO,
            fieldbackground=theme.COR_BOTAO,
            foreground=theme.COR_TEXTO,
            borderwidth=0,
            relief="flat"
        )
        style.configure(
            "Delivery.Treeview.Heading",
            font=(theme.FONTE, 11, "bold"),
            background=theme.COR_PAINEL,
            foreground=theme.COR_TEXTO,
            borderwidth=0,
            relief="flat"
        )
        style.map(
            "Delivery.Treeview",
            background=[("selected", theme.COR_SELECIONADO)],
            foreground=[("selected", theme.COR_TEXTO)]
        )

        ctk.CTkLabel(
            right,
            text="Entregas do dia",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        self._frame_tree_delivery = ctk.CTkFrame(right, fg_color=theme.COR_BOTAO, corner_radius=12)
        self._frame_tree_delivery.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="nsew")
        self._frame_tree_delivery.grid_rowconfigure(0, weight=1)
        self._frame_tree_delivery.grid_columnconfigure(0, weight=1)
        self._frame_tree_delivery.bind("<Configure>", self._ajustar_colunas_tree_delivery)

        self.tree = ttk.Treeview(
            self._frame_tree_delivery,
            columns=("hora", "cliente", "valor", "status"),
            show="headings",
            style="Delivery.Treeview"
        )
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)

        self.tree.heading("hora", text="Previsão", anchor="w")
        self.tree.heading("cliente", text="Cliente", anchor="w")
        self.tree.heading("valor", text="Total", anchor="w")
        self.tree.heading("status", text="Status", anchor="w")

        scroll = ttk.Scrollbar(self._frame_tree_delivery, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns", padx=(8, 8), pady=8)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.bind("<Double-1>", lambda e: self._editar_pedido_sel())

        ctk.CTkButton(
            right,
            text="Remover pedido selecionado",
            height=36,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._remover_pedido_sel
        ).grid(row=2, column=0, padx=12, pady=(0, 12), sticky="ew")

    # -------------------- AJUSTES DINÂMICOS TREEVIEWS --------------------
    def _ajustar_colunas_tree_itens(self, event=None):
        if not self.tree_itens or not self._frame_tree_itens:
            return
        largura = max(self._frame_tree_itens.winfo_width() - 28, 250)
        c1 = int(largura * 0.44)
        c2 = int(largura * 0.10)
        c3 = int(largura * 0.22)
        c4 = max(largura - c1 - c2 - c3, 70)

        self.tree_itens.column("produto", width=c1, anchor="w")
        self.tree_itens.column("qtd", width=c2, anchor="w")
        self.tree_itens.column("unitario", width=c3, anchor="w")
        self.tree_itens.column("subtotal", width=c4, anchor="w")

    def _ajustar_colunas_tree_delivery(self, event=None):
        if not self.tree or not self._frame_tree_delivery:
            return
        largura = max(self._frame_tree_delivery.winfo_width() - 28, 220)
        c1 = int(largura * 0.22)
        c2 = int(largura * 0.38)
        c3 = int(largura * 0.20)
        c4 = max(largura - c1 - c2 - c3, 60)

        self.tree.column("hora", width=c1, anchor="w")
        self.tree.column("cliente", width=c2, anchor="w")
        self.tree.column("valor", width=c3, anchor="w")
        self.tree.column("status", width=c4, anchor="w")

    # -------------------- DADOS / SISTEMA --------------------
    def _listar_funcionarios_sistema(self):
        metodo = self._obter_metodo_sistema("listar_funcionarios")
        if not metodo:
            return []

        try:
            itens = metodo()
        except TypeError:
            try:
                itens = metodo(termo="")
            except Exception:
                return []
        except Exception:
            return []

        if not isinstance(itens, list):
            return []

        normalizados = []
        for f in itens:
            if not isinstance(f, dict):
                continue

            try:
                fid = int(f.get("id"))
            except Exception:
                continue

            normalizados.append({
                "id": fid,
                "nome": str(f.get("nome") or f"Funcionário {fid}"),
                "telefone": str(f.get("telefone") or ""),
                "cargo": str(f.get("cargo") or ""),
            })

        return normalizados

    def _carregar_entregadores(self):
        metodo = self._obter_metodo_sistema("listar_entregadores")
        if metodo:
            try:
                itens = metodo()
                if isinstance(itens, list) and itens:
                    normalizados = []
                    for e in itens:
                        if not isinstance(e, dict):
                            continue
                        try:
                            eid = int(e.get("id"))
                        except Exception:
                            continue
                        normalizados.append({
                            "id": eid,
                            "nome": str(e.get("nome") or f"Funcionário {eid}"),
                            "telefone": str(e.get("telefone") or ""),
                            "cargo": str(e.get("cargo") or ""),
                        })
                    if normalizados:
                        return normalizados
            except Exception:
                pass

        funcionarios = self._listar_funcionarios_sistema()
        if not funcionarios:
            return []

        filtrados = [
            f for f in funcionarios
            if any(chave in f["cargo"].lower() for chave in ("entreg", "motoboy", "moto"))
        ]
        return filtrados or funcionarios

    def _listar_catalogo(self):
        metodo = self._obter_metodo_sistema("listar_catalogo")
        if not metodo:
            return []

        try:
            itens = metodo()
        except TypeError:
            try:
                itens = metodo("")
            except Exception:
                itens = []
        except Exception:
            itens = []

        if not isinstance(itens, list):
            return []

        catalogo = []
        for p in itens:
            if not isinstance(p, dict):
                continue
            if p.get("ativo") is False:
                continue

            if p.get("eh_insumo") is True:
                continue
            if str(p.get("tipo_item", "")).strip().lower() == "insumo":
                continue

            try:
                preco = float(p.get("preco", 0) or 0)
            except Exception:
                preco = 0.0

            try:
                estoque = int(p.get("estoque", 0) or 0)
            except Exception:
                estoque = 0

            catalogo.append({
                "id": p["id"],
                "nome": p.get("nome", "Produto"),
                "preco": preco,
                "estoque": estoque,
            })

        return catalogo

    def _carregar_produtos_combo(self):
        self.produtos = self._listar_catalogo()
        self._mapa_produtos_combo = {}

        opcoes = []
        for p in self.produtos:
            texto = f'{p["nome"]} • {theme.fmt_dinheiro(p["preco"])}'
            opcoes.append(texto)
            self._mapa_produtos_combo[texto] = p

        if not opcoes:
            opcoes = ["(sem produtos)"]

        self.combo_prod.configure(values=opcoes)
        self.combo_prod.set(opcoes[0])

    def _resolver_produto_combo(self):
        texto = self.combo_prod.get().strip()
        return self._mapa_produtos_combo.get(texto)

    def _status_gera_venda(self, status):
        return status in {"Em preparo", "Em rota", "Entregue"}

    # -------------------- ITENS --------------------
    def _adicionar_item(self):
        self._carregar_produtos_combo()

        prod = self._resolver_produto_combo()
        if not prod:
            messagebox.showwarning("Itens", "Selecione um produto válido.")
            return

        try:
            qtd = int(self.qtd_var.get())
            if qtd <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Itens", "Quantidade inválida.")
            return

        existente = next((i for i in self.carrinho_itens if i["id"] == prod["id"]), None)
        qtd_atual = existente["qtd"] if existente else 0

        if prod.get("estoque", 0) > 0 and (qtd_atual + qtd) > prod["estoque"]:
            messagebox.showwarning("Itens", "Quantidade acima do estoque disponível.")
            return

        if existente:
            existente["qtd"] += qtd
        else:
            self.carrinho_itens.append({
                "id": prod["id"],
                "nome": prod["nome"],
                "preco": prod["preco"],
                "qtd": qtd
            })

        self._render_itens()

    def _remover_item_sel(self):
        if not self.tree_itens:
            return
        sel = self.tree_itens.selection()
        if not sel:
            messagebox.showwarning("Itens", "Selecione um item na lista.")
            return

        tags = self.tree_itens.item(sel[0], "tags")
        pid = None
        for t in tags:
            if str(t).startswith("it-"):
                pid = int(t.split("-")[1])
                break
        if pid is None:
            return

        self._remover_item(pid)

    def _remover_item(self, pid):
        self.carrinho_itens = [i for i in self.carrinho_itens if i["id"] != pid]
        self._render_itens()

    def _render_itens(self):
        if self.tree_itens:
            for i in self.tree_itens.get_children():
                self.tree_itens.delete(i)

        subtotal = 0.0
        for item in self.carrinho_itens:
            item_total = item["preco"] * item["qtd"]
            subtotal += item_total
            if self.tree_itens:
                self.tree_itens.insert(
                    "",
                    "end",
                    values=(
                        item["nome"],
                        item["qtd"],
                        theme.fmt_dinheiro(item["preco"]),
                        theme.fmt_dinheiro(item_total)
                    ),
                    tags=(f'it-{item["id"]}',)
                )

        try:
            taxa = float(self.taxa_var.get().replace(",", "."))
        except ValueError:
            taxa = 0.0

        total = subtotal + taxa
        if self.lbl_total:
            self.lbl_total.configure(text=f"Total: {theme.fmt_dinheiro(total)}")

    def _get_obs(self):
        return self.obs_widget.get("1.0", "end").strip()

    def _set_obs(self, txt):
        self.obs_widget.delete("1.0", "end")
        if txt:
            self.obs_widget.insert("1.0", txt)

    # -------------------- VALIDAÇÃO / CÁLCULO --------------------
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

        prev = self.prev_saida_var.get().strip()
        if prev and self._parse_hora(prev) is None:
            return False, "Previsão de saída inválida (use HH:MM)."

        return True, ""

    def _parse_hora(self, s):
        try:
            h, m = s.split(":")
            h = int(h)
            m = int(m)
            if 0 <= h <= 23 and 0 <= m <= 59:
                return h * 60 + m
        except Exception:
            pass
        return None

    def _calcular_total(self, itens, taxa):
        return sum(i["preco"] * i["qtd"] for i in itens) + taxa

    # -------------------- SALVAR / VENDAS --------------------
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

        pedido_existente = None
        if self._pedido_em_edicao_id is not None:
            pedido_existente = next((p for p in self.entregas if p["id"] == self._pedido_em_edicao_id), None)

        venda_ja_registrada = pedido_existente.get("venda_registrada", False) if pedido_existente else False

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
            "obs": self._get_obs(),
            "venda_registrada": venda_ja_registrada
        }

        precisa_registrar_venda = self._status_gera_venda(pedido["status"]) and not venda_ja_registrada

        if precisa_registrar_venda:
            try:
                try:
                    self.sistema.registrar_venda(
                        tipo="DELIVERY",
                        cliente_id=None,
                        itens=[{"produto_id": i["id"], "qtd": i["qtd"]} for i in self.carrinho_itens],
                        forma_pagamento=self.combo_pag.get(),
                        desconto=0,
                        taxa_entrega=taxa,
                        observacao=self._get_obs(),
                        data_venda=self.data_var.get().strip(),
                    )
                except TypeError:
                    self.sistema.registrar_venda(
                        tipo="DELIVERY",
                        cliente_id=None,
                        itens=[{"produto_id": i["id"], "qtd": i["qtd"]} for i in self.carrinho_itens],
                        forma_pagamento=self.combo_pag.get(),
                        desconto=0,
                        observacao=self._get_obs(),
                        data_venda=self.data_var.get().strip(),
                    )
            except Exception as e:
                messagebox.showerror(
                    "Erro",
                    f"Não foi possível registrar a venda do delivery.\n\nDetalhes: {e}"
                )
                return

            pedido["venda_registrada"] = True

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
        if not txt or txt == "(nenhum entregador)":
            return None
        nome = txt.split("•")[0].strip()
        return next((e for e in self.entregadores if e["nome"] == nome), None)

    def _prox_id(self):
        return max([p["id"] for p in self.entregas], default=0) + 1

    def _limpar_form(self):
        self._pedido_em_edicao_id = None
        self.cli_nome_var.set("")
        self.cli_tel_var.set("")
        self.end_rua_var.set("")
        self.end_num_var.set("")
        self.end_bairro_var.set("")
        self.end_comp_var.set("")
        self.prev_saida_var.set("00:30")
        self.pag_var.set("Pix")
        self.status_var.set("Pendente")
        self.taxa_var.set("5.00")
        self.carrinho_itens = []
        self._set_obs("")
        self._carregar_produtos_combo()
        self._render_itens()

    # -------------------- LISTA DO DIA --------------------
    def _render_entregas_dia(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        try:
            dia = dt.date.fromisoformat(self.data_var.get().strip())
        except ValueError:
            dia = dt.date.today()

        do_dia = [p for p in self.entregas if p["data"] == dia]

        def key_prev(p):
            m = self._parse_hora(p["prev"]) if p["prev"] else 9999
            return m

        do_dia.sort(key=key_prev)

        for p in do_dia:
            self.tree.insert(
                "",
                "end",
                values=(
                    p["prev"],
                    p["cliente"]["nome"],
                    theme.fmt_dinheiro(p["total"]),
                    p["status"]
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

        if p["entregador_nome"]:
            ent = next((e for e in self.entregadores if e["nome"] == p["entregador_nome"]), None)
            if ent:
                self.combo_entregador.set(f'{ent["nome"]} • {ent["telefone"]}')
            else:
                self.combo_entregador.set(p["entregador_nome"])

        self._set_obs(p.get("obs", ""))
        self.carrinho_itens = [dict(i) for i in p["itens"]]
        self._carregar_produtos_combo()
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
# WRAPPER: ABAS
# ===========================================================
class PaginaOperacaoCarrinhos(ctk.CTkFrame):
    """
    Página com abas:
      - Agendamentos
      - Agenda do dia
      - Delivery
    """
    def __init__(self, master, sistema):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        self.sistema = sistema

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

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

        self.tabs = ctk.CTkTabview(
            self,
            fg_color=theme.COR_PAINEL,
            segmented_button_fg_color=theme.COR_BOTAO,
            segmented_button_selected_color=theme.COR_SELECIONADO,
            segmented_button_selected_hover_color=theme.COR_HOVER,
            segmented_button_unselected_color=theme.COR_BOTAO,
            segmented_button_unselected_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            corner_radius=14,
            anchor="w"
        )
        self.tabs.grid(row=2, column=0, padx=24, pady=(0, 20), sticky="nsew")

        tab_ag = self.tabs.add("Agendamentos")
        tab_agenda = self.tabs.add("Agenda do dia")
        tab_dl = self.tabs.add("Delivery")

        self.pg_ag = PaginaAgendamentoCarrinhos(
            tab_ag,
            sistema=self.sistema,
            on_open_agenda=self._ir_para_aba_agenda,
            on_agenda_changed=self._atualizar_aba_agenda
        )
        self.pg_ag.pack(fill="both", expand=True, padx=6, pady=6)

        self.pg_agenda = PaginaAgendaDoDia(
            tab_agenda,
            pagina_agendamento=self.pg_ag,
            on_back_to_agendamento=self._ir_para_aba_agendamentos
        )
        self.pg_agenda.pack(fill="both", expand=True, padx=6, pady=6)

        self.pg_dl = PaginaDelivery(tab_dl, self.sistema)
        self.pg_dl.pack(fill="both", expand=True, padx=6, pady=6)

    def _ir_para_aba_agenda(self):
        self.pg_agenda.renderizar()
        self.tabs.set("Agenda do dia")

    def _ir_para_aba_agendamentos(self):
        self.tabs.set("Agendamentos")

    def _atualizar_aba_agenda(self):
        self.pg_agenda.renderizar()