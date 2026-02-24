import customtkinter as ctk

from app.config.theme import COR_FUNDO
from app.pages.placeholder import PlaceholderPage
from app.pages.relatorios.page import PaginaAdminRelatorios
from app.pages.funcionarios.page import PaginaFuncionarios
from app.pages.balcao.page import PaginaVendasBalcao
from app.pages.estoque.produtos import PaginaProdutos
from app.pages.estoque.receitas import PaginaReceitas
from app.pages.estoque.page import PaginaEstoque


class Navigation(ctk.CTkFrame):
    """
    Área principal (conteúdo). Troca páginas conforme uma chave.
    Ex: "inicio", "clientes", "relatorios", etc.
    """

    def __init__(self, master):
        super().__init__(master, fg_color=COR_FUNDO)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.pagina_atual = None

        # mapeamento de rotas -> classes de páginas
        self.routes = {
            "relatorios": PaginaAdminRelatorios,
            "funcionarios": PaginaFuncionarios,
            "balcao": PaginaVendasBalcao,
            "produtos": PaginaProdutos,
            "receitas": PaginaReceitas,
            "estoque": PaginaEstoque,
        }

        # começa no início
        self.show("inicio")

    def show(self, chave: str):
        """Troca a página atual por outra, baseada na chave."""
        if self.pagina_atual is not None:
            self.pagina_atual.destroy()

        PageClass = self.routes.get(chave, None)

        if PageClass is None:
            self.pagina_atual = PlaceholderPage(self, chave=chave)
        else:
            self.pagina_atual = PageClass(self)

        self.pagina_atual.grid(row=0, column=0, sticky="nsew")
