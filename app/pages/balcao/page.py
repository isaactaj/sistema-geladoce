from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk
from datetime import datetime

try:
    from CTkMessagebox import CTkMessagebox
except Exception:
    CTkMessagebox = None

from app.config import theme


class PaginaVendasBalcao(ctk.CTkFrame):
    def __init__(self, master, sistema=None):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        self.sistema = sistema

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)

        # ---------------- estado ----------------
        self.busca_var = ctk.StringVar(value="")
        self.tipo_var = ctk.StringVar(value="Todos")
        self.carrinho = []

        self.vincular_cliente_var = ctk.BooleanVar(value=False)
        self.cliente_busca_var = ctk.StringVar(value="")
        self.cliente_selecionado = None
        self._clientes_filtrados = []

        self.formas_pagamento = self._listar_formas_pagamento()

        # refs
        self.tree = None
        self.lista_carrinho = None
        self.combo_pag = None
        self.lbl_subtotal = None
        self.lbl_total = None
        self.lbl_pontos_previstos = None

        # UI
        self._topo()
        self._filtros()
        self._catalogo()
        self._carrinho_ui()

        self._render_catalogo()
        self._toggle_cliente()

    # =========================================================
    # HELPERS GERAIS
    # =========================================================
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

    def _listar_clientes(self, termo=""):
        try:
            return self.sistema.listar_clientes(termo=termo)
        except TypeError:
            try:
                return self.sistema.listar_clientes(termo)
            except TypeError:
                return self.sistema.listar_clientes()

    def _listar_produtos_catalogo(self, termo="", categoria="Todos"):
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
        produtos = self._listar_produtos_catalogo("", "Todos")
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

    def _fmt_money(self, valor):
        try:
            return theme.fmt_dinheiro(float(valor))
        except Exception:
            return f"R$ {float(valor):.2f}"

    def _calcular_subtotal(self):
        subtotal = 0.0
        for item in self.carrinho:
            subtotal += float(item["preco"]) * int(item["qtd"])
        return subtotal

    def _calcular_pontos_previstos(self, valor_base):
        if not self.cliente_selecionado:
            return 0

        if not self.sistema or not hasattr(self.sistema, "calcular_pontos_rn05"):
            return 0

        tipo = str(self.cliente_selecionado.get("tipo_cliente", "Varejo"))
        try:
            return int(self.sistema.calcular_pontos_rn05(tipo, valor_base))
        except Exception:
            return 0

    def _atualizar_resumo_venda(self):
        subtotal = self._calcular_subtotal()
        total = subtotal
        pontos = self._calcular_pontos_previstos(total)

        if self.lbl_subtotal is not None:
            self.lbl_subtotal.configure(text=f"Subtotal: {self._fmt_money(subtotal)}")

        if self.lbl_total is not None:
            self.lbl_total.configure(text=f"Total: {self._fmt_money(total)}")

        if self.lbl_pontos_previstos is not None:
            if self.cliente_selecionado:
                self.lbl_pontos_previstos.configure(text=f"RN05 prevista: {pontos} ponto(s)")
            else:
                self.lbl_pontos_previstos.configure(text="RN05 prevista: vincule um cliente")

    # =========================================================
    # UI
    # =========================================================
    def _topo(self):
        ctk.CTkLabel(
            self,
            text="Vendas • Balcão",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, columnspan=2, padx=30, pady=(14, 6), sticky="w")

        ctk.CTkLabel(
            self,
            text="Selecione produtos, vincule cliente se desejar e finalize a venda.",
            font=ctk.CTkFont(family=theme.FONTE, size=13),
            text_color=theme.COR_TEXTO_SEC
        ).grid(row=1, column=0, columnspan=2, padx=30, pady=(0, 12), sticky="w")

    def _filtros(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=2, column=0, padx=(30, 12), pady=(0, 10), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        self.entry_busca = ctk.CTkEntry(
            frame,
            textvariable=self.busca_var,
            placeholder_text="🔎 Buscar produto/sabor…",
            height=36
        )
        self.entry_busca.grid(row=0, column=0, sticky="ew")
        self.entry_busca.bind("<KeyRelease>", lambda e: self._render_catalogo())

        self.combo_tipo = ctk.CTkComboBox(
            frame,
            values=["Todos", "Sorvete", "Picolé", "Açaí", "Outros"],
            width=160,
            command=lambda _: self._render_catalogo()
        )
        self.combo_tipo.set("Todos")
        self.combo_tipo.grid(row=0, column=1, padx=(10, 0))

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

        style.configure("Balcao.Treeview", font=(theme.FONTE, 12), rowheight=30)
        style.configure("Balcao.Treeview.Heading", font=(theme.FONTE, 12, "bold"))
        style.map("Balcao.Treeview", background=[("selected", theme.COR_HOVER)])

        self.tree = ttk.Treeview(
            box,
            columns=("preco", "estoque"),
            show="tree headings",
            style="Balcao.Treeview"
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

    def _carrinho_ui(self):
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=2, column=1, rowspan=2, padx=(12, 30), pady=(0, 20), sticky="nsew")
        box.grid_columnconfigure(0, weight=1)

        box.grid_rowconfigure(0, weight=0)
        box.grid_rowconfigure(1, weight=0)
        box.grid_rowconfigure(2, weight=1)
        box.grid_rowconfigure(3, weight=0)

        ctk.CTkLabel(
            box,
            text="Carrinho",
            font=ctk.CTkFont(family=theme.FONTE, size=16, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        # Cliente
        self.cliente_box = ctk.CTkFrame(box, fg_color="#FFFFFF", corner_radius=14)
        self.cliente_box.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")
        self.cliente_box.grid_columnconfigure(0, weight=1)

        top_line = ctk.CTkFrame(self.cliente_box, fg_color="transparent")
        top_line.grid(row=0, column=0, padx=12, pady=(10, 6), sticky="ew")
        top_line.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top_line,
            text="Cliente vinculado",
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
            height=34
        )
        self.entry_cliente.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        self.entry_cliente.bind("<KeyRelease>", lambda e: self._atualizar_lista_clientes())

        self.combo_cliente = ctk.CTkComboBox(
            self.cliente_box,
            values=["(nenhum)"],
            command=lambda _: self._selecionar_cliente()
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
            fg_color="#FFFFFF",
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._remover_cliente
        )
        self.btn_remover_cliente.grid(row=4, column=0, padx=12, pady=(0, 12), sticky="ew")

        # Lista do carrinho
        carrinho_box = ctk.CTkFrame(box, fg_color="transparent")
        carrinho_box.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="nsew")
        carrinho_box.grid_columnconfigure(0, weight=1)
        carrinho_box.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            carrinho_box,
            text="Itens da venda",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, pady=(0, 8), sticky="w")

        self.lista_carrinho = ctk.CTkScrollableFrame(carrinho_box, fg_color="transparent", height=260)
        self.lista_carrinho.grid(row=1, column=0, sticky="nsew")

        # Rodapé limpo
        footer = ctk.CTkFrame(box, fg_color="#FFFFFF", corner_radius=14)
        footer.grid(row=3, column=0, padx=16, pady=(0, 16), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            footer,
            text="Forma de pagamento",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self.combo_pag = ctk.CTkComboBox(
            footer,
            values=self.formas_pagamento,
            width=180
        )
        self.combo_pag.set(self.formas_pagamento[0] if self.formas_pagamento else "Pix")
        self.combo_pag.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")

        self.lbl_subtotal = ctk.CTkLabel(
            footer,
            text="Subtotal: R$ 0,00",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC
        )
        self.lbl_subtotal.grid(row=2, column=0, padx=12, pady=(0, 0), sticky="w")

        self.lbl_total = ctk.CTkLabel(
            footer,
            text="Total: R$ 0,00",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO
        )
        self.lbl_total.grid(row=3, column=0, padx=12, pady=(2, 0), sticky="w")

        self.lbl_pontos_previstos = ctk.CTkLabel(
            footer,
            text="RN05 prevista: vincule um cliente",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC
        )
        self.lbl_pontos_previstos.grid(row=4, column=0, padx=12, pady=(2, 10), sticky="w")

        self.btn_finalizar = ctk.CTkButton(
            footer,
            text="Finalizar venda",
            height=40,
            fg_color="#FFFFFF",
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._finalizar
        )
        self.btn_finalizar.grid(row=5, column=0, padx=12, pady=(0, 12), sticky="ew")

        self._render_carrinho()

    # =========================================================
    # CLIENTE
    # =========================================================
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

        for c in self._listar_clientes(termo):
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
            self._atualizar_resumo_venda()

    def _selecionar_cliente(self):
        if not self._clientes_filtrados:
            return

        escolhido = self.combo_cliente.get()
        idx = 0

        for i, c in enumerate(self._clientes_filtrados):
            nome = c.get("nome", "")
            if escolhido.startswith(nome):
                idx = i
                break

        self.cliente_selecionado = self._clientes_filtrados[idx]
        c = self.cliente_selecionado
        self.lbl_cliente_sel.configure(text=f'Vinculado: {c.get("nome", "")} ({c.get("telefone", "")})')
        self._atualizar_resumo_venda()

    def _remover_cliente(self):
        self.cliente_selecionado = None
        self.cliente_busca_var.set("")
        self.combo_cliente.configure(values=["(nenhum)"])
        self.combo_cliente.set("(nenhum)")
        self.lbl_cliente_sel.configure(text="Nenhum cliente vinculado")
        self._atualizar_resumo_venda()

    # =========================================================
    # CATÁLOGO
    # =========================================================
    def _render_catalogo(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        filtro = self.busca_var.get().strip()
        tipo = self.combo_tipo.get()

        produtos = self._listar_produtos_catalogo(filtro, tipo)

        grupos = {}
        for p in produtos:
            categoria = p.get("categoria", "Outros")
            subgrupo = self._extrair_subgrupo(p)
            grupos.setdefault(categoria, {}).setdefault(subgrupo, []).append(p)

        for tipo_nome, subgrupos in grupos.items():
            tipo_node = self.tree.insert("", "end", text=tipo_nome, open=True)

            for subgrupo_nome, itens in subgrupos.items():
                sub_node = self.tree.insert(tipo_node, "end", text=subgrupo_nome, open=True)

                for p in itens:
                    preco = self._fmt_money(p["preco"])
                    estoque = self._estoque_disponivel(p)
                    tag = "sem_estoque" if estoque <= 0 else "ok"

                    self.tree.insert(
                        sub_node,
                        "end",
                        text=p["nome"],
                        values=(preco, estoque),
                        tags=(tag, str(p["id"]))
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

        produto = self._obter_produto_catalogo(pid)
        if not produto:
            self._render_catalogo()
            return

        estoque_disponivel = self._estoque_disponivel(produto)
        if estoque_disponivel <= 0:
            self._msg("Estoque", "Sem estoque disponível para este produto.", icon="warning")
            self._render_catalogo()
            return

        existente = next((c for c in self.carrinho if c["id"] == pid), None)
        if existente:
            existente["qtd"] += 1
        else:
            self.carrinho.append(
                {
                    "id": pid,
                    "nome": produto["nome"],
                    "preco": float(produto["preco"]),
                    "qtd": 1,
                    "categoria": produto.get("categoria", "Outros")
                }
            )

        self._render_catalogo()
        self._render_carrinho()

    # =========================================================
    # CARRINHO
    # =========================================================
    def _alterar_qtd(self, produto_id, delta):
        item = next((c for c in self.carrinho if c["id"] == produto_id), None)
        if not item:
            return

        if delta > 0:
            produto = self._obter_produto_catalogo(produto_id)
            if produto:
                disp = self._estoque_disponivel(produto)
                if disp <= 0:
                    self._msg("Estoque", "Quantidade acima do estoque disponível.", icon="warning")
                    self._render_catalogo()
                    return

        item["qtd"] += int(delta)

        if item["qtd"] <= 0:
            self.carrinho = [c for c in self.carrinho if c["id"] != produto_id]

        self._render_catalogo()
        self._render_carrinho()

    def _remover_item(self, produto_id):
        self.carrinho = [c for c in self.carrinho if c["id"] != produto_id]
        self._render_catalogo()
        self._render_carrinho()

    def _render_carrinho(self):
        for w in self.lista_carrinho.winfo_children():
            w.destroy()

        for item in self.carrinho:
            total_item = float(item["preco"]) * int(item["qtd"])

            linha = ctk.CTkFrame(self.lista_carrinho, fg_color="#FFFFFF", corner_radius=10)
            linha.pack(fill="x", pady=6)

            linha.grid_columnconfigure(0, weight=1)
            linha.grid_columnconfigure(1, weight=0)

            ctk.CTkLabel(
                linha,
                text=item["nome"],
                font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
                text_color=theme.COR_TEXTO
            ).grid(row=0, column=0, padx=10, pady=(8, 0), sticky="w")

            ctk.CTkLabel(
                linha,
                text=f'Qtd: {item["qtd"]}  |  Unit.: {self._fmt_money(item["preco"])}  |  Item: {self._fmt_money(total_item)}',
                font=ctk.CTkFont(family=theme.FONTE, size=12),
                text_color=theme.COR_TEXTO_SEC
            ).grid(row=1, column=0, padx=10, pady=(0, 8), sticky="w")

            btns = ctk.CTkFrame(linha, fg_color="transparent")
            btns.grid(row=0, column=1, rowspan=2, padx=10, pady=8, sticky="e")

            ctk.CTkButton(
                btns,
                text="−",
                width=34,
                height=28,
                fg_color="#FFFFFF",
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
                fg_color="#FFFFFF",
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
                fg_color="#FFFFFF",
                hover_color=theme.COR_HOVER,
                text_color=theme.COR_TEXTO,
                border_width=1,
                border_color=theme.COR_HOVER,
                command=lambda pid=item["id"]: self._remover_item(pid),
            ).pack(side="left")

        self._atualizar_resumo_venda()

    # =========================================================
    # FINALIZAR
    # =========================================================
    def _finalizar(self):
        if not self.carrinho:
            self._msg("Carrinho", "Adicione ao menos um produto.", icon="warning")
            return

        itens = [{"produto_id": item["id"], "qtd": item["qtd"]} for item in self.carrinho]
        cliente_id = self.cliente_selecionado["id"] if self.cliente_selecionado else None
        pontos_previstos = self._calcular_pontos_previstos(self._calcular_subtotal())

        try:
            self.sistema.registrar_venda(
                tipo="BALCAO",
                cliente_id=cliente_id,
                itens=itens,
                forma_pagamento=self.combo_pag.get(),
                data_venda=self._agora_para_banco(),
            )
        except Exception as e:
            self._msg(
                "Erro ao finalizar",
                f"Não foi possível concluir a venda.\n\nDetalhes: {e}",
                icon="cancel"
            )
            self._render_catalogo()
            return

        self.carrinho = []
        self._remover_cliente()
        self._render_catalogo()
        self._render_carrinho()

        msg = "Venda registrada com sucesso!"
        if pontos_previstos > 0:
            msg += f"\n\nRN05 prevista: {pontos_previstos} ponto(s)"

        self._msg("Sucesso", msg, icon="check")