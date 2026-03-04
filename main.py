# main.py
from pathlib import Path

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from app.config import theme
from app.ui.sidebar import MenuLateral
from app.core.navigation import Navigation
from app.pages.login.page import TelaLogin
from app.database.connection import (
    criar_banco_se_nao_existir,
    criar_tabelas_se_nao_existirem,
    testar_conexao,
)
from app.database.repositories.usuarios_repository import UsuariosRepository


MODO_DESENVOLVIMENTO_SEM_LOGIN = False


class SistemaGeladoce(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("light")

        self.title("Geladoce - Sistema de Gestão")
        self.configure(fg_color=theme.COR_FUNDO)

        self._configurar_icone()

        self.usuario_logado = None
        self.usuarios_repo = UsuariosRepository()

        self.menu = None
        self.area = None
        self.tela_login = None

        # Bootstrap do usuário admin padrão
        try:
            self.usuarios_repo.garantir_admin_padrao()
        except Exception as e:
            print(f"Aviso ao preparar usuário padrão: {e}")

        if MODO_DESENVOLVIMENTO_SEM_LOGIN:
            usuario_dev = {
                "id": 0,
                "nome": "Modo Desenvolvimento",
                "login": "dev",
                "tipo_acesso": "Administrador",
            }
            self.abrir_sistema(usuario_dev)
        else:
            self.mostrar_login()

    # ======================================================
    # CONFIG JANELA
    # ======================================================
    def _configurar_icone(self):
        raiz = Path(__file__).parent
        assets = raiz / "assets"
        icon_path = assets / "sorvete.ico"

        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

    def _limpar_tela(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.menu = None
        self.area = None
        self.tela_login = None

    # ======================================================
    # FLUXO DE LOGIN
    # ======================================================
    def mostrar_login(self):
        self.usuario_logado = None
        self._limpar_tela()

        self.geometry("980x560")
        self.minsize(920, 520)

        # Layout da tela de login
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self.tela_login = TelaLogin(
            self,
            autenticar_callback=self.usuarios_repo.autenticar,
            criar_usuario_callback=self.usuarios_repo.criar_usuario,
            alterar_senha_callback=self.usuarios_repo.alterar_senha,
            on_login_success=self._ao_login_sucesso,
            on_exit=self.destroy,
        )
        self.tela_login.grid(row=0, column=0, columnspan=2, sticky="nsew")

    def _ao_login_sucesso(self, usuario: dict):
        self.abrir_sistema(usuario)

    def abrir_sistema(self, usuario: dict):
        self.usuario_logado = usuario or {}
        self._limpar_tela()

        self.geometry("1100x680")
        self.minsize(1000, 620)

        # Layout principal
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar
        self.menu = MenuLateral(
            self,
            self.navegar,
            usuario_logado=self.usuario_logado,
        )
        self.menu.grid(row=0, column=0, sticky="ns")

        # Conteúdo
        self.area = Navigation(
            self,
            usuario_logado=self.usuario_logado,
        )
        self.area.grid(row=0, column=1, sticky="nsew")

        # Garante atualização explícita do usuário no sidebar
        if hasattr(self.menu, "set_usuario_logado"):
            self.menu.set_usuario_logado(self.usuario_logado)
        elif hasattr(self.menu, "atualizar_usuario"):
            self.menu.atualizar_usuario(self.usuario_logado.get("nome", "Usuário"))

        # Garante atualização explícita do usuário na navegação
        if hasattr(self.area, "set_usuario_logado"):
            self.area.set_usuario_logado(self.usuario_logado)

        # Ação do botão do rodapé (trocar usuário / logout)
        if hasattr(self.menu, "configurar_acao_usuario"):
            self.menu.configurar_acao_usuario(self.confirmar_troca_usuario)

        # Página inicial
        if hasattr(self.menu, "marcar_ativo"):
            self.menu.marcar_ativo("inicio")

        if self.area is not None:
            self.area.show("inicio")

    def confirmar_troca_usuario(self):
        nome = (self.usuario_logado or {}).get("nome", "usuário atual")

        msg = CTkMessagebox(
            title="Trocar usuário",
            message=f"Deseja sair da conta atual ({nome}) e voltar para a tela de login?",
            icon="question",
            option_1="Cancelar",
            option_2="Sair",
        )

        if msg.get() != "Sair":
            return

        self.mostrar_login()

    # ======================================================
    # NAVEGAÇÃO
    # ======================================================
    def navegar(self, chave: str):
        """
        Navega para a rota informada e só marca como ativa
        se a navegação realmente aconteceu.

        Isso evita, por exemplo, marcar "Administração" no menu
        quando um colaborador tenta abrir uma rota bloqueada.
        """
        if self.area is None:
            return

        rota_anterior = getattr(self.area, "chave_atual", None)

        self.area.show(chave)

        rota_atual = getattr(self.area, "chave_atual", None)

        if self.menu is None or not hasattr(self.menu, "marcar_ativo"):
            return

        # Só marca a rota nova se ela realmente foi aberta
        if rota_atual == chave:
            self.menu.marcar_ativo(chave)
        # Se foi bloqueada, mantém o item anterior marcado
        elif rota_atual:
            self.menu.marcar_ativo(rota_atual)
        elif rota_anterior:
            self.menu.marcar_ativo(rota_anterior)


def iniciar_banco() -> bool:
    """
    Inicializa o banco antes de abrir a interface.
    1. Garante que o banco exista.
    2. Garante que as tabelas existam.
    3. Testa a conexão.
    """
    try:
        criar_banco_se_nao_existir()
        criar_tabelas_se_nao_existirem()

        if testar_conexao():
            print("Conexão com MySQL funcionando com sucesso.")
            return True

        print("Falha ao conectar com MySQL.")
        return False

    except Exception as e:
        print(f"Erro ao inicializar o banco: {e}")
        return False


def main():
    banco_ok = iniciar_banco()

    if not banco_ok:
        print("O sistema não foi iniciado porque a conexão com o banco falhou.")
        return

    app = SistemaGeladoce()
    app.mainloop()


if __name__ == "__main__":
    main()