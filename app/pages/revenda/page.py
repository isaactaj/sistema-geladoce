# -*- coding: utf-8 -*-
"""
MÓDULO DE REVENDA - Sistema Geladoce
===================================

Aba "Nova Revenda" inspirada na página de Vendas no Balcão:
- Catálogo de produtos à esquerda
- Painel lateral de carrinho à direita
- Vinculação opcional de cliente
- Campos extras: revendedor, data/hora, pagamento, desconto, observação

Aba "Histórico de Revendas":
- Tabela com filtro por mês e ano
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.config import theme


class PaginaRevenda(ctk.CTkFrame):
    def __init__(self, master, sistema=None):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        self.sistema = sistema

        # Layout principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Estado geral
        self.busca_var = ctk.StringVar(value="")
        self.tipo_var = ctk.StringVar(value="Todos")
        self.carrinho = []  # {id, nome, preco, qtd, categoria}

        # Cliente opcional
        self.vincular_cliente_var = ctk.BooleanVar(value=False)
        self.cliente_busca_var = ctk.StringVar(value="")
        self.cliente_selecionado = None
        self._clientes_filtrados = []

        # Revendedores
        self.revendedores_map = {}

        # Histórico (fallback local caso o serviço ainda não tenha listagem)
        self._historico_local = []
        self._usar_historico_local = False

        # UI
        self._topo()
        self._render_abas()

    # ==========================================================
    # Helpers
    # ==========================================================
    def _fmt_moeda(self, valor):
        try:
            return theme.fmt_dinheiro(float(valor))
        except Exception:
            return "R$ 0,00"

    def _obter_desconto(self):
        if not hasattr(self, "entry_desconto"):
            return Decimal("0")

        texto = self.entry_desconto.get().strip().replace(".", "").replace(",", ".")
        if not texto:
            return Decimal("0")

        try:
            valor = Decimal(texto)
            if valor < 0:
                return Decimal("0")
            return valor
        except (InvalidOperation, ValueError):
            return Decimal("0")

    def _configurar_treeview(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Geladoce.Treeview",
            font=(theme.FONTE, 12),
            rowheight=30,
            background=theme.COR_FUNDO,
            fieldbackground=theme.COR_FUNDO,
            foreground=theme.COR_TEXTO,
            borderwidth=0,
            relief="flat",
        )
        style.configure(
            "Geladoce.Treeview.Heading",
            font=(theme.FONTE, 12, "bold"),
            background=theme.COR_HOVER,
            foreground=theme.COR_TEXTO,
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Geladoce.Treeview",
            background=[("selected", theme.COR_HOVER)],
            foreground=[("selected", theme.COR_TEXTO)],
        )

    def _listar_clientes(self, termo=""):
        try:
            return self.sistema.listar_clientes(termo=termo)
        except TypeError:
            try:
                return self.sistema.listar_clientes(termo)
            except TypeError:
                return self.sistema.listar_clientes()

    def _listar_clientes_para_vinculo(self, termo=""):
        """
        Cliente opcional da revenda.
        Mantém apenas clientes que não sejam revendedores.
        """
        clientes = self._listar_clientes(termo)
        resultado = []

        for c in clientes:
            tipo_cliente = str(c.get("tipo_cliente", "Varejo")).strip().lower()
            if tipo_cliente == "revendedor":
                continue
            resultado.append(c)

        return resultado

    def _listar_revendedores(self):
        """
        Revendedor vem do cadastro de clientes.
        Primeiro tenta método dedicado do sistema; se não existir,
        filtra em listar_clientes().
        """
        try:
            revendedores = self.sistema.listar_revendedores()
            if isinstance(revendedores, list):
                return revendedores
        except Exception:
            pass

        revendedores = []
        for c in self._listar_clientes(""):
            tipo_cliente = str(c.get("tipo_cliente", "")).strip().lower()
            if tipo_cliente == "revendedor":
                revendedores.append(c)
        return revendedores

    def _carregar_revendedores_combo(self):
        if not hasattr(self, "combo_revendedor"):
            return

        revendedores = self._listar_revendedores()
        nomes = [r["nome"] for r in revendedores]

        self.revendedores_map = {r["nome"]: r["id"] for r in revendedores}

        if not nomes:
            nomes = ["(nenhum)"]

        self.combo_revendedor.configure(values=nomes)
        self.combo_revendedor.set(nomes[0])

    def _listar_catalogo(self, termo="", categoria="Todos"):
        try:
            return self.sistema.listar_catalogo(termo=termo, categoria=categoria)
        except TypeError:
            try:
                if categoria != "Todos":
                    return self.sistema.listar_catalogo(termo, categoria)
                return self.sistema.listar_catalogo(termo)
            except TypeError:
                return self.sistema.listar_catalogo()

    def _obter_produto_catalogo(self, produto_id):
        produtos = self._listar_catalogo("", "Todos")
        for p in produtos:
            if p["id"] == produto_id:
                return p
        return None

    def _qtd_no_carrinho(self, produto_id):
        item = next((c for c in self.carrinho if c["id"] == produto_id), None)
        return item["qtd"] if item else 0

    def _estoque_disponivel(self, produto):
        estoque_real = int(produto.get("estoque", 0))
        reservado = self._qtd_no_carrinho(produto["id"])
        return max(estoque_real - reservado, 0)

    def _extrair_subgrupo(self, produto):
        """
        Mantém a organização visual do tree:
        categoria -> subgrupo -> item
        """
        nome = str(produto.get("nome", "")).strip()

        if "•" in nome:
            partes = [p.strip() for p in nome.split("•") if p.strip()]
            if len(partes) >= 2:
                return partes[-1]

        if "(" in nome and ")" in nome:
            ini = nome.rfind("(")
            fim = nome.rfind(")")
            if ini != -1 and fim != -1 and fim > ini:
                conteudo = nome[ini + 1:fim].strip()
                if conteudo:
                    return conteudo

        return "Itens"

    def _nome_cliente_por_id(self, cliente_id):
        if not cliente_id:
            return None

        for c in self._listar_clientes(""):
            if c.get("id") == cliente_id:
                return c.get("nome")
        return None

    def _nome_revendedor_por_id(self, revendedor_id):
        if not revendedor_id:
            return None

        for r in self._listar_revendedores():
            if r.get("id") == revendedor_id:
                return r.get("nome")
        return None

    def _listar_revendas(self):
        """
        Tenta buscar no sistema; se o sistema ainda não tiver um método de listagem,
        usa o histórico local da sessão como fallback.
        """
        registros = None
        consultou_servico = False

        # 1) tentar listar_vendas(tipo="REVENDA")
        try:
            if hasattr(self.sistema, "listar_vendas"):
                consultou_servico = True
                registros = self.sistema.listar_vendas(tipo="REVENDA")
        except TypeError:
            try:
                registros = self.sistema.listar_vendas()
            except Exception:
                registros = None
        except Exception:
            registros = None

        # 2) fallback: tentar listar_revendas()
        if registros is None:
            try:
                if hasattr(self.sistema, "listar_revendas"):
                    consultou_servico = True
                    registros = self.sistema.listar_revendas()
            except Exception:
                registros = None

        if registros is None and not consultou_servico:
            self._usar_historico_local = True
            return list(self._historico_local)

        self._usar_historico_local = False

        if not isinstance(registros, list):
            return []

        normalizados = []
        for reg in registros:
            item = self._normalizar_registro_revenda(reg)
            if item:
                normalizados.append(item)

        return normalizados

    def _normalizar_registro_revenda(self, reg):
        """
        Converte o retorno do sistema para o formato que a tree do histórico espera.
        """
        if not isinstance(reg, dict):
            return None

        tipo = str(reg.get("tipo", reg.get("tipo_venda", "REVENDA"))).strip().upper()
        if tipo and tipo != "REVENDA":
            return None

        venda_id = reg.get("id", reg.get("venda_id", reg.get("codigo", "")))

        data_valor = reg.get("data_venda", reg.get("data", reg.get("data_hora", "")))
        if isinstance(data_valor, datetime):
            data_txt = data_valor.strftime("%d/%m/%Y %H:%M")
        else:
            data_txt = str(data_valor).strip()

        revendedor_nome = reg.get("revendedor_nome") or reg.get("revendedor")
        if not revendedor_nome:
            revendedor_nome = self._nome_revendedor_por_id(reg.get("revendedor_id"))

        cliente_nome = reg.get("cliente_nome") or reg.get("cliente")
        if not cliente_nome:
            cliente_nome = self._nome_cliente_por_id(reg.get("cliente_id"))

        pagamento = reg.get("forma_pagamento", reg.get("pagamento", "-"))

        itens = reg.get("itens", reg.get("produtos", []))
        if not isinstance(itens, list):
            itens = []

        qtd_itens = reg.get("qtd_itens")
        if qtd_itens is None:
            qtd_itens = sum(int(item.get("qtd", 0)) for item in itens)

        total = reg.get("total")
        if total is None:
            subtotal = reg.get("subtotal", 0)
            desconto = reg.get("desconto", 0)
            try:
                total = Decimal(str(subtotal)) - Decimal(str(desconto))
            except Exception:
                total = 0

        return {
            "id": venda_id,
            "data": data_txt,
            "revendedor_nome": revendedor_nome or "-",
            "cliente_nome": cliente_nome or None,
            "pagamento": pagamento,
            "qtd_itens": qtd_itens,
            "total": total,
        }

    # ==========================================================
    # Topo e abas
    # ==========================================================
    def _topo(self):
        ctk.CTkLabel(
            self,
            text="Revenda",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=30, pady=(14, 4), sticky="w")

    def _render_abas(self):
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=theme.COR_PAINEL,
            segmented_button_fg_color=theme.COR_BOTAO,
            segmented_button_selected_color=theme.COR_SELECIONADO,
            segmented_button_selected_hover_color=theme.COR_HOVER,
            segmented_button_unselected_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
        )
        self.tabview.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="nsew")

        aba_nova = self.tabview.add("Nova Revenda")
        aba_historico = self.tabview.add("Histórico de Revendas")

        self._render_aba_nova_revenda(aba_nova)
        self._render_aba_historico(aba_historico)

    # ==========================================================
    # ABA 1 - Nova Revenda
    # ==========================================================
    def _render_aba_nova_revenda(self, parent):
        # Layout igual à lógica da venda balcão
        parent.grid_columnconfigure(0, weight=3)  # catálogo
        parent.grid_columnconfigure(1, weight=2)  # carrinho/painel direito

        parent.grid_rowconfigure(0, weight=0)  # filtros
        parent.grid_rowconfigure(1, weight=1)  # catálogo cresce

        self._configurar_treeview()

        self._filtros(parent)
        self._catalogo(parent)
        self._painel_direito(parent)

        self._render_catalogo()
        self._render_carrinho()
        self._toggle_cliente()

    def _filtros(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=0, padx=(30, 12), pady=(20, 10), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        self.entry_busca = ctk.CTkEntry(
            frame,
            textvariable=self.busca_var,
            placeholder_text="🔎 Buscar produto/sabor…",
            height=36,
            fg_color=theme.COR_FUNDO,
            text_color=theme.COR_TEXTO,
            border_color=theme.COR_HOVER,
        )
        self.entry_busca.grid(row=0, column=0, sticky="ew")
        self.entry_busca.bind("<KeyRelease>", lambda e: self._render_catalogo())

        self.combo_tipo = ctk.CTkComboBox(
            frame,
            values=["Todos", "Sorvete", "Picolé", "Açaí", "Outros"],
            width=160,
            command=lambda _: self._render_catalogo(),
            state="readonly",
            fg_color=theme.COR_FUNDO,
            button_color=theme.COR_HOVER,
            button_hover_color=theme.COR_SELECIONADO,
            border_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_FUNDO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
        )
        self.combo_tipo.set("Todos")
        self.combo_tipo.grid(row=0, column=1, padx=(10, 0))

    def _catalogo(self, parent):
        box = ctk.CTkFrame(parent, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=1, column=0, padx=(30, 12), pady=(0, 20), sticky="nsew")
        box.grid_rowconfigure(0, weight=1)
        box.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            box,
            style="Geladoce.Treeview",
            columns=("preco", "estoque"),
            show="tree headings"
        )
        self.tree.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        self.tree.heading("#0", text="Produto")
        self.tree.heading("preco", text="Preço")
        self.tree.heading("estoque", text="Estoque")

        self.tree.column("#0", width=280, anchor="w")
        self.tree.column("preco", width=100, anchor="e")
        self.tree.column("estoque", width=80, anchor="center")

        scroll_y = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        scroll_y.grid(row=0, column=1, sticky="ns", padx=(0, 12), pady=12)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.bind("<Double-1>", lambda e: self._adicionar_selecionado())
        self.tree.tag_configure("sem_estoque", foreground="#888888")

    def _painel_direito(self, parent):
        box = ctk.CTkFrame(parent, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=0, column=1, rowspan=2, padx=(12, 30), pady=(20, 20), sticky="nsew")
        box.grid_columnconfigure(0, weight=1)

        # Rows
        box.grid_rowconfigure(0, weight=0)  # título
        box.grid_rowconfigure(1, weight=0)  # cliente
        box.grid_rowconfigure(2, weight=0)  # dados extras
        box.grid_rowconfigure(3, weight=0)  # total
        box.grid_rowconfigure(4, weight=1)  # lista carrinho
        box.grid_rowconfigure(5, weight=0)  # ações

        ctk.CTkLabel(
            box,
            text="Carrinho da Revenda",
            font=ctk.CTkFont(family=theme.FONTE, size=16, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        # ===== Cliente (opcional) =====
        self.cliente_box = ctk.CTkFrame(box, fg_color=theme.COR_FUNDO, corner_radius=14)
        self.cliente_box.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")
        self.cliente_box.grid_columnconfigure(0, weight=1)

        top_line = ctk.CTkFrame(self.cliente_box, fg_color="transparent")
        top_line.grid(row=0, column=0, padx=12, pady=(10, 6), sticky="ew")
        top_line.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top_line,
            text="Cliente (opcional)",
            font=ctk.CTkFont(family=theme.FONTE, size=13, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, sticky="w")

        self.switch_cliente = ctk.CTkSwitch(
            top_line,
            text="Vincular",
            variable=self.vincular_cliente_var,
            command=self._toggle_cliente
        )
        self.switch_cliente.grid(row=0, column=1, sticky="e")

        self.entry_cliente = ctk.CTkEntry(
            self.cliente_box,
            textvariable=self.cliente_busca_var,
            placeholder_text="Buscar cliente por nome/telefone/CPF…",
            height=34,
            fg_color=theme.COR_FUNDO,
            text_color=theme.COR_TEXTO,
            border_color=theme.COR_HOVER,
        )
        self.entry_cliente.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        self.entry_cliente.bind("<KeyRelease>", lambda e: self._atualizar_lista_clientes())

        self.combo_cliente = ctk.CTkComboBox(
            self.cliente_box,
            values=["(nenhum)"],
            command=lambda _: self._selecionar_cliente(),
            state="readonly",
            fg_color=theme.COR_FUNDO,
            button_color=theme.COR_HOVER,
            button_hover_color=theme.COR_SELECIONADO,
            border_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_FUNDO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
        )
        self.combo_cliente.grid(row=2, column=0, padx=12, pady=(0, 8), sticky="ew")

        self.lbl_cliente_sel = ctk.CTkLabel(
            self.cliente_box,
            text="Nenhum cliente vinculado",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC
        )
        self.lbl_cliente_sel.grid(row=3, column=0, padx=12, pady=(0, 10), sticky="w")

        self.btn_remover_cliente = ctk.CTkButton(
            self.cliente_box,
            text="Remover cliente",
            height=32,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._remover_cliente
        )
        self.btn_remover_cliente.grid(row=4, column=0, padx=12, pady=(0, 12), sticky="ew")

        # ===== Dados extras da revenda =====
        self.dados_box = ctk.CTkFrame(box, fg_color=theme.COR_FUNDO, corner_radius=14)
        self.dados_box.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="ew")
        self.dados_box.grid_columnconfigure(0, weight=1)
        self.dados_box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self.dados_box,
            text="Dados da Revenda",
            font=ctk.CTkFont(family=theme.FONTE, size=13, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, columnspan=2, padx=12, pady=(10, 8), sticky="w")

        ctk.CTkLabel(
            self.dados_box, text="Revendedor", text_color=theme.COR_TEXTO
        ).grid(row=1, column=0, padx=12, pady=(0, 4), sticky="w")

        self.combo_revendedor = ctk.CTkComboBox(
            self.dados_box,
            values=["(nenhum)"],
            state="readonly",
            fg_color=theme.COR_FUNDO,
            button_color=theme.COR_HOVER,
            button_hover_color=theme.COR_SELECIONADO,
            border_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_FUNDO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
        )
        self.combo_revendedor.grid(row=2, column=0, padx=12, pady=(0, 8), sticky="ew")
        self._carregar_revendedores_combo()

        ctk.CTkLabel(
            self.dados_box, text="Data/Hora", text_color=theme.COR_TEXTO
        ).grid(row=1, column=1, padx=12, pady=(0, 4), sticky="w")

        self.entry_data = ctk.CTkEntry(
            self.dados_box,
            height=34,
            fg_color=theme.COR_FUNDO,
            text_color=theme.COR_TEXTO,
            border_color=theme.COR_HOVER,
        )
        self.entry_data.grid(row=2, column=1, padx=12, pady=(0, 8), sticky="ew")
        self.entry_data.insert(0, datetime.now().strftime("%d/%m/%Y %H:%M"))

        ctk.CTkLabel(
            self.dados_box, text="Pagamento", text_color=theme.COR_TEXTO
        ).grid(row=3, column=0, padx=12, pady=(0, 4), sticky="w")

        self.combo_pag = ctk.CTkComboBox(
            self.dados_box,
            values=["Dinheiro", "Pix", "Cartão", "Prazo"],
            state="readonly",
            fg_color=theme.COR_FUNDO,
            button_color=theme.COR_HOVER,
            button_hover_color=theme.COR_SELECIONADO,
            border_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_FUNDO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
        )
        self.combo_pag.set("Pix")
        self.combo_pag.grid(row=4, column=0, padx=12, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(
            self.dados_box, text="Desconto (R$)", text_color=theme.COR_TEXTO
        ).grid(row=3, column=1, padx=12, pady=(0, 4), sticky="w")

        self.entry_desconto = ctk.CTkEntry(
            self.dados_box,
            height=34,
            placeholder_text="0,00",
            fg_color=theme.COR_FUNDO,
            text_color=theme.COR_TEXTO,
            border_color=theme.COR_HOVER,
        )
        self.entry_desconto.grid(row=4, column=1, padx=12, pady=(0, 8), sticky="ew")
        self.entry_desconto.insert(0, "0,00")
        self.entry_desconto.bind("<KeyRelease>", lambda e: self._render_carrinho())

        ctk.CTkLabel(
            self.dados_box, text="Observação", text_color=theme.COR_TEXTO
        ).grid(row=5, column=0, columnspan=2, padx=12, pady=(0, 4), sticky="w")

        self.entry_obs = ctk.CTkEntry(
            self.dados_box,
            height=34,
            placeholder_text="Observações da revenda",
            fg_color=theme.COR_FUNDO,
            text_color=theme.COR_TEXTO,
            border_color=theme.COR_HOVER,
        )
        self.entry_obs.grid(row=6, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="ew")

        # ===== Total =====
        self.lbl_total = ctk.CTkLabel(
            box,
            text="Total: R$ 0,00",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO
        )
        self.lbl_total.grid(row=3, column=0, padx=16, pady=(0, 8), sticky="w")

        # ===== Lista carrinho =====
        self.lista_carrinho = ctk.CTkScrollableFrame(box, fg_color="transparent", height=220)
        self.lista_carrinho.grid(row=4, column=0, padx=16, pady=(0, 12), sticky="nsew")

        # ===== Ações =====
        acoes = ctk.CTkFrame(box, fg_color="transparent")
        acoes.grid(row=5, column=0, padx=16, pady=(0, 16), sticky="ew")
        acoes.grid_columnconfigure((0, 1, 2), weight=1)

        self.btn_remover_item = ctk.CTkButton(
            acoes,
            text="Remover último item",
            height=38,
            fg_color=theme.COR_ERRO,
            hover_color=theme.COR_ERRO,
            text_color="#FFFFFF",
            command=self._remover_ultimo_item
        )
        self.btn_remover_item.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.btn_limpar = ctk.CTkButton(
            acoes,
            text="Limpar venda",
            height=38,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._limpar_venda
        )
        self.btn_limpar.grid(row=0, column=1, padx=6, sticky="ew")

        self.btn_finalizar = ctk.CTkButton(
            acoes,
            text="Finalizar revenda",
            height=38,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._finalizar
        )
        self.btn_finalizar.grid(row=0, column=2, padx=(6, 0), sticky="ew")

    # ==========================================================
    # Cliente opcional
    # ==========================================================
    def _toggle_cliente(self):
        ligado = self.vincular_cliente_var.get()
        estado = "normal" if ligado else "disabled"

        self.entry_cliente.configure(state=estado)
        self.combo_cliente.configure(state=estado)
        self.btn_remover_cliente.configure(state=estado)

        if not ligado:
            self._remover_cliente()
        else:
            self._atualizar_lista_clientes()

    def _atualizar_lista_clientes(self):
        termo = self.cliente_busca_var.get().strip().lower()

        opcoes = []
        self._clientes_filtrados = []

        for c in self._listar_clientes_para_vinculo(termo):
            texto = f'{c.get("nome", "")} {c.get("cpf_cnpj", "")} {c.get("telefone", "")}'.lower()
            if not termo or termo in texto:
                opcoes.append(f'{c.get("nome", "")} • {c.get("telefone", "")}')
                self._clientes_filtrados.append(c)

        if not opcoes:
            opcoes = ["(nenhum encontrado)"]
            self._clientes_filtrados = []

        self.combo_cliente.configure(values=opcoes)
        self.combo_cliente.set(opcoes[0])

        if self._clientes_filtrados:
            self._selecionar_cliente()
        else:
            self.cliente_selecionado = None
            self.lbl_cliente_sel.configure(text="Nenhum cliente vinculado")

    def _selecionar_cliente(self):
        if not self._clientes_filtrados:
            return

        escolhido = self.combo_cliente.get()
        idx = 0
        for i, c in enumerate(self._clientes_filtrados):
            if escolhido.startswith(c.get("nome", "")):
                idx = i
                break

        self.cliente_selecionado = self._clientes_filtrados[idx]
        c = self.cliente_selecionado
        self.lbl_cliente_sel.configure(text=f'Vinculado: {c.get("nome", "")} ({c.get("telefone", "")})')

    def _remover_cliente(self):
        self.cliente_selecionado = None
        self.cliente_busca_var.set("")
        self.combo_cliente.configure(values=["(nenhum)"])
        self.combo_cliente.set("(nenhum)")
        self.lbl_cliente_sel.configure(text="Nenhum cliente vinculado")

    # ==========================================================
    # Catálogo
    # ==========================================================
    def _render_catalogo(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        filtro = self.busca_var.get().strip()
        tipo = self.combo_tipo.get()

        grupos = {}
        for p in self._listar_catalogo(filtro, tipo):
            if p.get("ativo") is False:
                continue

            categoria = p.get("categoria", "Outros")
            subgrupo = self._extrair_subgrupo(p)
            grupos.setdefault(categoria, {}).setdefault(subgrupo, []).append(p)

        for tipo_nome, subgrupos in grupos.items():
            tipo_node = self.tree.insert("", "end", text=tipo_nome, open=True)

            for subgrupo_nome, itens in subgrupos.items():
                sub_node = self.tree.insert(tipo_node, "end", text=subgrupo_nome, open=True)

                for p in itens:
                    preco_valor = p.get("preco", 0)
                    try:
                        preco = self._fmt_moeda(float(preco_valor))
                    except Exception:
                        preco = self._fmt_moeda(preco_valor)

                    estoque = self._estoque_disponivel(p)
                    tag = "sem_estoque" if estoque <= 0 else "ok"

                    self.tree.insert(
                        sub_node,
                        "end",
                        text=p["nome"],
                        values=(preco, estoque),
                        tags=(tag, str(p["id"]))
                    )

        self.tree.tag_configure("sem_estoque", foreground="#888888")

    def _adicionar_selecionado(self):
        sel = self.tree.selection()
        if not sel:
            return

        item_id = sel[0]
        tags = self.tree.item(item_id, "tags")

        pid = None
        for t in tags:
            if str(t).isdigit():
                pid = int(t)
                break

        if pid is None:
            return  # clicou em grupo

        produto = self._obter_produto_catalogo(pid)
        if not produto:
            self._render_catalogo()
            return

        if self._estoque_disponivel(produto) <= 0:
            self._render_catalogo()
            return

        existente = next((c for c in self.carrinho if c["id"] == pid), None)
        if existente:
            existente["qtd"] += 1
        else:
            self.carrinho.append({
                "id": pid,
                "nome": produto["nome"],
                "preco": float(produto["preco"]),
                "qtd": 1,
                "categoria": produto.get("categoria", "Outros"),
            })

        self._render_catalogo()
        self._render_carrinho()

    # ==========================================================
    # Carrinho
    # ==========================================================
    def _calcular_total(self):
        subtotal = 0.0
        for item in self.carrinho:
            subtotal += item["preco"] * item["qtd"]

        desconto = float(self._obter_desconto())
        if desconto > subtotal:
            desconto = subtotal

        return subtotal - desconto

    def _render_carrinho(self):
        for w in self.lista_carrinho.winfo_children():
            w.destroy()

        total = 0.0
        for item in self.carrinho:
            total += item["preco"] * item["qtd"]

            linha = ctk.CTkFrame(self.lista_carrinho, fg_color=theme.COR_FUNDO, corner_radius=10)
            linha.pack(fill="x", pady=6)

            ctk.CTkLabel(
                linha,
                text=item["nome"],
                font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
                text_color=theme.COR_TEXTO
            ).pack(anchor="w", padx=10, pady=(8, 0))

            ctk.CTkLabel(
                linha,
                text=f'{item["qtd"]} x {self._fmt_moeda(item["preco"])}',
                font=ctk.CTkFont(family=theme.FONTE, size=12),
                text_color=theme.COR_TEXTO_SEC
            ).pack(anchor="w", padx=10, pady=(0, 8))

        desconto = float(self._obter_desconto())
        if desconto > total:
            desconto = total

        total_final = total - desconto
        self.lbl_total.configure(text=f"Total: {self._fmt_moeda(total_final)}")

    def _remover_ultimo_item(self):
        if not self.carrinho:
            return

        ultimo = self.carrinho[-1]
        ultimo["qtd"] -= 1

        if ultimo["qtd"] <= 0:
            self.carrinho.pop()

        self._render_catalogo()
        self._render_carrinho()

    def _limpar_venda(self):
        self.carrinho = []

        if hasattr(self, "entry_data"):
            self.entry_data.delete(0, "end")
            self.entry_data.insert(0, datetime.now().strftime("%d/%m/%Y %H:%M"))

        if hasattr(self, "entry_desconto"):
            self.entry_desconto.delete(0, "end")
            self.entry_desconto.insert(0, "0,00")

        if hasattr(self, "entry_obs"):
            self.entry_obs.delete(0, "end")

        if hasattr(self, "combo_pag"):
            self.combo_pag.set("Pix")

        if hasattr(self, "combo_revendedor"):
            self._carregar_revendedores_combo()

        if self.vincular_cliente_var.get():
            self._remover_cliente()

        self._render_catalogo()
        self._render_carrinho()

    def _finalizar(self):
        if not self.carrinho:
            messagebox.showwarning("Aviso", "Adicione produtos à revenda.")
            return

        revendedor_nome = self.combo_revendedor.get().strip()
        revendedor_id = self.revendedores_map.get(revendedor_nome)

        if not revendedor_id:
            messagebox.showwarning("Aviso", "Selecione um revendedor válido.")
            return

        data_txt = self.entry_data.get().strip()
        try:
            data_formatada = datetime.strptime(data_txt, "%d/%m/%Y %H:%M").strftime("%d/%m/%Y %H:%M")
        except ValueError:
            messagebox.showerror("Erro", "Data inválida. Use o formato: dd/mm/aaaa hh:mm")
            return

        itens = [{"produto_id": item["id"], "qtd": item["qtd"]} for item in self.carrinho]
        cliente_id = self.cliente_selecionado["id"] if self.cliente_selecionado else None

        kwargs = {
            "tipo": "REVENDA",
            "revendedor_id": revendedor_id,
            "itens": itens,
            "forma_pagamento": self.combo_pag.get(),
            "desconto": self._obter_desconto(),
            "observacao": self.entry_obs.get().strip(),
            "data_venda": data_formatada,
        }
        if cliente_id:
            kwargs["cliente_id"] = cliente_id

        try:
            try:
                self.sistema.registrar_venda(**kwargs)
            except TypeError:
                # fallback caso o serviço ainda não aceite cliente_id
                kwargs.pop("cliente_id", None)
                self.sistema.registrar_venda(**kwargs)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível registrar a revenda.\n\nDetalhes: {e}")
            self._render_catalogo()
            return

        # Se o sistema ainda não tiver listagem de histórico, mantém a aba funcional nesta sessão
        if self._usar_historico_local:
            subtotal = Decimal(str(sum(item["preco"] * item["qtd"] for item in self.carrinho)))
            desconto = self._obter_desconto()
            if desconto > subtotal:
                desconto = subtotal
            total_final = subtotal - desconto

            self._historico_local.append({
                "id": len(self._historico_local) + 1,
                "data": data_formatada,
                "revendedor_nome": revendedor_nome,
                "cliente_nome": self.cliente_selecionado["nome"] if self.cliente_selecionado else None,
                "pagamento": self.combo_pag.get(),
                "qtd_itens": sum(item["qtd"] for item in self.carrinho),
                "total": total_final,
            })

        self._limpar_venda()
        self._atualizar_tree_historico()
        messagebox.showinfo("Sucesso", "Revenda registrada com sucesso.")

    # ==========================================================
    # ABA 2 - Histórico
    # ==========================================================
    def _render_aba_historico(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        self._configurar_treeview()

        filtros = ctk.CTkFrame(parent, fg_color="transparent")
        filtros.grid(row=0, column=0, padx=20, pady=(20, 12), sticky="ew")
        filtros.grid_columnconfigure(5, weight=1)

        ctk.CTkLabel(filtros, text="Mês", text_color=theme.COR_TEXTO).grid(
            row=0, column=0, padx=(0, 8), sticky="w"
        )

        self.combo_filtro_mes = ctk.CTkComboBox(
            filtros,
            values=["Todos", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"],
            width=110,
            state="readonly",
            command=lambda _: self._atualizar_tree_historico(),
            fg_color=theme.COR_FUNDO,
            button_color=theme.COR_HOVER,
            button_hover_color=theme.COR_SELECIONADO,
            border_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_FUNDO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
        )
        self.combo_filtro_mes.grid(row=0, column=1, padx=(0, 16), sticky="w")
        self.combo_filtro_mes.set("Todos")

        ctk.CTkLabel(filtros, text="Ano", text_color=theme.COR_TEXTO).grid(
            row=0, column=2, padx=(0, 8), sticky="w"
        )

        self.combo_filtro_ano = ctk.CTkComboBox(
            filtros,
            values=[],
            width=120,
            state="readonly",
            command=lambda _: self._atualizar_tree_historico(),
            fg_color=theme.COR_FUNDO,
            button_color=theme.COR_HOVER,
            button_hover_color=theme.COR_SELECIONADO,
            border_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_FUNDO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
        )
        self.combo_filtro_ano.grid(row=0, column=3, padx=(0, 16), sticky="w")

        ctk.CTkButton(
            filtros,
            text="Aplicar filtros",
            width=140,
            height=36,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._atualizar_tree_historico
        ).grid(row=0, column=4, sticky="w")

        box = ctk.CTkFrame(parent, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        box.grid_rowconfigure(1, weight=1)
        box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            box,
            text="Histórico de Revendas",
            font=ctk.CTkFont(family=theme.FONTE, size=16, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        tabela_frame = ctk.CTkFrame(box, fg_color="transparent")
        tabela_frame.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        tabela_frame.grid_rowconfigure(0, weight=1)
        tabela_frame.grid_columnconfigure(0, weight=1)

        self.tree_historico = ttk.Treeview(
            tabela_frame,
            style="Geladoce.Treeview",
            columns=("data", "revendedor", "cliente", "itens", "pagamento", "total"),
            show="tree headings"
        )
        self.tree_historico.grid(row=0, column=0, sticky="nsew")

        self.tree_historico.heading("#0", text="ID")
        self.tree_historico.heading("data", text="Data/Hora")
        self.tree_historico.heading("revendedor", text="Revendedor")
        self.tree_historico.heading("cliente", text="Cliente")
        self.tree_historico.heading("itens", text="Itens")
        self.tree_historico.heading("pagamento", text="Pagamento")
        self.tree_historico.heading("total", text="Total")

        self.tree_historico.column("#0", width=60, anchor="center")
        self.tree_historico.column("data", width=140, anchor="center")
        self.tree_historico.column("revendedor", width=170, anchor="w")
        self.tree_historico.column("cliente", width=170, anchor="w")
        self.tree_historico.column("itens", width=70, anchor="center")
        self.tree_historico.column("pagamento", width=110, anchor="center")
        self.tree_historico.column("total", width=110, anchor="center")

        scroll_y = ttk.Scrollbar(tabela_frame, orient="vertical", command=self.tree_historico.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")
        self.tree_historico.configure(yscrollcommand=scroll_y.set)

        self._recarregar_filtro_ano()
        self._atualizar_tree_historico()

    def _recarregar_filtro_ano(self):
        anos = {"Todos"}
        for venda in self._listar_revendas():
            try:
                dt = datetime.strptime(venda["data"], "%d/%m/%Y %H:%M")
                anos.add(str(dt.year))
            except ValueError:
                continue

        lista = ["Todos"] + sorted([a for a in anos if a != "Todos"])
        self.combo_filtro_ano.configure(values=lista)
        self.combo_filtro_ano.set("Todos")

    def _atualizar_tree_historico(self):
        if not hasattr(self, "tree_historico"):
            return

        for item in self.tree_historico.get_children():
            self.tree_historico.delete(item)

        filtro_mes = self.combo_filtro_mes.get()
        filtro_ano = self.combo_filtro_ano.get()

        for venda in sorted(self._listar_revendas(), key=lambda x: str(x.get("data", "")), reverse=True):
            try:
                dt = datetime.strptime(venda["data"], "%d/%m/%Y %H:%M")
            except ValueError:
                continue

            mes = dt.strftime("%m")
            ano = str(dt.year)

            if filtro_mes != "Todos" and mes != filtro_mes:
                continue
            if filtro_ano != "Todos" and ano != filtro_ano:
                continue

            cliente = venda.get("cliente_nome") or "-"

            self.tree_historico.insert(
                "",
                "end",
                text=str(venda.get("id", "")),
                values=(
                    venda.get("data", ""),
                    venda.get("revendedor_nome", "-"),
                    cliente,
                    venda.get("qtd_itens", 0),
                    venda.get("pagamento", "-"),
                    self._fmt_moeda(venda.get("total", 0)),
                ),
            )