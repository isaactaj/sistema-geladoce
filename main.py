# main.py
from pathlib import Path

import customtkinter as ctk

# Imports do projeto
from app.config import theme
from app.ui.sidebar import MenuLateral
from app.core.navigation import Navigation
from app.database.connection import (
    criar_banco_se_nao_existir,
    criar_tabelas_se_nao_existirem,
    testar_conexao,
)


class SistemaGeladoce(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ===== Aparência
        ctk.set_appearance_mode("light")

        # ===== Config básica da janela
        self.title("Geladoce - Sistema de Gestão")
        self.geometry("1100x680")
        self.minsize(1100, 680)
        self.configure(fg_color=theme.COR_FUNDO)

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


def iniciar_banco() -> bool:
    """
    Inicializa o banco antes de abrir a interface.
    1. Garante que o banco exista.
    2. Garante que as tabelas existam.
    3. Testa a conexão com o MySQL.
    """
    try:
        criar_banco_se_nao_existir()
        criar_tabelas_se_nao_existirem()  # <- aqui estava faltando chamar a função

        if testar_conexao():
            print("Conexão com MySQL funcionando com sucesso.")
            print("Banco e tabelas prontos.")
            return True

        print("Falha ao conectar com MySQL.")
        return False

    except Exception as e:
        print(f"Erro ao inicializar o banco: {e}")
        return False


def main():
    banco_ok = iniciar_banco()

    if not banco_ok:
        print("O sistema não foi iniciado porque o banco não está pronto.")
        return

    app = SistemaGeladoce()
    app.mainloop()


if __name__ == "__main__":
    main()