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

# ✅ Agora o main depende do núcleo central, não do repo direto
from app.core.sistema import SistemaService


MODO_DESENVOLVIMENTO_SEM_LOGIN = False


class SistemaGeladoce(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("light")

        self.title("Geladoce - Sistema de Gestão")
        self.configure(fg_color=theme.COR_FUNDO)

        self._configurar_icone()

        # ✅ Núcleo do sistema (fonte da verdade)
        self.sistema = SistemaService()

        self.usuario_logado = None

        self.menu = None
        self.area = None
        self.tela_login = None

        # ✅ Admin padrão deve ser garantido DEPOIS do bootstrap do banco (feito antes no main())
        try:
            self.sistema.garantir_admin_padrao()
        except Exception as e:
            # não impede abrir o sistema, mas deixa rastreável
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

        # Layout da tela de login
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        # ✅ Callbacks passam pelo SistemaService (contrato central)
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

        # ✅ Injeta o service no menu e na área sem quebrar __init__ existente
        # (assim páginas conseguem acessar self.master.sistema / self.sistema)
        try:
            setattr(self.menu, "sistema", self.sistema)
        except Exception:
            pass

        try:
            setattr(self.area, "sistema", self.sistema)
        except Exception:
            pass

        # Atualiza usuário no sidebar
        if hasattr(self.menu, "set_usuario_logado"):
            self.menu.set_usuario_logado(self.usuario_logado)
        elif hasattr(self.menu, "atualizar_usuario"):
            self.menu.atualizar_usuario(self.usuario_logado.get("nome", "Usuário"))

        # Atualiza usuário na navegação
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
        """
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
    Inicializa o banco antes de abrir a interface.
    1) Garante que o banco exista.
    2) Garante schema/tabelas/views/seeds.
    3) Testa conexão.
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


def _mostrar_erro_banco_e_sair():
    """
    Mostra popup amigável e encerra.
    Útil porque CTkMessagebox precisa de um root.
    """
    root = ctk.CTk()
    root.withdraw()

    CTkMessagebox(
        title="Banco de dados indisponível",
        message=(
            "Não foi possível iniciar o sistema porque a conexão com o MySQL falhou.\n\n"
            "Checklist rápido:\n"
            "• MySQL está ligado (WAMP/XAMPP)?\n"
            "• DB_HOST/DB_PORT/DB_USER/DB_PASSWORD corretos em app/database/config.py\n"
            f"• Banco '{theme.__dict__.get('DB_NAME', 'geladoce')}' existe ou pode ser criado\n\n"
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