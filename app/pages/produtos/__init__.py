import customtkinter as ctk
from app.config.theme import (
    COR_FUNDO, COR_PAINEL, COR_TEXTO, COR_TEXTO_SEC, 
    COR_BOTAO, COR_HOVER, COR_SELECIONADO, FONTE, COR_SUCESSO, COR_ERRO
)
    
class PaginaProdutos(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=COR_FUNDO)

        # Configuração do Grid Principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # A tabela expande

        # -------------------------
        # 1. Cabeçalho (Título)
        # -------------------------
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))

        ctk.CTkLabel(
            self.header, text="Estoque • Produtos",
            font=ctk.CTkFont(family=FONTE, size=24, weight="bold"),
            text_color=COR_TEXTO
        ).pack(side="left")

        # -------------------------
        # 2. Barra de Controle (Pesquisa + Botão Adicionar)
        # -------------------------
        self.controls = ctk.CTkFrame(self, fg_color="transparent")
        self.controls.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 15))

        # Barra de Pesquisa
        self.entry_busca = ctk.CTkEntry(
            self.controls,
            placeholder_text="Buscar produto por nome ou ID...",
            width=300,
            height=40,
            fg_color=COR_PAINEL,
            border_width=0,
            text_color=COR_TEXTO
        )
        self.entry_busca.pack(side="left", padx=(0, 10))

        # Botão Buscar (Opcional, pois pode ser busca dinâmica)
        self.btn_buscar = ctk.CTkButton(
            self.controls, text="🔍", width=40, height=40,
            fg_color=COR_PAINEL, hover_color=COR_HOVER,
            text_color=COR_TEXTO,
            command=self.filtrar_produtos
        )
        self.btn_buscar.pack(side="left")

        # Botão Novo Produto
        self.btn_novo = ctk.CTkButton(
            self.controls, text="+ Novo Produto", height=40,
            fg_color=COR_SUCESSO, hover_color="#1B5E20", # Um verde mais escuro no hover
            text_color="white",
            font=ctk.CTkFont(family=FONTE, weight="bold"),
            command=self.adicionar_produto
        )
        self.btn_novo.pack(side="right")

        # -------------------------
        # 3. Tabela de Produtos (Do zero)
        # -------------------------
        self.frame_tabela = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_tabela.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 30))
        
        # Cabeçalho da Tabela
        self.criar_cabecalho_tabela()

        # Área de Rolagem (Linhas)
        self.scroll_tabela = ctk.CTkScrollableFrame(
            self.frame_tabela, 
            fg_color="transparent", 
            corner_radius=0
        )
        self.scroll_tabela.pack(expand=True, fill="both")

        # Mock de dados (Simulando banco de dados)
        self.dados_produtos = [
            {"id": "001", "nome": "Sorvete Chocolate 1L", "cat": "Sorvete", "preco": 25.00, "qtd": 12},
            {"id": "002", "nome": "Picolé Limão", "cat": "Picolé", "preco": 3.50, "qtd": 50},
            {"id": "003", "nome": "Açaí Copo 500ml", "cat": "Açaí", "preco": 18.00, "qtd": 8},
            {"id": "004", "nome": "Granola Pacote", "cat": "Insumo", "preco": 12.90, "qtd": 5},
            {"id": "005", "nome": "Calda Morango", "cat": "Outros", "preco": 8.50, "qtd": 20},
        ]
        
        self.carregar_tabela()

    def criar_cabecalho_tabela(self):
        # Frame do cabeçalho
        header_frame = ctk.CTkFrame(self.frame_tabela, fg_color=COR_PAINEL, height=40, corner_radius=6)
        header_frame.pack(fill="x", pady=(0, 5))

        # Definição das colunas (Titulo, Tamanho relativo)
        colunas = [
            ("ID", 0.1), 
            ("PRODUTO", 0.4), 
            ("CATEGORIA", 0.2), 
            ("PREÇO", 0.15), 
            ("ESTOQUE", 0.15),
            ("AÇÕES", 0.1) # Espaço para botões
        ]

        # Configurar grid do cabeçalho
        for i, (col, peso) in enumerate(colunas):
            header_frame.grid_columnconfigure(i, weight=int(peso*100))
            label = ctk.CTkLabel(
                header_frame, 
                text=col, 
                font=ctk.CTkFont(family=FONTE, size=12, weight="bold"),
                text_color=COR_TEXTO_SEC
            )
            label.grid(row=0, column=i, padx=5, pady=8, sticky="w" if i != 5 else "e")

    def carregar_tabela(self, filtro=""):
        # Limpar tabela atual
        for widget in self.scroll_tabela.winfo_children():
            widget.destroy()

        # Renderizar linhas
        for produto in self.dados_produtos:
            # Filtro simples
            if filtro.lower() not in produto["nome"].lower() and filtro not in produto["id"]:
                continue

            self.criar_linha_tabela(produto)

    def criar_linha_tabela(self, item):
        row = ctk.CTkFrame(self.scroll_tabela, fg_color=COR_BOTAO, corner_radius=6)
        row.pack(fill="x", pady=2)

        # Configuração de colunas idêntica ao cabeçalho
        pesos = [10, 40, 20, 15, 15, 10]
        for i, p in enumerate(pesos):
            row.grid_columnconfigure(i, weight=p)

        # 1. ID
        ctk.CTkLabel(row, text=f"#{item['id']}", text_color=COR_TEXTO_SEC, font=ctk.CTkFont(family=FONTE, size=12)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # 2. Nome (Destaque)
        ctk.CTkLabel(row, text=item['nome'], text_color=COR_TEXTO, font=ctk.CTkFont(family=FONTE, weight="bold")).grid(row=0, column=1, padx=5, sticky="w")
        
        # 3. Categoria
        ctk.CTkLabel(row, text=item['cat'], text_color=COR_TEXTO).grid(row=0, column=2, padx=5, sticky="w")
        
        # 4. Preço
        ctk.CTkLabel(row, text=f"R$ {item['preco']:.2f}", text_color=COR_TEXTO).grid(row=0, column=3, padx=5, sticky="w")

        # 5. Estoque (Com cor condicional)
        cor_estoque = COR_SUCESSO if item['qtd'] > 10 else COR_ERRO
        ctk.CTkLabel(row, text=f"{item['qtd']} un", text_color=cor_estoque, font=ctk.CTkFont(weight="bold")).grid(row=0, column=4, padx=5, sticky="w")

        # 6. Ações (Botões)
        frame_acoes = ctk.CTkFrame(row, fg_color="transparent")
        frame_acoes.grid(row=0, column=5, padx=5, sticky="e")

        btn_edit = ctk.CTkButton(frame_acoes, text="✎", width=30, height=30, fg_color=COR_PAINEL, text_color=COR_TEXTO, hover_color=COR_HOVER, command=lambda: print(f"Editar {item['id']}"))
        btn_edit.pack(side="left", padx=2)
        
        btn_del = ctk.CTkButton(frame_acoes, text="✖", width=30, height=30, fg_color=COR_PAINEL, text_color=COR_ERRO, hover_color="#FFCDD2", command=lambda: print(f"Deletar {item['id']}"))
        btn_del.pack(side="left", padx=2)

    def filtrar_produtos(self):
        termo = self.entry_busca.get()
        self.carregar_tabela(termo)

    def adicionar_produto(self):
        print("Abrir modal de cadastro aqui...")
        # Aqui você pode abrir um CTkToplevel ou trocar de tela