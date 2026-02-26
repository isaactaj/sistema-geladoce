# main.py
import customtkinter as ctk
from pathlib import Path
from app.config import theme
from app.ui.sidebar import MenuLateral
from app.core.navigation import Navigation


class SistemaGeladoce(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ===== Config básica da janela
        self.title("Geladoce - Sistema de Gestão")
        self.geometry("1100x680")

        self.configure(fg_color=theme.COR_FUNDO)  # cor de fundo da janela principal
        # ===== Assets (ícone)
        raiz = Path(__file__).parent
        assets = raiz / "assets"
        icon_path = assets / "sorvete.ico"

        # Evita quebrar em SO que não suporta .ico
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        # ===== Aparência
        ctk.set_appearance_mode("light")

        # ===== Layout principal (sidebar + conteúdo)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)  # coluna do conteúdo cresce

        # Sidebar
        self.menu = MenuLateral(self, self.navegar)
        self.menu.grid(row=0, column=0, sticky="ns")

        # Conteúdo (navegação)
        self.area = Navigation(self)
        self.area.grid(row=0, column=1, sticky="nsew")

        # Simulação de usuário logado (depois você liga ao login)
        self.menu.atualizar_usuario("Augusto Junior")

        # Página inicial
        self.menu.marcar_ativo("inicio")
        self.area.show("inicio")

    def navegar(self, chave: str):
        """Chamado pela sidebar quando o usuário clica em um item."""
        self.area.show(chave)
        self.menu.marcar_ativo(chave)


def main():
    app = SistemaGeladoce()
    app.mainloop()


if __name__ == "__main__":
    main()
