# -*- coding: utf-8 -*-
from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk
from datetime import datetime, date

try:
    from CTkMessagebox import CTkMessagebox
except Exception:
    CTkMessagebox = None

from app.config import theme


class PaginaRevenda(ctk.CTkFrame):
    """
    Vendas • Revenda (MySQL)
    - Catálogo vem de SistemaService.listar_catalogo()
    - Revendedores vêm de SistemaService.listar_revendedores()
    - Venda final é registrada em SistemaService.registrar_venda(tipo="REVENDA", revendedor_id=...)
      -> baixa estoque / grava vendas + itens / alimenta fechamento via view

    Layout (parecido com Balcão):
    - Esquerda: catálogo com filtros
    - Direita: painel de revendedor + carrinho + pagamento + desconto + observação + data/hora
    """

    def __init__(self, master, sistema=None):
        super().__init__(master, fg_color=theme.COR_FUNDO)
        self.sistema = sistema

        # ---------- layout base ----------
        self.grid_columnconfigure(0, weight=3)  # catálogo
        self.grid_columnconfigure(1, weight=2)  # carrinho
        self.grid_rowconfigure(0, weight=0)  # título
        self.grid_rowconfigure(1, weight=0)  # subtítulo
        self.grid_rowconfigure(2, weight=0)  # filtros
        self.grid_rowconfigure(3, weight=1)  # catálogo cresce

        # ---------- estado ----------
        self.busca_var = ctk.StringVar(value="")
        self.categoria_var = ctk.StringVar(value="Todos")

        self.vincular_revendedor_var = ctk.BooleanVar(value=True)
        self.revendedor_busca_var = ctk.StringVar(value="")
        self.revendedor_selecionado = None
        self._revendedores_filtrados = []

        # carrinho: [{id, nome, preco, qtd, categoria}]
        self.carrinho = []

        # venda/config
        self.forma_pag_var = ctk.StringVar(value="Pix")
        self.desconto_var = ctk.StringVar(value="0,00")
        self.data_var = ctk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        self.hora_var = ctk.StringVar(value=datetime.now().strftime("%H:%M"))

        # UI refs
        self.tree = None
        self._frame_tree = None
        self.lista_carrinho = None

        self.entry_rev_busca = None
        self.combo_rev = None
        self.lbl_rev_sel = None

        self.entry_desconto = None
        self.txt_obs = None

        self.lbl_subtotal = None
        self.lbl_total = None

        # colors fallback
        self._btn_text = getattr(theme, "COR_TEXTO_ALT", theme.COR_TEXTO)

        # UI
        self._topo()
        self._filtros()
        self._catalogo()
        self._painel_direito()

        # render inicial
        self._render_catalogo()
        self._atualizar_lista_revendedores()
        self._render_carrinho()

    # ======================================================
    # HELPERS (serviço)
    # ======================================================
    def _listar_catalogo(self, termo="", categoria="Todos"):
        if not self.sistema:
            return []
        try:
            return self.sistema.listar_catalogo(termo=termo, categoria=categoria)
        except TypeError:
            try:
                return self.sistema.listar_catalogo(termo, categoria)
            except TypeError:
                return self.sistema.listar_catalogo()

    def _listar_revendedores(self, termo=""):
        if not self.sistema:
            return []
        try:
            # preferível: listar_revendedores()
            if hasattr(self.sistema, "listar_revendedores"):
                return self.sistema.listar_revendedores()
            # fallback: listar_clientes(tipo_cliente='Revendedor')
            return self.sistema.listar_clientes(termo=termo, tipo_cliente="Revendedor")
        except TypeError:
            try:
                return self.sistema.listar_clientes(termo)
            except Exception:
                return []

    def _msg(self, title, message, icon="info"):
        if CTkMessagebox is not None:
            CTkMessagebox(title=title, message=message, icon=icon)
        else:
            print(f"[{title}] {message}")

    # ======================================================
    # HELPERS (carrinho/estoque)
    # ======================================================
    def _qtd_no_carrinho(self, produto_id: int) -> int:
        item = next((c for c in self.carrinho if c["id"] == produto_id), None)
        return int(item["qtd"]) if item else 0

    def _estoque_disponivel(self, produto: dict) -> int:
        # estoque real menos o reservado no carrinho
        try:
            estoque_real = int(produto.get("estoque", 0) or 0)
        except Exception:
            estoque_real = 0
        reservado = self._qtd_no_carrinho(int(produto["id"]))
        return max(estoque_real - reservado, 0)

    def _extrair_subgrupo(self, produto: dict) -> str:
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

    def _parse_moeda(self, txt: str) -> float:
        t = str(txt or "").strip()
        if not t:
            return 0.0
        t = t.replace("R$", "").replace(" ", "")
        if "," in t and "." in t:
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", ".")
        try:
            return float(t)
        except Exception:
            return 0.0

    def _fmt_entry(self, valor: float) -> str:
        try:
            v = float(valor)
        except Exception:
            v = 0.0
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _fmt_money(self, valor: float) -> str:
        try:
            return theme.fmt_dinheiro(valor)
        except Exception:
            return f"R$ {self._fmt_entry(valor)}"

    def _get_obs(self) -> str:
        if not self.txt_obs:
            return ""
        return self.txt_obs.get("1.0", "end").strip()

    # ======================================================
    # UI: topo / filtros / catálogo
    # ======================================================
    def _topo(self):
        ctk.CTkLabel(
            self,
            text="Vendas • Revenda",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, columnspan=2, padx=30, pady=(14, 6), sticky="w")

        ctk.CTkLabel(
            self,
            text="Selecione produtos, vincule o revendedor e finalize a venda (estoque baixa automaticamente).",
            font=ctk.CTkFont(family=theme.FONTE, size=13),
            text_color=theme.COR_TEXTO_SEC,
        ).grid(row=1, column=0, columnspan=2, padx=30, pady=(0, 12), sticky="w")

    def _filtros(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=2, column=0, padx=(30, 12), pady=(0, 10), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        self.entry_busca = ctk.CTkEntry(
            frame,
            textvariable=self.busca_var,
            placeholder_text="🔎 Buscar produto…",
            height=36,
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        )
        self.entry_busca.grid(row=0, column=0, sticky="ew")
        self.entry_busca.bind("<KeyRelease>", lambda e: self._render_catalogo())

        self.combo_cat = ctk.CTkComboBox(
            frame,
            values=["Todos", "Sorvete", "Picolé", "Açaí", "Outros"],
            width=160,
            command=lambda _: self._render_catalogo(),
            fg_color=theme.COR_BOTAO,
            button_color=theme.COR_SELECIONADO,
            button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_BOTAO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        )
        self.combo_cat.set("Todos")
        self.combo_cat.grid(row=0, column=1, padx=(10, 0))

    def _catalogo(self):
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=3, column=0, padx=(30, 12), pady=(0, 20), sticky="nsew")
        box.grid_rowconfigure(0, weight=1)
        box.grid_columnconfigure(0, weight=1)

        # ttk style isolado
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Revenda.Treeview",
            font=(theme.FONTE, 12),
            rowheight=30,
            background=theme.COR_BOTAO,
            fieldbackground=theme.COR_BOTAO,
            foreground=theme.COR_TEXTO,
            borderwidth=0,
            relief="flat",
        )
        style.configure(
            "Revenda.Treeview.Heading",
            font=(theme.FONTE, 12, "bold"),
            background=theme.COR_PAINEL,
            foreground=theme.COR_TEXTO,
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Revenda.Treeview",
            background=[("selected", theme.COR_SELECIONADO)],
            foreground=[("selected", theme.COR_TEXTO)],
        )

        self._frame_tree = ctk.CTkFrame(box, fg_color=theme.COR_BOTAO, corner_radius=12)
        self._frame_tree.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self._frame_tree.grid_rowconfigure(0, weight=1)
        self._frame_tree.grid_columnconfigure(0, weight=1)
        self._frame_tree.bind("<Configure>", self._ajustar_colunas_tree)

        self.tree = ttk.Treeview(
            self._frame_tree,
            columns=("preco", "estoque"),
            show="tree headings",
            style="Revenda.Treeview",
        )
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
        self.tree.heading("#0", text="Produto", anchor="w")
        self.tree.heading("preco", text="Preço", anchor="w")
        self.tree.heading("estoque", text="Estoque", anchor="w")

        scroll_y = ttk.Scrollbar(self._frame_tree, orient="vertical", command=self.tree.yview)
        scroll_y.grid(row=0, column=1, sticky="ns", padx=(8, 8), pady=8)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.tag_configure("sem_estoque", foreground="#888888")
        self.tree.bind("<Double-1>", lambda e: self._adicionar_selecionado())

    def _ajustar_colunas_tree(self, event=None):
        if not self.tree or not self._frame_tree:
            return
        w = max(self._frame_tree.winfo_width() - 30, 360)
        c0 = int(w * 0.62)
        c1 = int(w * 0.22)
        c2 = max(w - c0 - c1, 80)
        self.tree.column("#0", width=c0, anchor="w")
        self.tree.column("preco", width=c1, anchor="e")
        self.tree.column("estoque", width=c2, anchor="center")

    # ======================================================
    # UI: painel direito (revendedor + carrinho + finalizar)
    # ======================================================
    def _painel_direito(self):
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=2, column=1, rowspan=2, padx=(12, 30), pady=(0, 20), sticky="nsew")
        box.grid_columnconfigure(0, weight=1)

        # rows
        box.grid_rowconfigure(0, weight=0)  # título
        box.grid_rowconfigure(1, weight=0)  # revendedor
        box.grid_rowconfigure(2, weight=0)  # data/hora + desconto
        box.grid_rowconfigure(3, weight=1)  # carrinho
        box.grid_rowconfigure(4, weight=0)  # pagamento
        box.grid_rowconfigure(5, weight=0)  # obs
        box.grid_rowconfigure(6, weight=0)  # totais + finalizar

        ctk.CTkLabel(
            box,
            text="Revenda",
            font=ctk.CTkFont(family=theme.FONTE, size=16, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        # --- revendedor ---
        self.rev_box = ctk.CTkFrame(box, fg_color=theme.COR_BOTAO, corner_radius=12)
        self.rev_box.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")
        self.rev_box.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self.rev_box, fg_color="transparent")
        header.grid(row=0, column=0, padx=12, pady=(10, 6), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Revendedor",
            font=ctk.CTkFont(family=theme.FONTE, size=13, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, sticky="w")

        self.switch_rev = ctk.CTkSwitch(
            header,
            text="Vincular",
            variable=self.vincular_revendedor_var,
            command=self._toggle_revendedor,
        )
        self.switch_rev.grid(row=0, column=1, sticky="e")

        self.entry_rev_busca = ctk.CTkEntry(
            self.rev_box,
            textvariable=self.revendedor_busca_var,
            placeholder_text="Buscar revendedor por nome/telefone/CPF…",
            height=34,
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        )
        self.entry_rev_busca.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        self.entry_rev_busca.bind("<KeyRelease>", lambda e: self._atualizar_lista_revendedores())

        self.combo_rev = ctk.CTkComboBox(
            self.rev_box,
            values=["(nenhum)"],
            command=lambda _: self._selecionar_revendedor(),
            fg_color=theme.COR_BOTAO,
            button_color=theme.COR_SELECIONADO,
            button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_BOTAO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        )
        self.combo_rev.grid(row=2, column=0, padx=12, pady=(0, 8), sticky="ew")

        self.lbl_rev_sel = ctk.CTkLabel(
            self.rev_box,
            text="Nenhum revendedor vinculado",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC,
        )
        self.lbl_rev_sel.grid(row=3, column=0, padx=12, pady=(0, 12), sticky="w")

        # --- data/hora + desconto ---
        linha_cfg = ctk.CTkFrame(box, fg_color=theme.COR_BOTAO, corner_radius=12)
        linha_cfg.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="ew")
        linha_cfg.grid_columnconfigure(0, weight=1)
        linha_cfg.grid_columnconfigure(1, weight=1)
        linha_cfg.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(linha_cfg, text="Data (AAAA-MM-DD)", text_color=theme.COR_TEXTO).grid(
            row=0, column=0, padx=10, pady=(10, 4), sticky="w"
        )
        ctk.CTkLabel(linha_cfg, text="Hora (HH:MM)", text_color=theme.COR_TEXTO).grid(
            row=0, column=1, padx=10, pady=(10, 4), sticky="w"
        )
        ctk.CTkLabel(linha_cfg, text="Desconto (R$)", text_color=theme.COR_TEXTO).grid(
            row=0, column=2, padx=10, pady=(10, 4), sticky="w"
        )

        ctk.CTkEntry(
            linha_cfg,
            textvariable=self.data_var,
            height=34,
            placeholder_text="2026-03-05",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        ).grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkEntry(
            linha_cfg,
            textvariable=self.hora_var,
            height=34,
            placeholder_text="14:30",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        ).grid(row=1, column=1, padx=10, pady=(0, 10), sticky="ew")

        self.entry_desconto = ctk.CTkEntry(
            linha_cfg,
            textvariable=self.desconto_var,
            height=34,
            placeholder_text="0,00",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        )
        self.entry_desconto.grid(row=1, column=2, padx=10, pady=(0, 10), sticky="ew")
        self.entry_desconto.bind("<KeyRelease>", lambda e: self._render_carrinho())

        # --- carrinho ---
        carr_box = ctk.CTkFrame(box, fg_color="transparent")
        carr_box.grid(row=3, column=0, padx=16, pady=(0, 10), sticky="nsew")
        carr_box.grid_columnconfigure(0, weight=1)
        carr_box.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            carr_box,
            text="Carrinho",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, pady=(0, 8), sticky="w")

        self.lista_carrinho = ctk.CTkScrollableFrame(carr_box, fg_color="transparent", height=260)
        self.lista_carrinho.grid(row=1, column=0, sticky="nsew")

        # --- pagamento ---
        linha_pag = ctk.CTkFrame(box, fg_color=theme.COR_BOTAO, corner_radius=12)
        linha_pag.grid(row=4, column=0, padx=16, pady=(0, 10), sticky="ew")
        linha_pag.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            linha_pag,
            text="Forma de pagamento",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self.combo_pag = ctk.CTkComboBox(
            linha_pag,
            values=["Dinheiro", "Pix", "Cartão", "Cartao", "Prazo"],
            variable=self.forma_pag_var,
            fg_color=theme.COR_BOTAO,
            button_color=theme.COR_SELECIONADO,
            button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_BOTAO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        )
        self.combo_pag.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="w")
        self.combo_pag.set("Pix")

        # --- observação ---
        obs_box = ctk.CTkFrame(box, fg_color=theme.COR_BOTAO, corner_radius=12)
        obs_box.grid(row=5, column=0, padx=16, pady=(0, 10), sticky="ew")
        obs_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            obs_box,
            text="Observação",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self.txt_obs = ctk.CTkTextbox(
            obs_box,
            height=70,
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        )
        self.txt_obs.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="ew")

        # --- totais + finalizar ---
        fim_box = ctk.CTkFrame(box, fg_color="transparent")
        fim_box.grid(row=6, column=0, padx=16, pady=(0, 16), sticky="ew")
        fim_box.grid_columnconfigure(0, weight=1)

        self.lbl_subtotal = ctk.CTkLabel(
            fim_box,
            text="Subtotal: R$ 0,00",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC,
        )
        self.lbl_subtotal.grid(row=0, column=0, sticky="w")

        self.lbl_total = ctk.CTkLabel(
            fim_box,
            text="Total: R$ 0,00",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO,
        )
        self.lbl_total.grid(row=1, column=0, pady=(2, 10), sticky="w")

        btn_finalizar = ctk.CTkButton(
            fim_box,
            text="Finalizar revenda",
            height=40,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._finalizar_revenda,
        )
        btn_finalizar.grid(row=2, column=0, sticky="ew")

    # ======================================================
    # Revendedor: toggle/lista/seleção
    # ======================================================
    def _toggle_revendedor(self):
        ligado = self.vincular_revendedor_var.get()
        estado = "normal" if ligado else "disabled"
        self.entry_rev_busca.configure(state=estado)
        self.combo_rev.configure(state=estado)

        if not ligado:
            self.revendedor_selecionado = None
            self.revendedor_busca_var.set("")
            self.combo_rev.configure(values=["(nenhum)"])
            self.combo_rev.set("(nenhum)")
            self.lbl_rev_sel.configure(text="Nenhum revendedor vinculado")
        else:
            self._atualizar_lista_revendedores()

    def _atualizar_lista_revendedores(self):
        termo = self.revendedor_busca_var.get().strip().lower()

        opcoes = []
        self._revendedores_filtrados = []

        for c in self._listar_revendedores(""):
            nome = str(c.get("nome", "") or "")
            cpf = str(c.get("cpf_cnpj", "") or c.get("cpf", "") or "")
            tel = str(c.get("telefone", "") or "")
            texto_busca = f"{nome} {cpf} {tel}".lower()

            if (not termo) or (termo in texto_busca):
                opcoes.append(f"{nome} • {tel}")
                self._revendedores_filtrados.append(c)

        if not opcoes:
            opcoes = ["(nenhum encontrado)"]
            self._revendedores_filtrados = []

        self.combo_rev.configure(values=opcoes)
        self.combo_rev.set(opcoes[0])

        if self._revendedores_filtrados:
            self._selecionar_revendedor()
        else:
            self.revendedor_selecionado = None
            self.lbl_rev_sel.configure(text="Nenhum revendedor vinculado")

    def _selecionar_revendedor(self):
        if not self._revendedores_filtrados:
            return

        escolhido = self.combo_rev.get().strip()
        idx = 0
        for i, c in enumerate(self._revendedores_filtrados):
            if escolhido.startswith(str(c.get("nome", ""))):
                idx = i
                break

        self.revendedor_selecionado = self._revendedores_filtrados[idx]
        r = self.revendedor_selecionado
        self.lbl_rev_sel.configure(text=f'Vinculado: {r.get("nome","")} ({r.get("telefone","")})')

    # ======================================================
    # Catálogo: render / adicionar
    # ======================================================
    def _render_catalogo(self):
        if not self.tree:
            return
        for i in self.tree.get_children():
            self.tree.delete(i)

        termo = self.busca_var.get().strip()
        cat = self.combo_cat.get().strip()

        produtos = self._listar_catalogo(termo=termo, categoria=cat)

        # agrupa categoria -> subgrupo
        grupos: Dict[str, Dict[str, List[dict]]] = {}
        for p in produtos:
            categoria = p.get("categoria", "Outros")
            subgrupo = self._extrair_subgrupo(p)
            grupos.setdefault(categoria, {}).setdefault(subgrupo, []).append(p)

        for categoria, subgrupos in grupos.items():
            node_cat = self.tree.insert("", "end", text=categoria, open=True)
            for sub, itens in subgrupos.items():
                node_sub = self.tree.insert(node_cat, "end", text=sub, open=True)

                for p in itens:
                    pid = int(p["id"])
                    estoque = self._estoque_disponivel(p)
                    tag = "sem_estoque" if estoque <= 0 else "ok"
                    preco = self._fmt_money(float(p.get("preco", 0) or 0))

                    self.tree.insert(
                        node_sub,
                        "end",
                        text=str(p.get("nome", "")),
                        values=(preco, estoque),
                        tags=(tag, str(pid)),
                    )

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
            return  # clicou em categoria/subgrupo

        # buscar produto no catálogo atual (mais confiável)
        produtos = self._listar_catalogo(termo=self.busca_var.get().strip(), categoria=self.combo_cat.get().strip())
        produto = next((p for p in produtos if int(p["id"]) == pid), None)
        if not produto:
            # recarrega catálogo geral e tenta achar
            produtos = self._listar_catalogo("", "Todos")
            produto = next((p for p in produtos if int(p["id"]) == pid), None)
        if not produto:
            self._render_catalogo()
            return

        disp = self._estoque_disponivel(produto)
        if disp <= 0:
            self._msg("Estoque", "Sem estoque disponível para este produto.", icon="warning")
            self._render_catalogo()
            return

        existente = next((c for c in self.carrinho if c["id"] == pid), None)
        if existente:
            existente["qtd"] += 1
        else:
            self.carrinho.append({
                "id": pid,
                "nome": str(produto.get("nome", "")),
                "preco": float(produto.get("preco", 0) or 0),
                "qtd": 1,
                "categoria": str(produto.get("categoria", "Outros")),
            })

        self._render_catalogo()
        self._render_carrinho()

    # ======================================================
    # Carrinho: render / alterar qtd / remover
    # ======================================================
    def _render_carrinho(self):
        if not self.lista_carrinho:
            return

        for w in self.lista_carrinho.winfo_children():
            w.destroy()

        subtotal = 0.0
        for item in self.carrinho:
            subtotal += float(item["preco"]) * int(item["qtd"])

            linha = ctk.CTkFrame(self.lista_carrinho, fg_color=theme.COR_BOTAO, corner_radius=10)
            linha.pack(fill="x", pady=6)

            linha.grid_columnconfigure(0, weight=1)
            linha.grid_columnconfigure(1, weight=0)

            ctk.CTkLabel(
                linha,
                text=item["nome"],
                font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
                text_color=theme.COR_TEXTO,
                anchor="w",
                justify="left",
            ).grid(row=0, column=0, padx=10, pady=(8, 0), sticky="w")

            ctk.CTkLabel(
                linha,
                text=f'{item["qtd"]} x {self._fmt_money(item["preco"])}',
                font=ctk.CTkFont(family=theme.FONTE, size=12),
                text_color=theme.COR_TEXTO_SEC,
                anchor="w",
            ).grid(row=1, column=0, padx=10, pady=(0, 8), sticky="w")

            # botões qtd
            btns = ctk.CTkFrame(linha, fg_color="transparent")
            btns.grid(row=0, column=1, rowspan=2, padx=10, pady=8, sticky="e")

            ctk.CTkButton(
                btns,
                text="−",
                width=34,
                height=28,
                fg_color=theme.COR_BOTAO,
                hover_color=theme.COR_HOVER,
                text_color=theme.COR_TEXTO,
                border_width=1,
                border_color=theme.COR_HOVER,
                command=lambda pid=item["id"]: self._alterar_qtd(pid, -1),
            ).pack(side="left", padx=(0, 6))

            ctk.CTkButton(
                btns,
                text="+",
                width=34,
                height=28,
                fg_color=theme.COR_BOTAO,
                hover_color=theme.COR_HOVER,
                text_color=theme.COR_TEXTO,
                border_width=1,
                border_color=theme.COR_HOVER,
                command=lambda pid=item["id"]: self._alterar_qtd(pid, +1),
            ).pack(side="left", padx=(0, 6))

            ctk.CTkButton(
                btns,
                text="Remover",
                width=86,
                height=28,
                fg_color=theme.COR_BOTAO,
                hover_color=theme.COR_HOVER,
                text_color=theme.COR_TEXTO,
                border_width=1,
                border_color=theme.COR_HOVER,
                command=lambda pid=item["id"]: self._remover_item(pid),
            ).pack(side="left")

        desconto = self._parse_moeda(self.desconto_var.get())
        if desconto < 0:
            desconto = 0.0
        if desconto > subtotal:
            desconto = subtotal

        total = max(0.0, subtotal - desconto)

        if self.lbl_subtotal:
            self.lbl_subtotal.configure(text=f"Subtotal: {self._fmt_money(subtotal)}")
        if self.lbl_total:
            self.lbl_total.configure(text=f"Total: {self._fmt_money(total)}")

    def _alterar_qtd(self, produto_id: int, delta: int):
        item = next((c for c in self.carrinho if c["id"] == produto_id), None)
        if not item:
            return

        # validar estoque ao aumentar
        if delta > 0:
            # pega produto mais recente do banco (via catálogo completo)
            produto = next((p for p in self._listar_catalogo("", "Todos") if int(p["id"]) == produto_id), None)
            if produto:
                disp = self._estoque_disponivel(produto)
                if disp <= 0:
                    self._msg("Estoque", "Quantidade acima do estoque disponível.", icon="warning")
                    self._render_catalogo()
                    return

        item["qtd"] = int(item["qtd"]) + int(delta)
        if item["qtd"] <= 0:
            self.carrinho = [c for c in self.carrinho if c["id"] != produto_id]

        self._render_catalogo()
        self._render_carrinho()

    def _remover_item(self, produto_id: int):
        self.carrinho = [c for c in self.carrinho if c["id"] != produto_id]
        self._render_catalogo()
        self._render_carrinho()

    # ======================================================
    # Finalizar
    # ======================================================
    def _validar_revenda(self) -> Optional[str]:
        if not self.sistema:
            return "SistemaService não disponível."
        if not self.carrinho:
            return "Carrinho vazio."

        # revendedor obrigatório (regra da revenda)
        if not self.revendedor_selecionado:
            return "Selecione um revendedor."

        # data/hora
        try:
            date.fromisoformat(self.data_var.get().strip())
        except Exception:
            return "Data inválida. Use AAAA-MM-DD."

        hora = self.hora_var.get().strip()
        if hora:
            try:
                h, m = hora.split(":")
                h = int(h); m = int(m)
                if not (0 <= h <= 23 and 0 <= m <= 59):
                    raise ValueError
            except Exception:
                return "Hora inválida. Use HH:MM."

        return None

    def _finalizar_revenda(self):
        err = self._validar_revenda()
        if err:
            self._msg("Validação", err, icon="warning")
            return

        itens = [{"produto_id": int(i["id"]), "qtd": int(i["qtd"])} for i in self.carrinho]
        revendedor_id = int(self.revendedor_selecionado["id"])
        forma = self.forma_pag_var.get().strip() or "Pix"
        desconto = self._parse_moeda(self.desconto_var.get())
        if desconto < 0:
            desconto = 0.0

        # data_venda: junta data + hora para ficar auditável
        data_txt = self.data_var.get().strip()
        hora_txt = self.hora_var.get().strip() or "00:00"
        data_venda = f"{data_txt} {hora_txt}"

        obs = self._get_obs()

        try:
            self.sistema.registrar_venda(
                tipo="REVENDA",
                revendedor_id=revendedor_id,
                itens=itens,
                forma_pagamento=forma,
                desconto=desconto,
                taxa_entrega=0,
                observacao=obs,
                data_venda=data_venda,
            )
        except Exception as e:
            self._msg(
                "Erro ao finalizar",
                f"Não foi possível concluir a revenda.\n\nDetalhes: {e}",
                icon="cancel",
            )
            # recarrega catálogo (estoque pode ter mudado)
            self._render_catalogo()
            return

        # sucesso: limpa
        self.carrinho = []
        self.desconto_var.set("0,00")
        try:
            self.txt_obs.delete("1.0", "end")
        except Exception:
            pass

        self._render_catalogo()
        self._render_carrinho()

        self._msg("Sucesso", "Revenda registrada com sucesso!", icon="check")