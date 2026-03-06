# app/pages/servicos/delivery_inalterado.py
# -*- coding: utf-8 -*-
import customtkinter as ctk
from tkinter import ttk, messagebox
import datetime as dt

from app.config import theme


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

    # -------------------- Helpers sistema --------------------
    def _obter_metodo_sistema(self, *nomes):
        if not self.sistema:
            return None
        for nome in nomes:
            metodo = getattr(self.sistema, nome, None)
            if callable(metodo):
                return metodo
        return None

    # -------------------- UI --------------------
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
            box_cli, text="Cliente",
            text_color=theme.COR_TEXTO,
            font=ctk.CTkFont(family=theme.FONTE, size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 4), sticky="w")

        ctk.CTkEntry(
            box_cli, textvariable=self.cli_nome_var, height=34,
            placeholder_text="Nome",
            fg_color=theme.COR_BOTAO, text_color=theme.COR_TEXTO,
            border_width=1, border_color=theme.COR_HOVER
        ).grid(row=1, column=0, padx=(10, 5), pady=(0, 8), sticky="ew")

        ctk.CTkEntry(
            box_cli, textvariable=self.cli_tel_var, height=34,
            placeholder_text="Telefone",
            fg_color=theme.COR_BOTAO, text_color=theme.COR_TEXTO,
            border_width=1, border_color=theme.COR_HOVER
        ).grid(row=1, column=1, padx=(5, 10), pady=(0, 8), sticky="ew")

        box_end = ctk.CTkFrame(left, fg_color=theme.COR_BOTAO, corner_radius=12)
        box_end.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        for c in range(4):
            box_end.grid_columnconfigure(c, weight=1)

        ctk.CTkLabel(
            box_end, text="Endereço de entrega",
            text_color=theme.COR_TEXTO,
            font=ctk.CTkFont(family=theme.FONTE, size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=4, padx=10, pady=(10, 4), sticky="w")

        ctk.CTkEntry(
            box_end, textvariable=self.end_rua_var, height=34,
            placeholder_text="Rua / Avenida",
            fg_color=theme.COR_BOTAO, text_color=theme.COR_TEXTO,
            border_width=1, border_color=theme.COR_HOVER
        ).grid(row=1, column=0, columnspan=3, padx=(10, 5), pady=(0, 6), sticky="ew")

        ctk.CTkEntry(
            box_end, textvariable=self.end_num_var, height=34,
            placeholder_text="Número",
            fg_color=theme.COR_BOTAO, text_color=theme.COR_TEXTO,
            border_width=1, border_color=theme.COR_HOVER
        ).grid(row=1, column=3, padx=(5, 10), pady=(0, 6), sticky="ew")

        ctk.CTkEntry(
            box_end, textvariable=self.end_bairro_var, height=34,
            placeholder_text="Bairro",
            fg_color=theme.COR_BOTAO, text_color=theme.COR_TEXTO,
            border_width=1, border_color=theme.COR_HOVER
        ).grid(row=2, column=0, padx=(10, 5), pady=(0, 6), sticky="ew")

        ctk.CTkEntry(
            box_end, textvariable=self.end_cidade_var, height=34,
            placeholder_text="Cidade",
            fg_color=theme.COR_BOTAO, text_color=theme.COR_TEXTO,
            border_width=1, border_color=theme.COR_HOVER
        ).grid(row=2, column=1, padx=5, pady=(0, 6), sticky="ew")

        ctk.CTkEntry(
            box_end, textvariable=self.end_comp_var, height=34,
            placeholder_text="Complemento / Referência",
            fg_color=theme.COR_BOTAO, text_color=theme.COR_TEXTO,
            border_width=1, border_color=theme.COR_HOVER
        ).grid(row=2, column=2, columnspan=2, padx=(5, 10), pady=(0, 6), sticky="ew")

        box_cfg = ctk.CTkFrame(left, fg_color=theme.COR_BOTAO, corner_radius=12)
        box_cfg.grid(row=2, column=0, padx=12, pady=(0, 8), sticky="ew")
        for c in range(4):
            box_cfg.grid_columnconfigure(c, weight=1)

        ctk.CTkLabel(
            box_cfg, text="Pedido",
            text_color=theme.COR_TEXTO,
            font=ctk.CTkFont(family=theme.FONTE, size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=4, padx=10, pady=(10, 4), sticky="w")

        ctk.CTkLabel(box_cfg, text="Data", text_color=theme.COR_TEXTO).grid(row=1, column=0, padx=10, sticky="w")
        ctk.CTkEntry(
            box_cfg, textvariable=self.data_var, height=34,
            placeholder_text="AAAA-MM-DD",
            fg_color=theme.COR_BOTAO, text_color=theme.COR_TEXTO,
            border_width=1, border_color=theme.COR_HOVER
        ).grid(row=2, column=0, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(box_cfg, text="Previsão de saída", text_color=theme.COR_TEXTO).grid(row=1, column=1, padx=10, sticky="w")
        ctk.CTkEntry(
            box_cfg, textvariable=self.prev_saida_var, height=34,
            placeholder_text="00:30",
            fg_color=theme.COR_BOTAO, text_color=theme.COR_TEXTO,
            border_width=1, border_color=theme.COR_HOVER
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
            values=["Pix", "Dinheiro", "Cartão", "Cartao", "Prazo"],
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

    # -------------------- painel itens --------------------
    def _painel_itens(self):
        middle = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        middle.grid(row=1, column=1, padx=8, pady=(0, 16), sticky="nsew")
        middle.grid_columnconfigure(0, weight=1)
        middle.grid_rowconfigure(1, weight=1)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
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

    # -------------------- lista dia --------------------
    def _lista_dia(self):
        right = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        right.grid(row=1, column=2, padx=(8, 16), pady=(0, 16), sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
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

    # -------------------- ajustes tree --------------------
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

    # -------------------- dados --------------------
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

    # -------------------- itens --------------------
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
            self.tree_itens.insert(
                "",
                "end",
                values=(item["nome"], item["qtd"], theme.fmt_dinheiro(item["preco"]), theme.fmt_dinheiro(item_total)),
                tags=(f'it-{item["id"]}',)
            )

        try:
            taxa = float(self.taxa_var.get().replace(",", "."))
        except ValueError:
            taxa = 0.0

        total = subtotal + taxa
        self.lbl_total.configure(text=f"Total: {theme.fmt_dinheiro(total)}")

    def _get_obs(self):
        return self.obs_widget.get("1.0", "end").strip()

    def _set_obs(self, txt):
        self.obs_widget.delete("1.0", "end")
        if txt:
            self.obs_widget.insert("1.0", txt)

    # -------------------- validação --------------------
    def _parse_hora(self, s):
        try:
            h, m = s.split(":")
            h = int(h); m = int(m)
            if 0 <= h <= 23 and 0 <= m <= 59:
                return h * 60 + m
        except Exception:
            return None
        return None

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

    # -------------------- banco: listar --------------------
    def _listar_entregas_dia_sistema(self, dia: dt.date):
        metodo = self._obter_metodo_sistema("listar_delivery_dia")
        if not metodo:
            return []
        try:
            res = metodo(dia)
            return res if isinstance(res, list) else []
        except Exception:
            return []

    def _obter_pedido_sistema(self, pedido_id: int):
        metodo = self._obter_metodo_sistema("obter_delivery")
        if not metodo:
            return None
        try:
            return metodo(pedido_id)
        except Exception:
            return None

    # -------------------- salvar pedido (MySQL + venda) --------------------
    def _salvar_pedido(self):
        ok, msg = self._validar()
        if not ok:
            messagebox.showwarning("Validação", msg)
            return

        try:
            taxa = float(self.taxa_var.get().replace(",", "."))
        except ValueError:
            taxa = 0.0

        # resolver entregador
        ent_txt = self.combo_entregador.get().strip()
        entregador_id = None
        entregador_nome = ""
        if ent_txt and ent_txt != "(nenhum entregador)":
            nome = ent_txt.split("•")[0].strip()
            ent = next((e for e in self.entregadores if e["nome"] == nome), None)
            if ent:
                entregador_id = ent["id"]
                entregador_nome = ent["nome"]

        pedido = {
            "id": self._pedido_em_edicao_id,
            "data": dt.date.fromisoformat(self.data_var.get().strip()),
            "prev": self.prev_saida_var.get().strip(),
            "cliente": {"nome": self.cli_nome_var.get().strip(), "telefone": self.cli_tel_var.get().strip()},
            "endereco": {
                "rua": self.end_rua_var.get().strip(),
                "numero": self.end_num_var.get().strip(),
                "bairro": self.end_bairro_var.get().strip(),
                "cidade": self.end_cidade_var.get().strip(),
                "comp": self.end_comp_var.get().strip(),
            },
            "itens": [dict(i) for i in self.carrinho_itens],
            "taxa": taxa,
            "pagamento": self.combo_pag.get().strip(),
            "status": self.combo_status.get().strip(),
            "entregador_id": entregador_id,
            "entregador_nome": entregador_nome,
            "obs": self._get_obs(),
        }

        metodo = self._obter_metodo_sistema("salvar_pedido_delivery")
        if not metodo:
            messagebox.showerror("Erro", "SistemaService não possui salvar_pedido_delivery().")
            return

        try:
            metodo(pedido)  # ✅ salva no MySQL e gera venda quando necessário
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o delivery.\n\n{e}")
            return

        self._limpar_form()
        self._render_entregas_dia()
        messagebox.showinfo("Delivery", "Pedido salvo com sucesso!")

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

    # -------------------- render entregas --------------------
    def _render_entregas_dia(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        try:
            dia = dt.date.fromisoformat(self.data_var.get().strip())
        except ValueError:
            dia = dt.date.today()

        entregas = self._listar_entregas_dia_sistema(dia)

        # ordena por prev
        def key_prev(p):
            m = self._parse_hora(p.get("prev", "")) if p.get("prev") else 9999
            return m

        entregas.sort(key=key_prev)

        for p in entregas:
            self.tree.insert(
                "",
                "end",
                values=(p.get("prev", ""), p.get("cliente", {}).get("nome", ""), theme.fmt_dinheiro(p.get("total", 0)), p.get("status", "")),
                tags=(f'pd-{p["id"]}',)
            )

    def _pedido_id_por_sel(self):
        sel = self.tree.selection()
        if not sel:
            return None
        tags = self.tree.item(sel[0], "tags")
        if not tags:
            return None
        tag = str(tags[0])
        if not tag.startswith("pd-"):
            return None
        return int(tag.split("-")[1])

    def _editar_pedido_sel(self):
        pid = self._pedido_id_por_sel()
        if pid is None:
            return

        p = self._obter_pedido_sistema(pid)
        if not p:
            messagebox.showwarning("Editar", "Pedido não encontrado.")
            return

        self._pedido_em_edicao_id = p["id"]
        self.data_var.set(p["data"].strftime("%Y-%m-%d"))
        self.prev_saida_var.set(p.get("prev", ""))
        self.cli_nome_var.set(p.get("cliente", {}).get("nome", ""))
        self.cli_tel_var.set(p.get("cliente", {}).get("telefone", ""))
        self.end_rua_var.set(p.get("endereco", {}).get("rua", ""))
        self.end_num_var.set(p.get("endereco", {}).get("numero", ""))
        self.end_bairro_var.set(p.get("endereco", {}).get("bairro", ""))
        self.end_cidade_var.set(p.get("endereco", {}).get("cidade", "Belém"))
        self.end_comp_var.set(p.get("endereco", {}).get("comp", ""))
        self.pag_var.set(p.get("pagamento", "Pix"))
        self.status_var.set(p.get("status", "Pendente"))
        self.taxa_var.set(f'{float(p.get("taxa", 0)):0.2f}'.replace(".", ","))

        if p.get("entregador_nome"):
            # tenta achar na lista
            ent = next((e for e in self.entregadores if e["nome"] == p["entregador_nome"]), None)
            if ent:
                self.combo_entregador.set(f'{ent["nome"]} • {ent["telefone"]}')
            else:
                self.combo_entregador.set(p["entregador_nome"])

        self._set_obs(p.get("obs", ""))
        self.carrinho_itens = [dict(i) for i in p.get("itens", [])]
        self._carregar_produtos_combo()
        self._render_itens()
        messagebox.showinfo("Editar", "Pedido carregado para edição.")

    def _remover_pedido_sel(self):
        pid = self._pedido_id_por_sel()
        if pid is None:
            messagebox.showwarning("Remover", "Selecione um pedido.")
            return

        if not messagebox.askyesno("Confirmar", "Deseja remover este pedido?"):
            return

        metodo = self._obter_metodo_sistema("excluir_delivery")
        if not metodo:
            messagebox.showerror("Erro", "SistemaService não possui excluir_delivery().")
            return

        try:
            metodo(pid)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao remover.\n\n{e}")
            return

        if self._pedido_em_edicao_id == pid:
            self._limpar_form()

        self._render_entregas_dia()
        messagebox.showinfo("Removido", "Pedido removido.")