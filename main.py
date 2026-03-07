from pathlib import Path

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

from app.config import theme
from app.ui.sidebar import MenuLateral
from app.core.navigation import Navigation
from app.pages.login.page import TelaLogin

from app.database.connection import testar_conexao
from app.database.config import DB_NAME
from app.core.sistema import SistemaService


MODO_DESENVOLVIMENTO_SEM_LOGIN = False


class SistemaGeladoce(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("light")

        self.title("Geladoce - Sistema de Gestão")
        self.configure(fg_color=theme.COR_FUNDO)

        self._configurar_icone()

        # Núcleo central do sistema
        self.sistema = SistemaService()

        self.usuario_logado = None

        self.menu = None
        self.area = None
        self.tela_login = None

        # Garante o admin padrão apenas no banco já existente
        try:
            self.sistema.garantir_admin_padrao()
        except Exception as e:
            print(f"Aviso ao preparar usuário padrão: {e}")

        if MODO_DESENVOLVIMENTO_SEM_LOGIN:
            usuario_dev = {
                "id": 0,
                "nome": "Modo Desenvolvimento",
                "login": "dev",
                "cpf": "00000000000",
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

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self.tela_login = TelaLogin(
            self,
            autenticar_callback=self.sistema.autenticar,
            criar_usuario_callback=self.sistema.criar_usuario,
            alterar_senha_callback=self.sistema.alterar_senha,
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

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.menu = MenuLateral(
            self,
            self.navegar,
            usuario_logado=self.usuario_logado,
        )
        self.menu.grid(row=0, column=0, sticky="ns")

        self.area = Navigation(
            self,
            usuario_logado=self.usuario_logado,
        )
        self.area.grid(row=0, column=1, sticky="nsew")

        try:
            setattr(self.menu, "sistema", self.sistema)
        except Exception:
            pass

        try:
            setattr(self.area, "sistema", self.sistema)
        except Exception:
            pass

        if hasattr(self.menu, "set_usuario_logado"):
            self.menu.set_usuario_logado(self.usuario_logado)
        elif hasattr(self.menu, "atualizar_usuario"):
            self.menu.atualizar_usuario(self.usuario_logado.get("nome", "Usuário"))

        if hasattr(self.area, "set_usuario_logado"):
            self.area.set_usuario_logado(self.usuario_logado)

        if hasattr(self.menu, "configurar_acao_usuario"):
            self.menu.configurar_acao_usuario(self.confirmar_troca_usuario)

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
        if self.area is None:
            return

        rota_anterior = getattr(self.area, "chave_atual", None)

        self.area.show(chave)

        rota_atual = getattr(self.area, "chave_atual", None)

        if self.menu is None or not hasattr(self.menu, "marcar_ativo"):
            return

        if rota_atual == chave:
            self.menu.marcar_ativo(chave)
        elif rota_atual:
            self.menu.marcar_ativo(rota_atual)
        elif rota_anterior:
            self.menu.marcar_ativo(rota_anterior)


def iniciar_banco() -> bool:
    """
    Apenas testa a conexão com o banco já existente.
    Não cria banco, não cria tabelas e não executa schema.sql.
    """
    try:
        if testar_conexao():
            print(f"Conexão com MySQL funcionando com sucesso. Banco atual: '{DB_NAME}'.")
            return True

        print(f"Falha ao conectar com MySQL no banco '{DB_NAME}'.")
        return False

    except Exception as e:
        print(f"Erro ao inicializar o banco: {e}")
        return False


def _mostrar_erro_banco_e_sair():
    root = ctk.CTk()
    root.withdraw()

    CTkMessagebox(
        title="Banco de dados indisponível",
        message=(
            "Não foi possível iniciar o sistema porque a conexão com o MySQL falhou.\n\n"
            "Checklist rápido:\n"
            "• MySQL está ligado (WAMP/XAMPP)?\n"
            "• DB_HOST/DB_PORT/DB_USER/DB_PASSWORD corretos em app/database/config.py\n"
            f"• Banco '{DB_NAME}' existe e está acessível\n\n"
            "Depois de corrigir, abra o sistema novamente."
        ),
        icon="cancel",
        option_1="OK",
    )

    try:
        root.destroy()
    except Exception:
        pass


def main():
    banco_ok = iniciar_banco()

    if not banco_ok:
        print("O sistema não foi iniciado porque a conexão com o banco falhou.")
        _mostrar_erro_banco_e_sair()
        return

    app = SistemaGeladoce()
    app.mainloop()


if __name__ == "__main__":
    main()