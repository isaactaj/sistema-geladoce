import customtkinter as ctk
from app.config.theme import (
    COR_FUNDO, COR_PAINEL, COR_TEXTO, COR_TEXTO_SEC, 
    COR_BOTAO, COR_HOVER, FONTE, COR_SUCESSO, COR_ERRO
)

class PaginaReceitas(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=COR_FUNDO)

        # Configuração do Grid Principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) 

        # -------------------------
        # 1. Cabeçalho (Título)
        # -------------------------
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))

        ctk.CTkLabel(
            self.header, text="Estoque • Receitas",
            font=ctk.CTkFont(family=FONTE, size=24, weight="bold"),
            text_color=COR_TEXTO
        ).pack(side="left")

        # -------------------------
        # 2. Barra de Controle
        # -------------------------
        self.controls = ctk.CTkFrame(self, fg_color="transparent")
        self.controls.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 15))

        # Barra de Pesquisa
        self.entry_busca = ctk.CTkEntry(
            self.controls,
            placeholder_text="Buscar receita por nome...",
            width=300,
            height=40,
            fg_color=COR_PAINEL,
            border_width=0,
            text_color=COR_TEXTO
        )
        self.entry_busca.pack(side="left", padx=(0, 10))

        # Botão Buscar
        self.btn_buscar = ctk.CTkButton(
            self.controls, text="🔍", width=40, height=40,
            fg_color=COR_PAINEL, hover_color=COR_HOVER,
            text_color=COR_TEXTO,
            command=self.filtrar_receitas
        )
        self.btn_buscar.pack(side="left")

        # Botão Nova Receita
        self.btn_novo = ctk.CTkButton(
            self.controls, text="+ Nova Receita", height=40,
            fg_color=COR_SUCESSO, hover_color="#1B5E20",
            text_color="white",
            font=ctk.CTkFont(family=FONTE, weight="bold"),
            command=self.adicionar_receita
        )
        self.btn_novo.pack(side="right")

        # -------------------------
        # 3. Tabela de Receitas
        # -------------------------
        self.frame_tabela = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_tabela.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 30))
        
        # Cabeçalho da Tabela
        self.criar_cabecalho_tabela()

        # Área de Rolagem
        self.scroll_tabela = ctk.CTkScrollableFrame(
            self.frame_tabela, 
            fg_color="transparent", 
            corner_radius=0
        )
        self.scroll_tabela.pack(expand=True, fill="both")

        # Mock de dados (Simulação)
        self.dados_receitas = [
            {"id": "001", "nome": "Base Sorvete Nata", "rendimento": "10 Litros", "custo": 45.90},
            {"id": "002", "nome": "Calda de Morango Artesanal", "rendimento": "2.5 Litros", "custo": 18.50},
            {"id": "003", "nome": "Mousse de Maracujá", "rendimento": "15 Unidades", "custo": 22.00},
            {"id": "004", "nome": "Casquinha Crocante", "rendimento": "100 Unidades", "custo": 12.30},
            {"id": "005", "nome": "Ganache de Chocolate", "rendimento": "3 kg", "custo": 55.00},
        ]
        
        self.carregar_tabela()

    def criar_cabecalho_tabela(self):
        header_frame = ctk.CTkFrame(self.frame_tabela, fg_color=COR_PAINEL, height=40, corner_radius=6)
        header_frame.pack(fill="x", pady=(0, 5))

        # Definição das colunas para Receitas
        colunas = [
            ("ID", 0.1), 
            ("NOME DA RECEITA", 0.45), 
            ("RENDIMENTO", 0.2), 
            ("CUSTO EST.", 0.15), 
            ("AÇÕES", 0.1)
        ]

        for i, (col, peso) in enumerate(colunas):
            header_frame.grid_columnconfigure(i, weight=int(peso*100))
            label = ctk.CTkLabel(
                header_frame, 
                text=col, 
                font=ctk.CTkFont(family=FONTE, size=12, weight="bold"),
                text_color=COR_TEXTO_SEC
            )
            label.grid(row=0, column=i, padx=5, pady=8, sticky="w" if i != 4 else "e")

    def carregar_tabela(self, filtro=""):
        for widget in self.scroll_tabela.winfo_children():
            widget.destroy()

        for item in self.dados_receitas:
            if filtro.lower() not in item["nome"].lower() and filtro not in item["id"]:
                continue
            self.criar_linha_tabela(item)

    def criar_linha_tabela(self, item):
        row = ctk.CTkFrame(self.scroll_tabela, fg_color=COR_BOTAO, corner_radius=6)
        row.pack(fill="x", pady=2)

        pesos = [10, 45, 20, 15, 10]
        for i, p in enumerate(pesos):
            row.grid_columnconfigure(i, weight=p)

        # 1. ID
        ctk.CTkLabel(row, text=f"#{item['id']}", text_color=COR_TEXTO_SEC, font=ctk.CTkFont(family=FONTE, size=12)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # 2. Nome
        ctk.CTkLabel(row, text=item['nome'], text_color=COR_TEXTO, font=ctk.CTkFont(family=FONTE, weight="bold")).grid(row=0, column=1, padx=5, sticky="w")
        
        # 3. Rendimento
        ctk.CTkLabel(row, text=item['rendimento'], text_color=COR_TEXTO).grid(row=0, column=2, padx=5, sticky="w")
        
        # 4. Custo
        ctk.CTkLabel(row, text=f"R$ {item['custo']:.2f}", text_color=COR_TEXTO).grid(row=0, column=3, padx=5, sticky="w")

        # 5. Ações
        frame_acoes = ctk.CTkFrame(row, fg_color="transparent")
        frame_acoes.grid(row=0, column=4, padx=5, sticky="e")

        # Botão Editar (Lápis)
        btn_edit = ctk.CTkButton(frame_acoes, text="✎", width=30, height=30, fg_color=COR_PAINEL, text_color=COR_TEXTO, hover_color=COR_HOVER, command=lambda: print(f"Editar {item['id']}"))
        btn_edit.pack(side="left", padx=2)
        
        # Botão Excluir (X)
        btn_del = ctk.CTkButton(frame_acoes, text="✖", width=30, height=30, fg_color=COR_PAINEL, text_color=COR_ERRO, hover_color="#FFCDD2", command=lambda: print(f"Deletar {item['id']}"))
        btn_del.pack(side="left", padx=2)

    def filtrar_receitas(self):
        termo = self.entry_busca.get()
        self.carregar_tabela(termo)

    def adicionar_receita(self):
        print("Abrir modal de nova receita...")