import inspect
import customtkinter as ctk

try:
    from CTkMessagebox import CTkMessagebox
except Exception:
    CTkMessagebox = None

try:
    from tkinter import messagebox
except Exception:
    messagebox = None

from app.config.theme import COR_FUNDO
from app.core.sistema import SistemaService

from app.pages.placeholder import PlaceholderPage
from app.pages.relatorios.page import PaginaAdminRelatorios
from app.pages.funcionarios.page import PaginaFuncionarios
from app.pages.balcao.page import PaginaVendasBalcao
from app.pages.produtos.page import PaginaProdutos
from app.pages.receitas.page import PaginaReceitas
from app.pages.estoque.page import PaginaEstoque
from app.pages.inicio.page import PaginaInicio
from app.pages.revenda.page import PaginaRevenda
from app.pages.fidelidade.page import PaginaFidelidade
from app.pages.fechamento.page import PaginaFechamento
from app.pages.clientes.page import PaginaClientes
from app.pages.fornecedores.page import PaginaFornecedores
from app.pages.servicos.page import PaginaOperacaoCarrinhos


class Navigation(ctk.CTkFrame):
    """
    Área principal (conteúdo). Troca páginas conforme uma chave.

    Revisão:
    - NÃO cria SistemaService novo aqui. Reusa o service do master (main app),
      ou aceita injeção via parâmetro.
    - Injeta 'sistema' e 'usuario_logado' nas páginas se elas aceitarem.
    """

    ROTAS_ADMIN = {"relatorios", "funcionarios"}

    def __init__(self, master, usuario_logado=None, sistema: SistemaService | None = None):
        super().__init__(master, fg_color=COR_FUNDO)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.pagina_atual = None
        self.chave_atual = None

        # ✅ Fonte da verdade: tentar pegar do master; senão usa o parâmetro; senão cria.
        # (Criar aqui é último fallback para não quebrar em testes isolados.)
        self.sistema = (
            getattr(master, "sistema", None)
            or sistema
            or SistemaService()
        )

        self.usuario_logado = usuario_logado or {}

        self.routes = {
            "inicio": PaginaInicio,
            "relatorios": PaginaAdminRelatorios,
            "funcionarios": PaginaFuncionarios,
            "balcao": PaginaVendasBalcao,
            "produtos": PaginaProdutos,
            "receitas": PaginaReceitas,
            "estoque": PaginaEstoque,
            "revenda": PaginaRevenda,
            "fidelidade": PaginaFidelidade,
            "fechamento": PaginaFechamento,
            "clientes": PaginaClientes,
            "fornecedores": PaginaFornecedores,
            "servicos": PaginaOperacaoCarrinhos,
        }

        self.show("inicio")

    # ======================================================
    # USUÁRIO / PERMISSÃO
    # ======================================================
    def set_usuario_logado(self, usuario: dict):
        self.usuario_logado = usuario or {}

        # Se o usuário atual não tem permissão e estava numa rota admin, volta pro início
        if (self.chave_atual in self.ROTAS_ADMIN) and (not self._is_admin()):
            self.show("inicio")

        # Se a página atual quiser reagir a mudança de usuário, permite
        if self.pagina_atual is not None:
            if hasattr(self.pagina_atual, "set_usuario_logado"):
                try:
                    self.pagina_atual.set_usuario_logado(self.usuario_logado)
                except Exception:
                    pass

    def _is_admin(self) -> bool:
        tipo = str(self.usuario_logado.get("tipo_acesso", "")).strip().lower()
        return tipo == "administrador"

    # ======================================================
    # INJEÇÃO (SISTEMA / USUÁRIO)
    # ======================================================
    def _assinatura_init(self, page_cls):
        try:
            return inspect.signature(page_cls.__init__)
        except (TypeError, ValueError):
            return None

    def _pagina_aceita_param(self, page_cls, nome_param: str) -> bool:
        sig = self._assinatura_init(page_cls)
        if sig is None:
            return False
        return nome_param in sig.parameters

    def _criar_pagina(self, chave: str):
        page_cls = self.routes.get(chave)
        if page_cls is None:
            return PlaceholderPage(self, chave=chave)

        kwargs = {}

        # ✅ injeta sistema se a página aceitar
        if self._pagina_aceita_param(page_cls, "sistema"):
            kwargs["sistema"] = self.sistema

        # ✅ injeta usuário logado se a página aceitar
        if self._pagina_aceita_param(page_cls, "usuario_logado"):
            kwargs["usuario_logado"] = self.usuario_logado

        # Se a página aceitar algo tipo "usuario" também, tenta (compatibilidade)
        elif self._pagina_aceita_param(page_cls, "usuario"):
            kwargs["usuario"] = self.usuario_logado

        return page_cls(self, **kwargs)

    # ======================================================
    # UI HELPERS
    # ======================================================
    def _mostrar_acesso_negado(self):
        msg = "Acesso restrito. Apenas administradores podem acessar esta seção."
        if CTkMessagebox is not None:
            CTkMessagebox(title="Acesso negado", message=msg, icon="warning")
        elif messagebox is not None:
            messagebox.showwarning("Acesso negado", msg)
        else:
            print(msg)

    # ======================================================
    # NAVEGAÇÃO
    # ======================================================
    def show(self, chave: str):
        # trava extra (segurança)
        if (chave in self.ROTAS_ADMIN) and (not self._is_admin()):
            self._mostrar_acesso_negado()
            return  # mantém a página atual

        if self.pagina_atual is not None:
            self.pagina_atual.destroy()
            self.pagina_atual = None

        self.chave_atual = chave
        self.pagina_atual = self._criar_pagina(chave)
        self.pagina_atual.grid(row=0, column=0, sticky="nsew")

    def refresh(self):
        if self.chave_atual:
            self.show(self.chave_atual)