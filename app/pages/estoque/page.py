import customtkinter as ctk
from tkinter import ttk
from CTkMessagebox import CTkMessagebox
from app.config import theme

class PaginaEstoque(ctk.CTkFrame):
    def __init__(self, master, chave="estoque"):
        super().__init__(master, fg_color=theme["COR_FUNDO"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Faz a tabela expandir

        self.produtos = [
        ]
        self.proximo_id = 1

        # --- 1. TÍTULO ---
        ctk.CTkLabel(
            self,
            text="Gerenciamento de Estoque",
            font=ctk.CTkFont(family=theme["FONTE"], size=24, weight="bold"),
            text_color=theme["COR_TEXTO"]
        ).grid(row=0, column=0, padx=30, pady=(30, 20), sticky="w")
        
        
        # # --- 2. FRAME DE BOTÕES DE AÇÕES ---
        self.frame_acoes = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_acoes.grid(row=1, column=0, padx=30, sticky="w")

        self.btn_salvar = ctk.CTkButton(
            self.frame_acoes,
            text="+ Adicionar Produto",
            fg_color=theme["COR_BTN_SALVAR"],
            hover_color=theme["COR_BTN_SALVAR_HOVER"],
            font=ctk.CTkFont(family=theme["FONTE"], size=13, weight="bold"),
            command=self.acao_salvar
        )
        self.btn_salvar.pack(side="left", padx=(0, 10))

        self.btn_editar = ctk.CTkButton(
            self.frame_acoes, 
            text="Editar Produto", 
            fg_color=theme["COR_BTN_EDITAR"],
            hover_color=theme["COR_BTN_EDITAR_HOVER"],
            font=ctk.CTkFont(family=theme["FONTE"], size=13, weight="bold"),
            command=self.acao_editar
        )
        self.btn_editar.pack(side="left", padx=(0, 10)) # O padx=(0, 10) mantém o alinhamento perfeito

        self.btn_excluir = ctk.CTkButton(
            self.frame_acoes,
            text="- Excluir Selecionado",
            fg_color=theme["COR_BTN_EXCLUIR"],
            hover_color=theme["COR_BTN_EXCLUIR_HOVER"],
            font=ctk.CTkFont(family=theme["FONTE"], size=13, weight="bold"),
            command=self.acao_excluir
        )
        self.btn_excluir.pack(side="left", padx=(0, 10))

        self.btn_alerta = ctk.CTkButton(
            self.frame_acoes,
            text="Verificar Alertas",
            fg_color=theme["COR_BTN_ALERTA"],
            hover_color=theme["COR_BTN_ALERTA_HOVER"],
            font=ctk.CTkFont(family=theme["FONTE"], size=13, weight="bold"),
            command=self.acao_alerta
        )
        self.btn_alerta.pack(side="left") # O último botão não precisa de margem à direita

        # --- 3. TABELA (Treeview) ---
        self.frame_tabela = ctk.CTkFrame(self)
        self.frame_tabela.grid(row=2, column=0, padx=30, pady=20, sticky="nsew")
        self.frame_tabela.grid_columnconfigure(0, weight=1)
        self.frame_tabela.grid_rowconfigure(0, weight=1)

        # Estilo para combinar com o tema do CTk
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="white", 
                        foreground="black", 
                        rowheight=30, 
                        fieldbackground="white",
                        font=(theme["FONTE"], 11))
        style.configure("Treeview.Heading", 
                        background="#C1ECFD", 
                        foreground="black", 
                        font=(theme["FONTE"], 12, "bold"))
        style.map('Treeview', background=[('selected', '#14375e')])

        # Colunas da tabela
        colunas = ("id", "nome", "qtd", "status")
        self.tabela = ttk.Treeview(self.frame_tabela, columns=colunas, show="headings", style="Treeview")
        
        # Configuração dos cabeçalhos
        self.tabela.heading("id", text="ID")
        self.tabela.heading("nome", text="Nome do Produto")
        self.tabela.heading("qtd", text="Quantidade")
        self.tabela.heading("status", text="Status")

        # Configuração do tamanho das colunas
        self.tabela.column("id", width=50, anchor="center")
        self.tabela.column("nome", width=300, anchor="w")
        self.tabela.column("qtd", width=100, anchor="center")
        self.tabela.column("status", width=150, anchor="center")

        self.tabela.grid(row=0, column=0, sticky="nsew")

        # Scrollbar para a tabela
        scrollbar = ttk.Scrollbar(self.frame_tabela, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Preenche a tabela inicialmente
        self.atualizar_tabela()

    # ------------------------------------------------
    # LÓGICA DE DADOS E EVENTOS
    # ------------------------------------------------

    def atualizar_tabela(self):
        # Limpa todos os itens atuais da tabela
        for item in self.tabela.get_children():
            self.tabela.delete(item)
            
        # Insere os dados atualizados
        for p in self.produtos:
            self.tabela.insert("", "end", iid=p["id"], values=(p["id"], p["nome"], p["qtd"], p["status"]))

    def acao_salvar(self):
    
        # Cria uma nova janela customizada (Pop-up)
        janela_novo = ctk.CTkToplevel(self)
        janela_novo.title("Novo Produto")
        janela_novo.geometry("400x420")
        janela_novo.attributes("-topmost", True) # Mantém a janela sempre no topo
        janela_novo.focus() # Foca na nova janela

        # --- CAMPO: NOME ---
        ctk.CTkLabel(janela_novo, text="Nome do Produto:").pack(pady=(20, 5), padx=20, anchor="w")
        entry_nome = ctk.CTkEntry(janela_novo, placeholder_text="Ex: Sorvete de Morango")
        entry_nome.pack(fill="x", padx=20)

        # --- CAMPO: QUANTIDADE ---
        ctk.CTkLabel(janela_novo, text="Quantidade:").pack(pady=(10, 5), padx=20, anchor="w")
        entry_qtd = ctk.CTkEntry(janela_novo, placeholder_text="Ex: 50")
        entry_qtd.pack(fill="x", padx=20)

        # --- CAMPO: STATUS ---
        ctk.CTkLabel(janela_novo, text="Status:").pack(pady=(10, 5), padx=20, anchor="w")
        combo_status = ctk.CTkOptionMenu(
            janela_novo, 
            values=["Cheio", "Normal", "Crítico"]
        )
        combo_status.set("Normal") # Status padrão
        combo_status.pack(fill="x", padx=20)

        # --- FUNÇÃO PARA SALVAR OS DADOS DA JANELA ---
        def confirmar_salvamento():
            nome = entry_nome.get()
            qtd_str = entry_qtd.get()
            status = combo_status.get()

            # Validação simples para ver se os campos não estão vazios
            if not nome or not qtd_str:
                CTkMessagebox(title="Erro", message="Por favor, preencha o nome e a quantidade.", icon="cancel")
                return
            
            # Validação para garantir que quantidade é número
            try:
                qtd = int(qtd_str)
            except ValueError:
                CTkMessagebox(title="Erro", message="A quantidade deve ser um número válido!", icon="cancel")
                return

            # Adiciona na "base de dados" simulada
            novo_produto = {
                "id": self.proximo_id, 
                "nome": nome, 
                "qtd": qtd, 
                "status": status
            }
            self.produtos.append(novo_produto)
            self.proximo_id += 1
            
            # Atualiza a visualização da tabela
            self.atualizar_tabela()

            # Fecha a janela de cadastro
            janela_novo.destroy()

            # Mostra mensagem de sucesso
            CTkMessagebox(
                title="Sucesso", 
                message=f"Produto '{nome}' adicionado com sucesso!", 
                icon="check"
            )

        # --- BOTÃO DE SALVAR ---
        btn_salvar = ctk.CTkButton(janela_novo, text="Salvar Produto", command=confirmar_salvamento)
        btn_salvar.pack(pady=30)
    
    def acao_editar(self):
        # Pega o item selecionado na tabela
        selecao = self.tabela.selection()
        
        if not selecao:
            CTkMessagebox(title="Aviso", message="Por favor, selecione um produto na tabela para editar.", icon="warning")
            return

        item_id = int(selecao[0])
        
        # Encontra o produto específico na nossa lista
        produto_atual = next((p for p in self.produtos if p["id"] == item_id), None)
        
        if not produto_atual:
            return

        # Cria a janela de edição
        janela_editar = ctk.CTkToplevel(self)
        janela_editar.title("Editar Produto")
        janela_editar.geometry("400x420")
        janela_editar.attributes("-topmost", True)
        janela_editar.focus()

        # --- CAMPO: NOME ---
        ctk.CTkLabel(janela_editar, text="Nome do Produto:").pack(pady=(20, 5), padx=20, anchor="w")
        entry_nome = ctk.CTkEntry(janela_editar)
        entry_nome.insert(0, produto_atual["nome"]) # Preenche com o nome atual
        entry_nome.pack(fill="x", padx=20)

        # --- CAMPO: QUANTIDADE ---
        ctk.CTkLabel(janela_editar, text="Quantidade:").pack(pady=(10, 5), padx=20, anchor="w")
        entry_qtd = ctk.CTkEntry(janela_editar)
        entry_qtd.insert(0, str(produto_atual["qtd"])) # Preenche com a qtd atual
        entry_qtd.pack(fill="x", padx=20)

        # --- CAMPO: STATUS ---
        ctk.CTkLabel(janela_editar, text="Status:").pack(pady=(10, 5), padx=20, anchor="w")
        combo_status = ctk.CTkOptionMenu(
            janela_editar, 
            values=["Cheio", "Normal", "Crítico"]
        )
        combo_status.set(produto_atual["status"]) # Preenche com o status atual
        combo_status.pack(fill="x", padx=20)

        # --- FUNÇÃO PARA SALVAR A EDIÇÃO ---
        def confirmar_edicao():
            nome = entry_nome.get()
            qtd_str = entry_qtd.get()
            status = combo_status.get()

            if not nome or not qtd_str:
                CTkMessagebox(title="Erro", message="Por favor, preencha o nome e a quantidade.", icon="cancel")
                return
            
            try:
                qtd = int(qtd_str)
            except ValueError:
                CTkMessagebox(title="Erro", message="A quantidade deve ser um número válido!", icon="cancel")
                return

            # Atualiza os dados no dicionário original
            produto_atual["nome"] = nome
            produto_atual["qtd"] = qtd
            produto_atual["status"] = status
            
            self.atualizar_tabela()
            janela_editar.destroy()

            CTkMessagebox(title="Sucesso", message="Produto atualizado com sucesso!", icon="check")

        # --- BOTÃO DE SALVAR EDIÇÃO ---
        btn_salvar_edicao = ctk.CTkButton(janela_editar, text="Salvar Alterações", command=confirmar_edicao)
        btn_salvar_edicao.pack(pady=30)
    
    def acao_excluir(self):
        # Pega o item selecionado na tabela
        selecao = self.tabela.selection()
        
        if not selecao:
            CTkMessagebox(title="Aviso", message="Por favor, selecione um produto na tabela para excluir.", icon="warning")
            return

        item_id = int(selecao[0]) # O IID configurado é o próprio ID do produto

        # Caixa de confirmação
        msg = CTkMessagebox(
            title="Atenção!", 
            message="Tem certeza que deseja excluir o produto selecionado?\nEsta ação não pode ser desfeita.", 
            icon="warning", 
            option_1="Cancelar", 
            option_2="Sim, Excluir"
        )
        
        if msg.get() == "Sim, Excluir":
            # Remove da "base de dados"
            self.produtos = [p for p in self.produtos if p["id"] != item_id]
            
            # --- NOVA LÓGICA: REORGANIZA OS IDs ---
            for index, p in enumerate(self.produtos):
                p["id"] = index + 1 # Começa do 1 novamente e vai subindo
            
            # Atualiza o próximo ID disponível para não haver falhas nas novas adições
            self.proximo_id = len(self.produtos) + 1
            
            # Atualiza a tabela
            self.atualizar_tabela()
            CTkMessagebox(title="Excluído", message="Produto excluído do estoque.", icon="info")

    def acao_alerta(self):
        # Filtra os produtos que estão com o status "Crítico" na nossa lista
        produtos_criticos = [p["nome"] for p in self.produtos if p["status"] == "Crítico"]

        if produtos_criticos:
            # Monta a lista de nomes com quebra de linha e um tracinho
            lista_nomes = "\n- ".join(produtos_criticos)
            
            CTkMessagebox(
                title="Alerta de Estoque Crítico", 
                message=f"Os seguintes produtos estão com status CRÍTICO e precisam de atenção:\n\n- {lista_nomes}", 
                icon="cancel"
            )
        else:
            CTkMessagebox(
                title="Tudo certo", 
                message="Nenhum produto está com o status 'Crítico' no momento.", 
                icon="check"
            )