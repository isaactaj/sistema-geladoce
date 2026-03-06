# app/pages/estoque/page.py
import customtkinter as ctk
from tkinter import ttk
from CTkMessagebox import CTkMessagebox
from app.config import theme


class PaginaEstoque(ctk.CTkFrame):
    def __init__(self, master, sistema=None):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        self.sistema = sistema

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            self, text="Gerenciamento de Estoque",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=30, pady=(30, 10), sticky="w")

        self.frame_busca = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_busca.grid(row=1, column=0, padx=30, pady=(0, 10), sticky="ew")

        self.entry_busca = ctk.CTkEntry(self.frame_busca, placeholder_text="Buscar item no estoque...")
        self.entry_busca.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_busca.bind("<KeyRelease>", lambda e: self.acao_buscar())

        self.btn_buscar = ctk.CTkButton(
            self.frame_busca, text="Buscar", width=100,
            fg_color=theme.COR_BOTAO, hover_color=theme.COR_HOVER,
            command=self.acao_buscar, text_color=theme.COR_TEXTO_ALT
        )
        self.btn_buscar.pack(side="left")

        self.frame_acoes = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_acoes.grid(row=2, column=0, padx=30, pady=(0, 20), sticky="w")

        btn_config = {
            "fg_color": theme.COR_BOTAO,
            "hover_color": theme.COR_HOVER,
            "font": ctk.CTkFont(family=theme.FONTE, size=13, weight="bold"),
            "height": 34,
            "text_color": theme.COR_TEXTO_ALT
        }
        pad_botoes = (0, 10)

        self.btn_salvar = ctk.CTkButton(self.frame_acoes, text="Adicionar Item", command=self.acao_salvar, **btn_config)
        self.btn_salvar.pack(side="left", padx=pad_botoes)

        self.btn_editar = ctk.CTkButton(self.frame_acoes, text="Editar Item", command=self.acao_editar, **btn_config)
        self.btn_editar.pack(side="left", padx=pad_botoes)

        self.btn_excluir = ctk.CTkButton(self.frame_acoes, text="Excluir", command=self.acao_excluir, **btn_config)
        self.btn_excluir.pack(side="left", padx=pad_botoes)

        self.btn_alerta = ctk.CTkButton(self.frame_acoes, text="Verificar Alertas", command=self.acao_alerta, **btn_config)
        self.btn_alerta.pack(side="left", padx=pad_botoes)

        self.frame_tabela = ctk.CTkFrame(self)
        self.frame_tabela.grid(row=3, column=0, padx=30, pady=(0, 30), sticky="nsew")
        self.frame_tabela.grid_columnconfigure(0, weight=1)
        self.frame_tabela.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Estoque.Treeview",
            background="white",
            foreground="black",
            rowheight=30,
            fieldbackground="white",
            font=(theme.FONTE, 11)
        )
        style.configure(
            "Estoque.Treeview.Heading",
            background="#C1ECFD",
            foreground="black",
            font=(theme.FONTE, 12, "bold")
        )
        style.map('Estoque.Treeview', background=[('selected', '#14375e')])

        colunas = ("id", "nome", "qtd", "status", "tipo")
        self.tabela = ttk.Treeview(self.frame_tabela, columns=colunas, show="headings", style="Estoque.Treeview")
        self.tabela.heading("id", text="ID")
        self.tabela.heading("nome", text="Nome do Item")
        self.tabela.heading("qtd", text="Quantidade")
        self.tabela.heading("status", text="Status")
        self.tabela.heading("tipo", text="Tipo")
        self.tabela.column("id", width=60, anchor="center")
        self.tabela.column("nome", width=320, anchor="w")
        self.tabela.column("qtd", width=100, anchor="center")
        self.tabela.column("status", width=140, anchor="center")
        self.tabela.column("tipo", width=120, anchor="center")

        self.tabela.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.frame_tabela, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Garante insumos padrão (agora como INSUMO + INATIVO)
        self._garantir_insumos_padrao()

        self.atualizar_tabela()

    # =========================================================
    # HELPERS
    # =========================================================
    def _listar_estoque(self, termo=""):
        try:
            return self.sistema.listar_estoque(termo=termo)
        except TypeError:
            try:
                return self.sistema.listar_estoque(termo)
            except TypeError:
                return self.sistema.listar_estoque()

    def _obter_produto(self, produto_id):
        try:
            return self.sistema.obter_produto(produto_id)
        except Exception:
            return None

    def _status_por_qtd(self, qtd):
        try:
            qtd = int(qtd)
        except Exception:
            qtd = 0
        if qtd <= 0:
            return "Crítico"
        if qtd <= 10:
            return "Normal"
        return "Cheio"

    def _normalizar_nome(self, nome):
        return str(nome or "").strip().lower()

    def _buscar_item_por_nome(self, nome):
        nome_ref = self._normalizar_nome(nome)
        for item in self._listar_estoque(""):
            if self._normalizar_nome(item.get("nome", "")) == nome_ref:
                return item
        return None

    def _buscar_item_por_id(self, produto_id):
        for item in self._listar_estoque(""):
            item_id = item.get("produto_id", item.get("id"))
            if int(item_id) == int(produto_id):
                return item
        return None

    def _criar_insumo_inativo(self, nome: str):
        """
        Cria um produto como INSUMO e INATIVO, para não aparecer no catálogo de vendas.
        """
        return self.sistema.salvar_produto(
            nome=nome,
            categoria="Outros",
            preco="0,00",
            tipo_item="Insumo",
            eh_insumo=True,
            ativo=False,
        )

    def _garantir_insumos_padrao(self):
        insumos_padrao = [
            ("Açúcar", 25),
            ("Leite Integral", 20),
            ("Leite Condensado", 12),
            ("Creme de Leite", 10),
            ("Liga Neutra", 4),
            ("Emulsificante", 4),
            ("Chocolate em Pó", 6),
            ("Polpa de Morango", 8),
            ("Polpa de Maracujá", 8),
            ("Polpa de Cupuaçu", 8),
            ("Palitos de Picolé", 500),
            ("Sacos para Picolé", 300),
        ]

        existentes = {self._normalizar_nome(item.get("nome", "")) for item in self._listar_estoque("")}

        for nome, qtd in insumos_padrao:
            if self._normalizar_nome(nome) in existentes:
                continue
            try:
                novo = self._criar_insumo_inativo(nome)
                pid = novo.get("id") if isinstance(novo, dict) else None
                if pid is None:
                    item = self._buscar_item_por_nome(nome)
                    pid = item.get("produto_id", item.get("id")) if item else None
                if pid is not None:
                    self.sistema.definir_estoque(produto_id=int(pid), quantidade=int(qtd))
            except Exception:
                pass

    # =========================================================
    # LÓGICA
    # =========================================================
    def atualizar_tabela(self, lista_para_exibir=None):
        if lista_para_exibir is None:
            lista_para_exibir = self._listar_estoque("")

        for item in self.tabela.get_children():
            self.tabela.delete(item)

        for p in lista_para_exibir:
            item_id = p.get("produto_id", p.get("id"))
            qtd = p.get("qtd", 0)
            status = p.get("status", self._status_por_qtd(qtd))

            tipo_item = p.get("tipo_item", "Produto")
            eh_insumo = bool(p.get("eh_insumo", False))
            tipo_txt = "Insumo" if (tipo_item == "Insumo" or eh_insumo) else "Produto"

            self.tabela.insert(
                "",
                "end",
                iid=str(item_id),
                values=(item_id, p.get("nome", ""), qtd, status, tipo_txt)
            )

    def acao_buscar(self):
        termo = self.entry_busca.get().strip()
        itens = self.sistema.listar_estoque(termo=termo)
        self.atualizar_tabela(itens)

    def acao_salvar(self):
        janela = ctk.CTkToplevel(self)
        janela.title("Novo Item de Estoque")
        janela.geometry("420x440")
        janela.attributes("-topmost", True)

        ctk.CTkLabel(janela, text="Nome do Item:").pack(pady=(20, 5), padx=20, anchor="w")
        entry_nome = ctk.CTkEntry(janela)
        entry_nome.pack(fill="x", padx=20)

        ctk.CTkLabel(janela, text="Quantidade:").pack(pady=(10, 5), padx=20, anchor="w")
        entry_qtd = ctk.CTkEntry(janela)
        entry_qtd.pack(fill="x", padx=20)

        ctk.CTkLabel(janela, text="Tipo:").pack(pady=(10, 5), padx=20, anchor="w")
        combo_tipo = ctk.CTkOptionMenu(janela, values=["Insumo", "Produto"])
        combo_tipo.pack(fill="x", padx=20)
        combo_tipo.set("Insumo")

        def confirmar():
            nome = entry_nome.get().strip()
            qtd_str = entry_qtd.get().strip()
            tipo = combo_tipo.get()

            if not nome or not qtd_str:
                CTkMessagebox(title="Erro", message="Preencha os campos.", icon="cancel")
                return

            try:
                qtd = int(qtd_str)
                if qtd < 0:
                    raise ValueError
            except ValueError:
                CTkMessagebox(title="Erro", message="Quantidade deve ser um inteiro >= 0.", icon="cancel")
                return

            try:
                item_existente = self._buscar_item_por_nome(nome)

                if item_existente:
                    pid = int(item_existente.get("produto_id", item_existente.get("id")))
                    qtd_atual = int(item_existente.get("qtd", 0))
                    self.sistema.definir_estoque(produto_id=pid, quantidade=qtd_atual + qtd)
                    msg = "Quantidade adicionada ao item existente!"
                else:
                    if tipo == "Insumo":
                        novo = self._criar_insumo_inativo(nome)
                    else:
                        # Produto interno pode ser ativo=False também, mas deixo ativo=True por padrão
                        novo = self.sistema.salvar_produto(
                            nome=nome,
                            categoria="Outros",
                            preco="0,00",
                            tipo_item="Produto",
                            eh_insumo=False,
                            ativo=True,
                        )
                    pid = novo.get("id") if isinstance(novo, dict) else None
                    if pid is None:
                        item = self._buscar_item_por_nome(nome)
                        pid = int(item.get("produto_id", item.get("id"))) if item else None
                    if pid is None:
                        raise ValueError("Não foi possível identificar o produto criado.")
                    self.sistema.definir_estoque(produto_id=int(pid), quantidade=int(qtd))
                    msg = "Item adicionado!"

                self.entry_busca.delete(0, "end")
                self.atualizar_tabela()
                janela.destroy()
                CTkMessagebox(title="Sucesso", message=msg, icon="check")

            except Exception as e:
                CTkMessagebox(title="Erro", message=f"Falha ao salvar item.\n\n{e}", icon="cancel")

        ctk.CTkButton(janela, text="Salvar", command=confirmar).pack(pady=30)

    def acao_editar(self):
        sel = self.tabela.selection()
        if not sel:
            CTkMessagebox(title="Aviso", message="Selecione um item.", icon="warning")
            return

        pid = int(sel[0])
        item_atual = self._buscar_item_por_id(pid)
        if not item_atual:
            CTkMessagebox(title="Erro", message="Item não encontrado no estoque.", icon="cancel")
            return

        produto = self._obter_produto(pid)

        janela = ctk.CTkToplevel(self)
        janela.title("Editar Estoque")
        janela.geometry("420x460")
        janela.attributes("-topmost", True)

        ctk.CTkLabel(janela, text="Nome:").pack(pady=(20, 5), padx=20, anchor="w")
        entry_nome = ctk.CTkEntry(janela)
        entry_nome.insert(0, item_atual.get("nome", ""))
        entry_nome.pack(fill="x", padx=20)

        ctk.CTkLabel(janela, text="Qtd:").pack(pady=(10, 5), padx=20, anchor="w")
        entry_qtd = ctk.CTkEntry(janela)
        entry_qtd.insert(0, str(item_atual.get("qtd", 0)))
        entry_qtd.pack(fill="x", padx=20)

        # tipo exibido (não muda em edição aqui)
        tipo_item = (produto or {}).get("tipo_item", item_atual.get("tipo_item", "Produto"))
        eh_insumo = bool((produto or {}).get("eh_insumo", item_atual.get("eh_insumo", False)))
        tipo_txt = "Insumo" if (tipo_item == "Insumo" or eh_insumo) else "Produto"

        ctk.CTkLabel(janela, text=f"Tipo atual: {tipo_txt}").pack(pady=(10, 0), padx=20, anchor="w")

        def confirmar():
            nome = entry_nome.get().strip()
            qtd_str = entry_qtd.get().strip()

            if not nome or not qtd_str:
                CTkMessagebox(title="Erro", message="Preencha os campos.", icon="cancel")
                return

            try:
                qtd = int(qtd_str)
                if qtd < 0:
                    raise ValueError
            except ValueError:
                CTkMessagebox(title="Erro", message="Quantidade deve ser um inteiro >= 0.", icon="cancel")
                return

            try:
                if produto:
                    # mantém categoria/preco/tipo/ativo do próprio produto
                    self.sistema.salvar_produto(
                        nome=nome,
                        categoria=produto.get("categoria", "Outros"),
                        preco=str(produto.get("preco", "0,00")),
                        produto_id=pid,
                        tipo_item=produto.get("tipo_item"),
                        eh_insumo=bool(produto.get("eh_insumo", False)),
                        ativo=bool(produto.get("ativo", 1)),
                    )

                self.sistema.definir_estoque(produto_id=pid, quantidade=qtd)

                self.atualizar_tabela()
                janela.destroy()
                CTkMessagebox(title="Sucesso", message="Item atualizado!", icon="check")

            except Exception as e:
                CTkMessagebox(title="Erro", message=f"Falha ao atualizar item.\n\n{e}", icon="cancel")

        ctk.CTkButton(janela, text="Salvar Alterações", command=confirmar).pack(pady=30)

    def acao_excluir(self):
        sel = self.tabela.selection()
        if not sel:
            CTkMessagebox(title="Aviso", message="Selecione um item.", icon="warning")
            return

        confirmacao = CTkMessagebox(
            title="Excluir",
            message="Remover item do estoque?",
            icon="question",
            option_1="Não",
            option_2="Sim"
        )
        if confirmacao.get() != "Sim":
            return

        pid = int(sel[0])
        try:
            produto = self._obter_produto(pid)
            tipo_item = (produto or {}).get("tipo_item", "Produto")
            eh_insumo = bool((produto or {}).get("eh_insumo", False))
            ativo = int((produto or {}).get("ativo", 1))

            # Insumo/inativo -> inativa e zera
            if (tipo_item == "Insumo" or eh_insumo or ativo == 0):
                try:
                    self.sistema.excluir_produto(pid)  # inativa
                except Exception:
                    pass
                self.sistema.definir_estoque(produto_id=pid, quantidade=0)
                msg = "Item inativado/zerado com sucesso!"
            else:
                # Produto de venda -> não apaga cadastro; apenas zera estoque
                self.sistema.definir_estoque(produto_id=pid, quantidade=0)
                msg = "Estoque zerado com sucesso!"

            self.entry_busca.delete(0, "end")
            self.atualizar_tabela()
            CTkMessagebox(title="Sucesso", message=msg, icon="check")

        except Exception as e:
            CTkMessagebox(title="Erro", message=f"Falha ao excluir/zerar.\n\n{e}", icon="cancel")

    def acao_alerta(self):
        itens = self._listar_estoque("")
        criticos = [
            i.get("nome", "")
            for i in itens
            if i.get("status", self._status_por_qtd(i.get("qtd", 0))) == "Crítico"
        ]

        if criticos:
            lista = "\n- ".join(criticos)
            CTkMessagebox(title="Alerta", message=f"Itens CRÍTICOS:\n\n- {lista}", icon="cancel")
        else:
            CTkMessagebox(title="OK", message="Nenhum item crítico.", icon="check")