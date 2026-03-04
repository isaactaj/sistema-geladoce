import customtkinter as ctk
from tkinter import ttk
from CTkMessagebox import CTkMessagebox
from app.config import theme


class PaginaEstoque(ctk.CTkFrame):
    def __init__(self, master, sistema=None):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        self.sistema = sistema

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Tabela na Row 3

        # --- TÍTULO ---
        ctk.CTkLabel(
            self, text="Gerenciamento de Estoque",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=30, pady=(30, 10), sticky="w")

        # --- BARRA DE PESQUISA (Linha 1) ---
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

        # --- BOTÕES DE AÇÃO (Linha 2) ---
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

        # --- TABELA (Linha 3) ---
        self.frame_tabela = ctk.CTkFrame(self)
        self.frame_tabela.grid(row=3, column=0, padx=30, pady=(0, 30), sticky="nsew")
        self.frame_tabela.grid_columnconfigure(0, weight=1)
        self.frame_tabela.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background="white",
            foreground="black",
            rowheight=30,
            fieldbackground="white",
            font=(theme.FONTE, 11)
        )
        style.configure(
            "Treeview.Heading",
            background="#C1ECFD",
            foreground="black",
            font=(theme.FONTE, 12, "bold")
        )
        style.map('Treeview', background=[('selected', '#14375e')])

        colunas = ("id", "nome", "qtd", "status")
        self.tabela = ttk.Treeview(self.frame_tabela, columns=colunas, show="headings", style="Treeview")
        self.tabela.heading("id", text="ID")
        self.tabela.heading("nome", text="Nome do Item")
        self.tabela.heading("qtd", text="Quantidade")
        self.tabela.heading("status", text="Status")
        self.tabela.column("id", width=50, anchor="center")
        self.tabela.column("nome", width=300, anchor="w")
        self.tabela.column("qtd", width=100, anchor="center")
        self.tabela.column("status", width=150, anchor="center")

        self.tabela.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.frame_tabela, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Garante alguns insumos padrão para produção
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

    def _inferir_categoria(self, nome):
        """
        Como a UI do estoque não possui campo de categoria e o estoque agora
        depende de produto_id, itens criados por aqui entram como 'Outros'
        por padrão (especialmente útil para insumos).
        """
        nome_lower = nome.strip().lower()

        if "sorvete" in nome_lower:
            return "Sorvete"
        if "picolé" in nome_lower or "picole" in nome_lower:
            return "Picolé"
        if "açaí" in nome_lower or "acai" in nome_lower:
            return "Açaí"
        return "Outros"

    def _normalizar_nome(self, nome):
        return nome.strip().lower()

    def _buscar_item_por_nome(self, nome):
        nome_ref = self._normalizar_nome(nome)
        for item in self._listar_estoque(""):
            if self._normalizar_nome(item.get("nome", "")) == nome_ref:
                return item
        return None

    def _buscar_item_por_id(self, produto_id):
        for item in self._listar_estoque(""):
            item_id = item.get("produto_id", item.get("id"))
            if item_id == produto_id:
                return item
        return None

    def _garantir_insumos_padrao(self):
        """
        Adiciona insumos básicos de produção apenas se ainda não existirem.
        Eles são criados como produtos para que o estoque seja sempre ligado
        a produto_id.
        """
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

        existentes = {
            self._normalizar_nome(item.get("nome", ""))
            for item in self._listar_estoque("")
        }

        for nome, qtd in insumos_padrao:
            if self._normalizar_nome(nome) in existentes:
                continue

            try:
                novo = self.sistema.salvar_produto(
                    nome=nome,
                    categoria="Outros",
                    preco="0,00"
                )

                produto_id = None
                if isinstance(novo, dict):
                    produto_id = novo.get("id")
                    # Mantém insumo fora do catálogo de vendas, se o serviço usar "ativo"
                    if "ativo" in novo:
                        novo["ativo"] = False

                if produto_id is None:
                    item = self._buscar_item_por_nome(nome)
                    if item:
                        produto_id = item.get("produto_id", item.get("id"))

                if produto_id is not None:
                    self.sistema.definir_estoque(produto_id=produto_id, quantidade=qtd)
            except Exception:
                # Não impede a tela de abrir se o serviço ainda estiver incompleto
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

            self.tabela.insert(
                "",
                "end",
                iid=str(item_id),
                values=(item_id, p.get("nome", ""), qtd, status)
            )

    def acao_buscar(self):
        termo = self.entry_busca.get().strip()
        itens = self.sistema.listar_estoque(termo=termo)
        self.atualizar_tabela(itens)

    def acao_salvar(self):
        janela = ctk.CTkToplevel(self)
        janela.title("Novo Item de Estoque")
        janela.geometry("400x420")
        janela.attributes("-topmost", True)

        ctk.CTkLabel(janela, text="Nome do Item:").pack(pady=(20, 5), padx=20, anchor="w")
        entry_nome = ctk.CTkEntry(janela)
        entry_nome.pack(fill="x", padx=20)

        ctk.CTkLabel(janela, text="Quantidade:").pack(pady=(10, 5), padx=20, anchor="w")
        entry_qtd = ctk.CTkEntry(janela)
        entry_qtd.pack(fill="x", padx=20)

        ctk.CTkLabel(janela, text="Status:").pack(pady=(10, 5), padx=20, anchor="w")
        combo_status = ctk.CTkOptionMenu(janela, values=["Cheio", "Normal", "Crítico"])
        combo_status.pack(fill="x", padx=20)
        combo_status.set("Normal")

        def confirmar():
            nome = entry_nome.get().strip()
            qtd_str = entry_qtd.get().strip()
            _status = combo_status.get()  # Mantido para preservar a UI; o status real vem da quantidade.

            if not nome or not qtd_str:
                CTkMessagebox(title="Erro", message="Preencha os campos.", icon="cancel")
                return

            try:
                qtd = int(qtd_str)
                if qtd < 0:
                    raise ValueError
            except ValueError:
                CTkMessagebox(title="Erro", message="Quantidade deve ser um número inteiro maior ou igual a zero.", icon="cancel")
                return

            try:
                item_existente = self._buscar_item_por_nome(nome)

                if item_existente:
                    produto_id = item_existente.get("produto_id", item_existente.get("id"))
                    qtd_atual = int(item_existente.get("qtd", 0))
                    nova_qtd = qtd_atual + qtd

                    self.sistema.definir_estoque(produto_id=produto_id, quantidade=nova_qtd)

                    mensagem = "Quantidade adicionada ao item existente!"
                else:
                    novo = self.sistema.salvar_produto(
                        nome=nome,
                        categoria=self._inferir_categoria(nome),
                        preco="0,00"
                    )

                    produto_id = None
                    if isinstance(novo, dict):
                        produto_id = novo.get("id")
                        # Itens criados por esta tela tendem a ser insumos/estoque interno
                        if "ativo" in novo:
                            novo["ativo"] = False

                    if produto_id is None:
                        item_criado = self._buscar_item_por_nome(nome)
                        if item_criado:
                            produto_id = item_criado.get("produto_id", item_criado.get("id"))

                    if produto_id is None:
                        raise ValueError("Não foi possível identificar o produto criado no sistema.")

                    self.sistema.definir_estoque(produto_id=produto_id, quantidade=qtd)

                    mensagem = "Item adicionado!"

                self.entry_busca.delete(0, "end")
                self.atualizar_tabela()
                janela.destroy()
                CTkMessagebox(title="Sucesso", message=mensagem, icon="check")

            except Exception as e:
                CTkMessagebox(
                    title="Erro",
                    message=f"Não foi possível salvar o item de estoque.\n\nDetalhes: {e}",
                    icon="cancel"
                )

        ctk.CTkButton(janela, text="Salvar", command=confirmar).pack(pady=30)

    def acao_editar(self):
        sel = self.tabela.selection()
        if not sel:
            CTkMessagebox(title="Aviso", message="Selecione um item.", icon="warning")
            return

        id_item = int(sel[0])
        item_atual = self._buscar_item_por_id(id_item)
        if not item_atual:
            CTkMessagebox(title="Erro", message="Item não encontrado no estoque.", icon="cancel")
            return

        janela = ctk.CTkToplevel(self)
        janela.title("Editar Estoque")
        janela.geometry("400x420")
        janela.attributes("-topmost", True)

        ctk.CTkLabel(janela, text="Nome:").pack(pady=(20, 5), padx=20, anchor="w")
        entry_nome = ctk.CTkEntry(janela)
        entry_nome.insert(0, item_atual.get("nome", ""))
        entry_nome.pack(fill="x", padx=20)

        ctk.CTkLabel(janela, text="Qtd:").pack(pady=(10, 5), padx=20, anchor="w")
        entry_qtd = ctk.CTkEntry(janela)
        entry_qtd.insert(0, str(item_atual.get("qtd", 0)))
        entry_qtd.pack(fill="x", padx=20)

        ctk.CTkLabel(janela, text="Status:").pack(pady=(10, 5), padx=20, anchor="w")
        combo_status = ctk.CTkOptionMenu(janela, values=["Cheio", "Normal", "Crítico"])
        combo_status.set(item_atual.get("status", self._status_por_qtd(item_atual.get("qtd", 0))))
        combo_status.pack(fill="x", padx=20)

        def confirmar():
            nome = entry_nome.get().strip()
            qtd_str = entry_qtd.get().strip()
            _status = combo_status.get()  # Mantido para preservar a UI; o status real vem da quantidade.

            if not nome or not qtd_str:
                CTkMessagebox(title="Erro", message="Preencha os campos.", icon="cancel")
                return

            try:
                qtd = int(qtd_str)
                if qtd < 0:
                    raise ValueError
            except ValueError:
                CTkMessagebox(title="Erro", message="Quantidade deve ser um número inteiro maior ou igual a zero.", icon="cancel")
                return

            try:
                produto = self._obter_produto(id_item)

                if produto:
                    categoria = produto.get("categoria", "Outros")
                    preco = produto.get("preco", "0,00")

                    self.sistema.salvar_produto(
                        nome=nome,
                        categoria=categoria,
                        preco=preco,
                        produto_id=id_item
                    )

                self.sistema.definir_estoque(produto_id=id_item, quantidade=qtd)

                self.atualizar_tabela()
                janela.destroy()
                CTkMessagebox(title="Sucesso", message="Item atualizado!", icon="check")

            except Exception as e:
                CTkMessagebox(
                    title="Erro",
                    message=f"Não foi possível atualizar o item.\n\nDetalhes: {e}",
                    icon="cancel"
                )

        ctk.CTkButton(janela, text="Salvar Alterações", command=confirmar).pack(pady=30)

    def acao_excluir(self):
        sel = self.tabela.selection()
        if not sel:
            CTkMessagebox(title="Aviso", message="Selecione um item.", icon="warning")
            return

        confirmacao = CTkMessagebox(
            title="Excluir",
            message="Remover item?",
            icon="question",
            option_1="Não",
            option_2="Sim"
        )

        if confirmacao.get() != "Sim":
            return

        id_item = int(sel[0])

        try:
            produto = self._obter_produto(id_item)

            # Se for um item interno/inativo (como insumo criado pelo estoque), tenta remover do sistema.
            if produto and produto.get("ativo") is False:
                try:
                    self.sistema.excluir_produto(id_item)
                    mensagem = "Item removido com sucesso!"
                except Exception:
                    self.sistema.definir_estoque(produto_id=id_item, quantidade=0)
                    mensagem = "Estoque zerado com sucesso!"
            else:
                # Para produtos normais, não remove o cadastro: apenas zera o estoque.
                self.sistema.definir_estoque(produto_id=id_item, quantidade=0)
                mensagem = "Estoque zerado com sucesso!"

            self.entry_busca.delete(0, "end")
            self.atualizar_tabela()
            CTkMessagebox(title="Sucesso", message=mensagem, icon="check")

        except Exception as e:
            CTkMessagebox(
                title="Erro",
                message=f"Não foi possível excluir/zerar o item.\n\nDetalhes: {e}",
                icon="cancel"
            )

    def acao_alerta(self):
        itens = self._listar_estoque("")
        criticos = [i.get("nome", "") for i in itens if i.get("status", self._status_por_qtd(i.get("qtd", 0))) == "Crítico"]

        if criticos:
            lista = "\n- ".join(criticos)
            CTkMessagebox(title="Alerta", message=f"Itens CRÍTICOS:\n\n- {lista}", icon="cancel")
        else:
            CTkMessagebox(title="OK", message="Nenhum item crítico.", icon="check")