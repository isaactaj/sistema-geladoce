import inspect
import customtkinter as ctk

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
    Ex: "inicio", "clientes", "relatorios", etc.

    Regras:
    - Existe apenas 1 instância de SistemaService compartilhada.
    - Toda página que declarar parâmetro 'sistema' no __init__
      recebe automaticamente essa instância.
    - Páginas que não usam 'sistema' continuam funcionando normalmente.
    """

    def __init__(self, master):
        super().__init__(master, fg_color=COR_FUNDO)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.pagina_atual = None
        self.chave_atual = None

        # Instância única compartilhada por toda a aplicação
        self.sistema = SistemaService()

        # Mapeamento de rotas -> classes de páginas
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

        # Começa na página inicial
        self.show("inicio")

    # ======================================================
    # HELPERS
    # ======================================================
    def _pagina_aceita_sistema(self, page_cls) -> bool:
        """
        Verifica de forma segura se a página aceita o parâmetro 'sistema'
        no construtor. Isso evita passar argumento indevido e mantém
        compatibilidade com páginas antigas.
        """
        try:
            assinatura = inspect.signature(page_cls.__init__)
        except (TypeError, ValueError):
            return False

        return "sistema" in assinatura.parameters

    def _criar_pagina(self, chave: str):
        """
        Instancia a página correta.
        Se a classe declarar 'sistema' no __init__, injeta automaticamente
        a instância compartilhada.
        """
        page_cls = self.routes.get(chave)

        if page_cls is None:
            return PlaceholderPage(self, chave=chave)

        kwargs = {}
        if self._pagina_aceita_sistema(page_cls):
            kwargs["sistema"] = self.sistema

        return page_cls(self, **kwargs)

    # ======================================================
    # NAVEGAÇÃO
    # ======================================================
    def show(self, chave: str):
        """Troca a página atual por outra, baseada na chave."""
        if self.pagina_atual is not None:
            self.pagina_atual.destroy()
            self.pagina_atual = None

        self.chave_atual = chave
        self.pagina_atual = self._criar_pagina(chave)
        self.pagina_atual.grid(row=0, column=0, sticky="nsew")

    def refresh(self):
        """
        Recarrega a página atual.
        Útil quando alguma ação externa altera dados e você quer
        reconstruir a tela inteira mantendo a rota atual.
        """
        if self.chave_atual:
            self.show(self.chave_atual)