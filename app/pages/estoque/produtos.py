import customtkinter as ctk
from app.config.theme import COR_FUNDO, COR_PAINEL, COR_TEXTO, COR_BOTAO, COR_HOVER, FONTE

class PaginaProdutos(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=COR_FUNDO)

        # Layout principal
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Cabeçalho ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=20, pady=20)

        ctk.CTkLabel(
            self.header, 
            text="Catálogo de Produtos", 
            font=ctk.CTkFont(family=FONTE, size=24, weight="bold"),
            text_color=COR_TEXTO
        ).pack(side="left")

        ctk.CTkButton(
            self.header, text="+ Novo Produto",
            fg_color=COR_BOTAO, text_color=COR_TEXTO, hover_color=COR_HOVER,
            height=35
        ).pack(side="right")

        # --- Tabela ---
        self.tabela_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.tabela_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.tabela_frame.grid_columnconfigure((0,1,2,3), weight=1)

        # Cabeçalho da Tabela
        headers = ["ID", "Nome", "Categoria", "Preço", "Qtd."]
        for i, h in enumerate(headers):
            ctk.CTkLabel(self.tabela_frame, text=h, font=ctk.CTkFont(weight="bold")).grid(row=0, column=i, sticky="ew", pady=5)

        # Dados fictícios
        produtos = [
            ("001", "Sorvete Flocos", "Massa", "R$ 12,00", "50"),
            ("002", "Açaí Tradicional", "Açaí", "R$ 15,00", "20"),
            ("003", "Picolé Uva", "Picolé", "R$ 3,00", "100"),
        ]

        for idx, (cod, nome, cat, preco, qtd) in enumerate(produtos, start=1):
            cor = COR_PAINEL if idx % 2 != 0 else "transparent"
            bg = ctk.CTkFrame(self.tabela_frame, fg_color=cor)
            bg.grid(row=idx, column=0, columnspan=5, sticky="ew", pady=2)
            bg.grid_columnconfigure((0,1,2,3,4), weight=1)
            
            valores = [cod, nome, cat, preco, qtd]
            for i, v in enumerate(valores):
                ctk.CTkLabel(bg, text=v).grid(row=0, column=i, pady=8)