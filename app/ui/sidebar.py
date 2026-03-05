import customtkinter as ctk
from PIL import Image
import os
from typing import Optional

# Popup elegante (se não existir, cai no tkinter.messagebox)
try:
    from CTkMessagebox import CTkMessagebox
except Exception:
    CTkMessagebox = None

try:
    from tkinter import messagebox
except Exception:
    messagebox = None

from app.config.theme import (
    COR_PAINEL, COR_BOTAO, COR_HOVER, COR_SELECIONADO,
    COR_TEXTO, FONTE
)


class SecaoExpansivel(ctk.CTkFrame):
    """
    Seção com botão principal + subitens (accordion).
    - Usa GRID (mais estável, não “puxa” largura do menu)
    - Pode ser bloqueada (ex: Administração para colaborador)
    """
    def __init__(self, master, titulo, ao_clicar, itens, ao_alternar=None, icone=None):
        super().__init__(master, fg_color="transparent")

        self.ao_clicar = ao_clicar
        self.itens = itens
        self.aberto = False
        self.ao_alternar = ao_alternar
        self._habilitado = True

        self.botoes_filhos = {}

        self.grid_columnconfigure(0, weight=1)

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
        self.botao_titulo.grid(row=0, column=0, sticky="ew", padx=20, pady=(6, 4))

        self.frame_itens = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_itens.grid_columnconfigure(0, weight=1)

        for i, (nome, chave) in enumerate(self.itens):
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
            botao.grid(row=i, column=0, sticky="ew", padx=34, pady=4)
            self.botoes_filhos[chave] = botao

    def abrir(self):
        if not self._habilitado:
            return
        if not self.aberto:
            self.aberto = True
            self.frame_itens.grid(row=1, column=0, sticky="ew", pady=(0, 6))

    def fechar(self):
        if self.aberto:
            self.aberto = False
            self.frame_itens.grid_forget()

    def alternar(self):
        if not self._habilitado:
            return

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

    def set_titulo(self, titulo: str):
        self.botao_titulo.configure(text=titulo)

    def set_habilitado(self, habilitado: bool):
        self._habilitado = bool(habilitado)

        estado = "normal" if self._habilitado else "disabled"
        self.botao_titulo.configure(state=estado)
        for b in self.botoes_filhos.values():
            b.configure(state=estado)

        if not self._habilitado:
            self.fechar()


class MenuLateral(ctk.CTkFrame):
    """
    Menu lateral fixo (não cresce no eixo X).
    Rodapé:
      - card clicável (em vez de botão multi-linha)
      - texto centralizado
      - nome em destaque
      - tipo menor e mais fino
      - chama callback para trocar usuário/logout
    """
    LARGURA_MENU = 260
    ROTAS_ADMIN = {"relatorios", "funcionarios"}  # rotas restritas

    def __init__(
        self,
        master,
        ao_navegar,
        assets_dir="assets",
        usuario_logado=None,
        sistema=None,  # ✅ opcional: reusa do master se existir
    ):
        super().__init__(master, width=self.LARGURA_MENU, fg_color=COR_PAINEL)

        # trava largura (para NÃO ficar responsivo no eixo X)
        self.grid_propagate(False)
        self.configure(width=self.LARGURA_MENU)

        self.ao_navegar = ao_navegar
        self.assets_dir = assets_dir

        # ✅ não cria service/repo aqui; apenas reusa se vier do master
        self.sistema = getattr(master, "sistema", None) or sistema

        self.botoes_simples = {}
        self.icones = self._carregar_icones()

        self._acao_usuario = None
        self._usuario_logado = usuario_logado or {}
        self._is_admin = False

        # layout geral
        self.grid_columnconfigure(0, weight=1, minsize=self.LARGURA_MENU)
        self.grid_rowconfigure(99, weight=1)  # empurra rodapé para baixo

        ctk.CTkLabel(self, text="").grid(row=0, column=0, pady=(10, 0))

        self._carregar_logo()

        # botões simples
        self.criar_botao("Início", "inicio", 3, self.icones["inicio"])
        self.criar_botao("Clientes", "clientes", 4, self.icones["clientes"])

        # seções expansíveis
        self.vendas = SecaoExpansivel(
            self,
            titulo="Vendas",
            ao_clicar=self._navegar_com_permissao,
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
            ao_clicar=self._navegar_com_permissao,
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
            ao_clicar=self._navegar_com_permissao,
            itens=[
                ("Relatórios", "relatorios"),
                ("Funcionários", "funcionarios"),
            ],
            ao_alternar=self.fechar_outras_secoes,
            icone=self.icones["administracao"]
        )
        self.adm.grid(row=9, column=0, sticky="ew")

        # rodapé (card clicável)
        self._criar_rodape_usuario()

        # aplica usuário/permissões iniciais
        self.set_usuario_logado(self._usuario_logado)

    # ------------------------
    # Ícones
    # ------------------------
    def _carregar_icones(self):
        tamanho = (18, 18)

        def carregar(nome_arquivo):
            caminho = os.path.join(self.assets_dir, nome_arquivo)
            if os.path.exists(caminho):
                try:
                    return ctk.CTkImage(light_image=Image.open(caminho), size=tamanho)
                except Exception:
                    return None
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
        """
        Mantém a row=1, mas centraliza no eixo X alinhando com as seções.
        Para isso:
        - usa sticky="ew" e o mesmo padx=20 dos botões
        - label com anchor="center"
        """
        logo_path = os.path.join(self.assets_dir, "logo_geladoce.png")

        if os.path.exists(logo_path):
            self.logo_img = ctk.CTkImage(light_image=Image.open(logo_path), size=(180, 80))
            self.logo_label = ctk.CTkLabel(self, image=self.logo_img, text="", anchor="center")
            self.logo_label.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
        else:
            self.logo_label = ctk.CTkLabel(
                self,
                text="Geladoce",
                font=ctk.CTkFont(family=FONTE, size=18, weight="bold"),
                text_color=COR_TEXTO,
                anchor="center",
            )
            self.logo_label.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")

    # -------------------------
    # Rodapé usuário (CARD clicável)
    # -------------------------
    def _criar_rodape_usuario(self):
        """
        Card com:
        - nome centralizado (maior/mais forte)
        - tipo centralizado (menor e mais fino)
        - hover + clique chamando callback do main.py
        """
        self.frame_usuario = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_usuario.grid(row=100, column=0, sticky="ew", padx=16, pady=(10, 16))
        self.frame_usuario.grid_columnconfigure(0, weight=1)

        # Card
        self.usuario_card = ctk.CTkFrame(
            self.frame_usuario,
            fg_color=COR_BOTAO,
            corner_radius=12,
            border_width=1,
            border_color=COR_HOVER,
        )
        self.usuario_card.grid(row=0, column=0, sticky="ew")
        self.usuario_card.grid_columnconfigure(0, weight=1)

        # Conteúdo (centralizado)
        self.usuario_inner = ctk.CTkFrame(self.usuario_card, fg_color="transparent")
        self.usuario_inner.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.usuario_inner.grid_columnconfigure(0, weight=1)

        self.lbl_usuario_nome = ctk.CTkLabel(
            self.usuario_inner,
            text="👤 Não logado",
            text_color=COR_TEXTO,
            font=ctk.CTkFont(family=FONTE, size=13, weight="bold"),
            anchor="center",
            justify="center",
        )
        self.lbl_usuario_nome.grid(row=0, column=0, sticky="ew")

        self.lbl_usuario_tipo = ctk.CTkLabel(
            self.usuario_inner,
            text="",
            text_color=COR_TEXTO,
            font=ctk.CTkFont(family=FONTE, size=11, weight="normal"),
            anchor="center",
            justify="center",
        )
        self.lbl_usuario_tipo.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        # bindings (clique + hover) em todas as partes
        self._bind_click_hover(self.usuario_card)
        self._bind_click_hover(self.usuario_inner)
        self._bind_click_hover(self.lbl_usuario_nome)
        self._bind_click_hover(self.lbl_usuario_tipo)

        # cursor de “mão” quando possível
        for w in (self.usuario_card, self.usuario_inner, self.lbl_usuario_nome, self.lbl_usuario_tipo):
            try:
                w.configure(cursor="hand2")
            except Exception:
                pass

    def _bind_click_hover(self, widget):
        widget.bind("<Button-1>", lambda e: self._ao_clicar_usuario())
        widget.bind("<Enter>", lambda e: self._hover_usuario(True))
        widget.bind("<Leave>", lambda e: self._hover_usuario(False))

    def _hover_usuario(self, hover: bool):
        # hover suave no card
        try:
            self.usuario_card.configure(fg_color=COR_HOVER if hover else COR_BOTAO)
        except Exception:
            pass

    def configurar_acao_usuario(self, callback):
        """main.py define o que acontece ao clicar no usuário."""
        self._acao_usuario = callback

    def _ao_clicar_usuario(self):
        if callable(self._acao_usuario):
            self._acao_usuario()

    # -------------------------
    # Usuário logado + permissões
    # -------------------------
    def set_usuario_logado(self, usuario: dict):
        """
        Passe o usuário do login:
        {"nome": "...", "tipo_acesso": "Administrador"|"Colaborador"}
        """
        self._usuario_logado = usuario or {}

        nome = (self._usuario_logado.get("nome") or self._usuario_logado.get("login") or "Não logado").strip()

        tipo_raw = str(self._usuario_logado.get("tipo_acesso", "")).strip()
        tipo = "Administrador" if tipo_raw.lower() == "administrador" else "Colaborador"
        self._is_admin = (tipo == "Administrador")

        # Atualiza UI do rodapé (centralizada, com fontes diferentes)
        if hasattr(self, "lbl_usuario_nome"):
            self.lbl_usuario_nome.configure(text=f"👤 {nome}")
        if hasattr(self, "lbl_usuario_tipo"):
            self.lbl_usuario_tipo.configure(text=tipo)

        self._aplicar_permissoes()

    def _aplicar_permissoes(self):
        if self._is_admin:
            self.adm.set_titulo("Administração")
            self.adm.set_habilitado(True)
        else:
            self.adm.fechar()
            self.adm.set_titulo("Administração 🔒")
            self.adm.set_habilitado(False)

    # compatibilidade com chamadas antigas
    def atualizar_usuario(self, nome: str):
        tipo_raw = str(self._usuario_logado.get("tipo_acesso", "")).strip()
        tipo = "Administrador" if tipo_raw.lower() == "administrador" else "Colaborador"
        if hasattr(self, "lbl_usuario_nome"):
            self.lbl_usuario_nome.configure(text=f"👤 {str(nome).strip()}")
        if hasattr(self, "lbl_usuario_tipo"):
            self.lbl_usuario_tipo.configure(text=tipo)

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
            command=lambda c=chave: self._navegar_com_permissao(c),
        )
        botao.grid(row=linha, column=0, sticky="ew", padx=20, pady=6)
        self.botoes_simples[chave] = botao

    # -------------------------
    # Navegação com permissão
    # -------------------------
    def _navegar_com_permissao(self, chave: str):
        if (chave in self.ROTAS_ADMIN) and (not self._is_admin):
            self._mostrar_acesso_negado()
            return
        self.ao_navegar(chave)

    def _mostrar_acesso_negado(self):
        msg = "Acesso restrito. Apenas administradores podem acessar esta seção."
        if CTkMessagebox is not None:
            CTkMessagebox(title="Acesso negado", message=msg, icon="warning")
        elif messagebox is not None:
            messagebox.showwarning("Acesso negado", msg)
        else:
            print(msg)

    # -------------------------
    # Marcar item ativo
    # -------------------------
    def marcar_ativo(self, chave_ativa):
        for chave, botao in self.botoes_simples.items():
            if chave == chave_ativa:
                botao.configure(fg_color=COR_SELECIONADO, text_color="white")
            else:
                botao.configure(fg_color=COR_BOTAO, text_color=COR_TEXTO)

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