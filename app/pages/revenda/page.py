# -*- coding: utf-8 -*-
from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk
from datetime import datetime
from typing import Dict, List, Optional

try:
    from CTkMessagebox import CTkMessagebox
except Exception:
    CTkMessagebox = None

from app.config import theme


class PaginaRevenda(ctk.CTkFrame):
    """
    Vendas • Revenda

    Ajustes desta versão:
    - layout mais limpo e parecido com Balcão
    - sem exibir data/hora na tela
    - sem campo de observação
    - data/hora continuam sendo gravadas automaticamente no banco
    - carrinho com quantidade, +, -, remover
    - revendedor vinculado em destaque
    - preview da RN05
    """

    def __init__(self, master, sistema=None):
        super().__init__(master, fg_color=theme.COR_FUNDO)
        self.sistema = sistema

        # ---------- layout base ----------
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)

        # ---------- estado ----------
        self.busca_var = ctk.StringVar(value="")
        self.categoria_var = ctk.StringVar(value="Todos")

        self.vincular_revendedor_var = ctk.BooleanVar(value=True)
        self.revendedor_busca_var = ctk.StringVar(value="")
        self.revendedor_selecionado = None
        self._revendedores_filtrados = []

        self.carrinho = []

        self.forma_pag_var = ctk.StringVar(value="Pix")
        self.desconto_var = ctk.StringVar(value="0,00")

        self.formas_pagamento = self._listar_formas_pagamento()

        # refs
        self.tree = None
        self._frame_tree = None
        self.lista_carrinho = None
        self.entry_rev_busca = None
        self.combo_rev = None
        self.lbl_rev_sel = None
        self.entry_desconto = None

        self.lbl_subtotal = None
        self.lbl_desconto = None
        self.lbl_total = None
        self.lbl_pontos_previstos = None

        # UI
        self._topo()
        self._filtros()
        self._catalogo()
        self._painel_direito()

        self._render_catalogo()
        self._atualizar_lista_revendedores()
        self._render_carrinho()

    # ======================================================
    # HELPERS GERAIS
    # ======================================================
    def _msg(self, title, message, icon="info"):
        if CTkMessagebox is not None:
            CTkMessagebox(title=title, message=message, icon=icon)
        else:
            print(f"[{title}] {message}")

    def _agora_para_banco(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _listar_formas_pagamento(self):
        padrao = ["Dinheiro", "Pix", "Cartão", "Cartao", "Prazo"]

        if not self.sistema or not hasattr(self.sistema, "listar_formas_pagamento"):
            return padrao

        try:
            formas = self.sistema.listar_formas_pagamento() or []
            codigos = []
            for item in formas:
                codigo = str(item.get("codigo", "")).strip()
                if codigo and codigo not in codigos:
                    codigos.append(codigo)
            return codigos or padrao
        except Exception:
            return padrao

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
            if hasattr(self.sistema, "listar_revendedores"):
                return self.sistema.listar_revendedores()
            return self.sistema.listar_clientes(termo=termo, tipo_cliente="Revendedor")
        except TypeError:
            try:
                return self.sistema.listar_clientes(termo)
            except Exception:
                return []

    def _qtd_no_carrinho(self, produto_id: int) -> int:
        item = next((c for c in self.carrinho if c["id"] == produto_id), None)
        return int(item["qtd"]) if item else 0

    def _estoque_disponivel(self, produto: dict) -> int:
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

    def _fmt_money(self, valor: float) -> str:
        try:
            return theme.fmt_dinheiro(valor)
        except Exception:
            return f"R$ {float(valor):.2f}"

    def _calcular_subtotal(self) -> float:
        subtotal = 0.0
        for item in self.carrinho:
            subtotal += float(item["preco"]) * int(item["qtd"])
        return subtotal

    def _calcular_desconto(self, subtotal: float) -> float:
        desconto = self._parse_moeda(self.desconto_var.get())
        if desconto < 0:
            desconto = 0.0
        if desconto > subtotal:
            desconto = subtotal
        return desconto

    def _calcular_pontos_previstos(self, valor_base: float) -> int:
        if not self.revendedor_selecionado:
            return 0

        if not self.sistema or not hasattr(self.sistema, "calcular_pontos_rn05"):
            return 0

        tipo = str(self.revendedor_selecionado.get("tipo_cliente", "Revendedor"))
        try:
            return int(self.sistema.calcular_pontos_rn05(tipo, valor_base))
        except Exception:
            return 0

    def _atualizar_resumo_venda(self):
        subtotal = self._calcular_subtotal()
        desconto = self._calcular_desconto(subtotal)
        total_produtos = max(0.0, subtotal - desconto)
        pontos = self._calcular_pontos_previstos(total_produtos)

        if self.lbl_subtotal is not None:
            self.lbl_subtotal.configure(text=f"Subtotal: {self._fmt_money(subtotal)}")

        if self.lbl_desconto is not None:
            self.lbl_desconto.configure(text=f"Desconto: {self._fmt_money(desconto)}")

        if self.lbl_total is not None:
            self.lbl_total.configure(text=f"Total: {self._fmt_money(total_produtos)}")

        if self.lbl_pontos_previstos is not None:
            if self.revendedor_selecionado:
                self.lbl_pontos_previstos.configure(text=f"RN05 prevista: {pontos} ponto(s)")
            else:
                self.lbl_pontos_previstos.configure(text="RN05 prevista: selecione um revendedor")

    # ======================================================
    # UI
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
            text="Selecione produtos, vincule o revendedor e finalize a revenda.",
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
        )
        self.entry_busca.grid(row=0, column=0, sticky="ew")
        self.entry_busca.bind("<KeyRelease>", lambda e: self._render_catalogo())

        self.combo_cat = ctk.CTkComboBox(
            frame,
            values=["Todos", "Sorvete", "Picolé", "Açaí", "Outros"],
            width=160,
            command=lambda _: self._render_catalogo(),
        )
        self.combo_cat.set("Todos")
        self.combo_cat.grid(row=0, column=1, padx=(10, 0))

    def _catalogo(self):
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=3, column=0, padx=(30, 12), pady=(0, 20), sticky="nsew")
        box.grid_rowconfigure(0, weight=1)
        box.grid_columnconfigure(0, weight=1)

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

    def _painel_direito(self):
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=2, column=1, rowspan=2, padx=(12, 30), pady=(0, 20), sticky="nsew")
        box.grid_columnconfigure(0, weight=1)

        box.grid_rowconfigure(0, weight=0)
        box.grid_rowconfigure(1, weight=0)
        box.grid_rowconfigure(2, weight=1)
        box.grid_rowconfigure(3, weight=0)

        ctk.CTkLabel(
            box,
            text="Revenda",
            font=ctk.CTkFont(family=theme.FONTE, size=16, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        # Revendedor
        self.rev_box = ctk.CTkFrame(box, fg_color=theme.COR_BOTAO, corner_radius=12)
        self.rev_box.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")
        self.rev_box.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self.rev_box, fg_color="transparent")
        header.grid(row=0, column=0, padx=12, pady=(10, 6), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Revendedor vinculado",
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
        )
        self.entry_rev_busca.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        self.entry_rev_busca.bind("<KeyRelease>", lambda e: self._atualizar_lista_revendedores())

        self.combo_rev = ctk.CTkComboBox(
            self.rev_box,
            values=["(nenhum)"],
            command=lambda _: self._selecionar_revendedor(),
        )
        self.combo_rev.grid(row=2, column=0, padx=12, pady=(0, 8), sticky="ew")

        self.lbl_rev_sel = ctk.CTkLabel(
            self.rev_box,
            text="Nenhum revendedor vinculado",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC,
        )
        self.lbl_rev_sel.grid(row=3, column=0, padx=12, pady=(0, 12), sticky="w")

        # Carrinho
        carr_box = ctk.CTkFrame(box, fg_color="transparent")
        carr_box.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="nsew")
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

        # Rodapé limpo
        footer = ctk.CTkFrame(box, fg_color=theme.COR_BOTAO, corner_radius=12)
        footer.grid(row=3, column=0, padx=16, pady=(0, 16), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            footer,
            text="Forma de pagamento",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self.combo_pag = ctk.CTkComboBox(
            footer,
            values=self.formas_pagamento,
            variable=self.forma_pag_var,
        )
        self.combo_pag.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        self.combo_pag.set(self.formas_pagamento[0] if self.formas_pagamento else "Pix")

        ctk.CTkLabel(
            footer,
            text="Desconto (R$)",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=2, column=0, padx=12, pady=(0, 4), sticky="w")

        self.entry_desconto = ctk.CTkEntry(
            footer,
            textvariable=self.desconto_var,
            height=34,
            placeholder_text="0,00",
        )
        self.entry_desconto.grid(row=3, column=0, padx=12, pady=(0, 8), sticky="ew")
        self.entry_desconto.bind("<KeyRelease>", lambda e: self._render_carrinho())

        self.lbl_subtotal = ctk.CTkLabel(
            footer,
            text="Subtotal: R$ 0,00",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC,
        )
        self.lbl_subtotal.grid(row=4, column=0, padx=12, pady=(0, 0), sticky="w")

        self.lbl_desconto = ctk.CTkLabel(
            footer,
            text="Desconto: R$ 0,00",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC,
        )
        self.lbl_desconto.grid(row=5, column=0, padx=12, pady=(2, 0), sticky="w")

        self.lbl_total = ctk.CTkLabel(
            footer,
            text="Total: R$ 0,00",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO,
        )
        self.lbl_total.grid(row=6, column=0, padx=12, pady=(2, 0), sticky="w")

        self.lbl_pontos_previstos = ctk.CTkLabel(
            footer,
            text="RN05 prevista: selecione um revendedor",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC,
        )
        self.lbl_pontos_previstos.grid(row=7, column=0, padx=12, pady=(2, 10), sticky="w")

        btn_finalizar = ctk.CTkButton(
            footer,
            text="Finalizar revenda",
            height=40,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._finalizar_revenda,
        )
        btn_finalizar.grid(row=8, column=0, padx=12, pady=(0, 12), sticky="ew")

    # ======================================================
    # REVENDEDOR
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
            self._atualizar_resumo_venda()
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
            self._atualizar_resumo_venda()

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
        self._atualizar_resumo_venda()

    # ======================================================
    # CATÁLOGO
    # ======================================================
    def _render_catalogo(self):
        if not self.tree:
            return
        for i in self.tree.get_children():
            self.tree.delete(i)

        termo = self.busca_var.get().strip()
        cat = self.combo_cat.get().strip()

        produtos = self._listar_catalogo(termo=termo, categoria=cat)

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
            return

        produtos = self._listar_catalogo(termo=self.busca_var.get().strip(), categoria=self.combo_cat.get().strip())
        produto = next((p for p in produtos if int(p["id"]) == pid), None)

        if not produto:
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
    # CARRINHO
    # ======================================================
    def _alterar_qtd(self, produto_id: int, delta: int):
        item = next((c for c in self.carrinho if c["id"] == produto_id), None)
        if not item:
            return

        if delta > 0:
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

    def _render_carrinho(self):
        if not self.lista_carrinho:
            return

        for w in self.lista_carrinho.winfo_children():
            w.destroy()

        for item in self.carrinho:
            total_item = float(item["preco"]) * int(item["qtd"])

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
                text=f'Qtd: {item["qtd"]}  |  Unit.: {self._fmt_money(item["preco"])}  |  Item: {self._fmt_money(total_item)}',
                font=ctk.CTkFont(family=theme.FONTE, size=12),
                text_color=theme.COR_TEXTO_SEC,
                anchor="w",
            ).grid(row=1, column=0, padx=10, pady=(0, 8), sticky="w")

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

        self._atualizar_resumo_venda()

    # ======================================================
    # FINALIZAR
    # ======================================================
    def _validar_revenda(self) -> Optional[str]:
        if not self.sistema:
            return "SistemaService não disponível."

        if not self.carrinho:
            return "Carrinho vazio."

        if not self.revendedor_selecionado:
            return "Selecione um revendedor."

        return None

    def _finalizar_revenda(self):
        err = self._validar_revenda()
        if err:
            self._msg("Validação", err, icon="warning")
            return

        itens = [{"produto_id": int(i["id"]), "qtd": int(i["qtd"])} for i in self.carrinho]
        revendedor_id = int(self.revendedor_selecionado["id"])
        forma = self.forma_pag_var.get().strip() or "Pix"

        subtotal = self._calcular_subtotal()
        desconto = self._calcular_desconto(subtotal)
        total_produtos = max(0.0, subtotal - desconto)
        pontos_previstos = self._calcular_pontos_previstos(total_produtos)

        try:
            self.sistema.registrar_venda(
                tipo="REVENDA",
                revendedor_id=revendedor_id,
                itens=itens,
                forma_pagamento=forma,
                desconto=desconto,
                taxa_entrega=0,
                observacao="",
                data_venda=self._agora_para_banco(),
            )
        except Exception as e:
            self._msg(
                "Erro ao finalizar",
                f"Não foi possível concluir a revenda.\n\nDetalhes: {e}",
                icon="cancel",
            )
            self._render_catalogo()
            return

        self.carrinho = []
        self.desconto_var.set("0,00")
        self._render_catalogo()
        self._render_carrinho()

        msg = "Revenda registrada com sucesso!"
        if pontos_previstos > 0:
            msg += f"\n\nRN05 prevista: {pontos_previstos} ponto(s)"

        self._msg("Sucesso", msg, icon="check")