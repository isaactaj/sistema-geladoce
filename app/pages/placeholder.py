import customtkinter as ctk
from app.config.theme import COR_FUNDO, COR_TEXTO, COR_TEXTO_SEC, FONTE


class PlaceholderPage(ctk.CTkFrame):
    def __init__(self, master, chave="pagina"):
        super().__init__(master, fg_color=COR_FUNDO)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=chave.replace("_", " ").title(),
            font=ctk.CTkFont(family=FONTE, size=24, weight="bold"),
            text_color=COR_TEXTO
        ).grid(row=0, column=0, padx=30, pady=(30, 10), sticky="w")

        ctk.CTkLabel(
            self,
            text="Página em construção…",
            font=ctk.CTkFont(family=FONTE, size=13),
            text_color=COR_TEXTO_SEC
        ).grid(row=1, column=0, padx=30, pady=(0, 20), sticky="w")
