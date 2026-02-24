import customtkinter as ctk
from app.config.theme import COR_FUNDO, COR_PAINEL, COR_TEXTO, COR_BOTAO, COR_HOVER, FONTE

class PaginaReceitas(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=COR_FUNDO)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Cabeçalho ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=20, pady=20)

        ctk.CTkLabel(
            self.header, 
            text="Receitas & Fichas Técnicas", 
            font=ctk.CTkFont(family=FONTE, size=24, weight="bold"),
            text_color=COR_TEXTO
        ).pack(side="left")

        ctk.CTkButton(
            self.header, text="+ Nova Receita",
            fg_color=COR_BOTAO, text_color=COR_TEXTO, hover_color=COR_HOVER,
            height=35
        ).pack(side="right")

        # --- Lista de Cards ---
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.scroll.grid_columnconfigure((0, 1), weight=1, pad=15)

        itens = [
            ("Base Gelato Nata", "45 min", "Alto custo"),
            ("Calda Chocolate", "15 min", "Custo baixo"),
            ("Chantilly Caseiro", "10 min", "Validade curta"),
            ("Xarope de Guaraná", "60 min", "Industrial"),
        ]

        for i, (nome, tempo, obs) in enumerate(itens):
            self.criar_card(i, nome, tempo, obs)

    def criar_card(self, i, nome, tempo, obs):
        row, col = divmod(i, 2)
        card = ctk.CTkFrame(self.scroll, fg_color=COR_PAINEL)
        card.grid(row=row, column=col, sticky="ew", pady=10, padx=5)

        ctk.CTkLabel(card, text=nome, font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkLabel(card, text=f"⏱ {tempo} • {obs}", text_color="gray").pack(anchor="w", padx=15, pady=(0, 15))