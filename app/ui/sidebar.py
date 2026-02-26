import customtkinter as ctk
from PIL import Image
import os

from app.config.theme import (
    COR_PAINEL, COR_BOTAO, COR_HOVER, COR_SELECIONADO,
    COR_TEXTO, FONTE
)


class SecaoExpansivel(ctk.CTkFrame):
    def __init__(self, master, titulo, ao_clicar, itens, ao_alternar=None, icone=None):
        super().__init__(master, fg_color="transparent")

        self.ao_clicar = ao_clicar
        self.itens = itens
        self.aberto = False
        self.ao_alternar = ao_alternar

        self.botoes_filhos = {}

        # Botão principal da seção
        self.botao_titulo = ctk.CTkButton(
            self,
            text=titulo,
            image=icone,
            compound="left",
            anchor="w",
            height=38,
            fg_color=COR_BOTAO,
            text_color=COR_TEXTO,
            hover_color=COR_HOVER,
            font=ctk.CTkFont(family=FONTE, size=13, weight="bold"),
            command=self.alternar,
        )
        self.botao_titulo.pack(fill="x", padx=20, pady=(6, 4))

        # Frame dos subitens (começa oculto)
        self.frame_itens = ctk.CTkFrame(self, fg_color="transparent")

        for nome, chave in self.itens:
            botao = ctk.CTkButton(
                self.frame_itens,
                text=nome,
                anchor="w",
                height=34,
                fg_color=COR_BOTAO,
                hover_color=COR_HOVER,
                text_color=COR_TEXTO,
                font=ctk.CTkFont(family=FONTE, size=12),
                command=lambda c=chave: self.ao_clicar(c),
            )
            botao.pack(fill="x", padx=34, pady=4)
            self.botoes_filhos[chave] = botao

    def abrir(self):
        if not self.aberto:
            self.aberto = True
            self.frame_itens.pack(fill="x", pady=(0, 6))

    def fechar(self):
        if self.aberto:
            self.aberto = False
            self.frame_itens.pack_forget()

    def alternar(self):
        if self.ao_alternar:
            self.ao_alternar(self)

        if self.aberto:
            self.fechar()
        else:
            self.abrir()

    def marcar_ativo(self, chave_ativa):
        for chave, botao in self.botoes_filhos.items():
            if chave == chave_ativa:
                botao.configure(fg_color=COR_SELECIONADO, text_color="white")
            else:
                botao.configure(fg_color=COR_BOTAO, text_color=COR_TEXTO)


class MenuLateral(ctk.CTkFrame):
    def __init__(self, master, ao_navegar, assets_dir="assets"):
        super().__init__(master, width=260, fg_color=COR_PAINEL)

        self.ao_navegar = ao_navegar
        self.assets_dir = assets_dir

        self.botoes_simples = {}
        self.icones = self._carregar_icones()

        # empurra conteúdo para cima (se precisar)
        self.grid_rowconfigure(99, weight=1)

        # espaçador topo
        ctk.CTkLabel(self, text="").grid(row=0, column=0, pady=(10, 0))

        # Logo (se existir)
        self._carregar_logo()

        # botões simples
        self.criar_botao("Início", "inicio", 3, self.icones["inicio"])
        self.criar_botao("Clientes", "clientes", 4, self.icones["clientes"])

        # seções expansíveis
        self.vendas = SecaoExpansivel(
            self,
            titulo="Vendas",
            ao_clicar=self.ao_navegar,
            itens=[
                ("Balcão", "balcao"),
                ("Revenda", "revenda"),
                ("Serviços", "servicos"),
                ("Fechamento", "fechamento"),
            ],
            ao_alternar=self.fechar_outras_secoes,
            icone=self.icones["vendas"]
        )
        self.vendas.grid(row=5, column=0, sticky="ew")

        self.estoque = SecaoExpansivel(
            self,
            titulo="Estoque",
            ao_clicar=self.ao_navegar,
            itens=[
                ("Produtos", "produtos"),
                ("Receitas", "receitas"),
                ("Estoque", "estoque"),
            ],
            ao_alternar=self.fechar_outras_secoes,
            icone=self.icones["estoque_menu"]
        )
        self.estoque.grid(row=6, column=0, sticky="ew")

        self.criar_botao("Fornecedores", "fornecedores", 7, self.icones["fornecedores"])
        self.criar_botao("Fidelidade", "fidelidade", 8, self.icones["fidelidade"])

        self.adm = SecaoExpansivel(
            self,
            titulo="Administração",
            ao_clicar=self.ao_navegar,
            itens=[
                ("Relatórios", "relatorios"),
                ("Funcionários", "funcionarios"),
            ],
            ao_alternar=self.fechar_outras_secoes,
            icone=self.icones["administracao"]
        )
        self.adm.grid(row=9, column=0, sticky="ew")

        # rodapé do usuário
        self._criar_rodape_usuario()
    # ------------------------
    # Icones do menu laterel
    #------------------------
    def _carregar_icones(self):
        tamanho = (18, 18)

        def carregar(nome_arquivo):
            caminho = os.path.join(self.assets_dir, nome_arquivo)
            if os.path.exists(caminho):
                return ctk.CTkImage(
                    light_image=Image.open(caminho),
                    size=tamanho
                )
            return None
        
        return {
            "inicio": carregar("icon_inicio.png"),
            "clientes": carregar("icon_clientes.png"),
            "vendas": carregar("icon_vendas.png"),
            "estoque_menu": carregar("icon_estoque_menu.png"),
            "fornecedores": carregar("icon_fornecedores.png"),
            "fidelidade": carregar("icon_fidelidade.png"),
            "administracao": carregar("icon_administracao.png")
        }

    # -------------------------
    # Logo
    # -------------------------
    def _carregar_logo(self):
        logo_path = os.path.join(self.assets_dir, "logo_geladoce.png")
        if os.path.exists(logo_path):
            self.logo_img = ctk.CTkImage(
                light_image=Image.open(logo_path),
                size=(160, 60),
            )
            ctk.CTkLabel(self, image=self.logo_img, text="").grid(
                row=1, column=0, padx=20, pady=(0, 15), sticky="w"
            )
        else:
            ctk.CTkLabel(
                self,
                text="Geladoce",
                font=ctk.CTkFont(family=FONTE, size=18, weight="bold"),
                text_color=COR_TEXTO,
            ).grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

    # -------------------------
    # Rodapé usuário
    # -------------------------
    def _criar_rodape_usuario(self):
        self.frame_usuario = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_usuario.place(relx=0, rely=1, anchor="sw", x=20, y=-20)
        self.frame_usuario.configure(width=220)

        self.label_icone_usuario = ctk.CTkLabel(
            self.frame_usuario,
            text="👤",
            font=ctk.CTkFont(family=FONTE, size=18),
            text_color=COR_TEXTO,
        )
        self.label_icone_usuario.grid(row=0, column=0, padx=(0, 10))

        self.label_nome_usuario = ctk.CTkLabel(
            self.frame_usuario,
            text="Não logado",
            font=ctk.CTkFont(family=FONTE, size=12, weight="bold"),
            text_color=COR_TEXTO,
        )
        self.label_nome_usuario.grid(row=0, column=1, sticky="w")

        self.frame_usuario.grid_columnconfigure(1, weight=1)

    def atualizar_usuario(self, nome: str):
        self.label_nome_usuario.configure(text=nome)

    # -------------------------
    # Botão simples
    # -------------------------
    def criar_botao(self, texto, chave, linha, icone=None):
        botao = ctk.CTkButton(
            self,
            text=texto,
            image=icone,
            compound="left",
            anchor="w",
            height=38,
            fg_color=COR_BOTAO,
            text_color=COR_TEXTO,
            hover_color=COR_HOVER,
            font=ctk.CTkFont(family=FONTE, size=13, weight="bold"),
            command=lambda c=chave: self.ao_navegar(c),
        )
        botao.grid(row=linha, column=0, sticky="ew", padx=20, pady=6)
        self.botoes_simples[chave] = botao

    # -------------------------
    # Marcar item ativo
    # -------------------------
    def marcar_ativo(self, chave_ativa):
        # botões simples
        for chave, botao in self.botoes_simples.items():
            if chave == chave_ativa:
                botao.configure(fg_color=COR_SELECIONADO, text_color="white")
            else:
                botao.configure(fg_color=COR_BOTAO, text_color=COR_TEXTO)

        # subitens
        self.vendas.marcar_ativo(chave_ativa)
        self.estoque.marcar_ativo(chave_ativa)
        self.adm.marcar_ativo(chave_ativa)

    # -------------------------
    # Accordion: só 1 aberto
    # -------------------------
    def fechar_outras_secoes(self, secao_clicada):
        for secao in (self.vendas, self.estoque, self.adm):
            if secao is not secao_clicada:
                secao.fechar()
