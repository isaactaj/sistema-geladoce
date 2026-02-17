
import customtkinter as ctk
from tkinter import ttk
from app.config import theme

#  Pagina funcionarios 
class PaginaFuncionarios(ctk.CTkFrame):

    
    def __init__(self, master):
        # Inicializa o frame com a cor de fundo do tema
        super().__init__(master, fg_color=theme.COR_FUNDO)

        # ===== CONFIGURAÇÃO DO LAYOUT =====
    
        self.grid_columnconfigure(0, weight=3)  # Coluna da tabela
        self.grid_columnconfigure(1, weight=2)  # Coluna do cadastro
        self.grid_rowconfigure(2, weight=1) # tabele cresce verticalmente

        # ===== INICIALIZAÇÃO DO BANCO DE DADOS (SIMULADO) =====
        # Contador para gerar IDs únicos para novos funcionários
        self._proximo_id = 1
        # Lista que armazena todos os funcionários (simula um banco de dados)
        self._funcionarios = []

        # ===== CONSTRUÇÃO DA INTERFACE =====
        # Chama os métodos que criam cada seção da página
        self._criar_topo()        # Cria o título e descrição
        self._criar_busca()       # Cria o campo de busca
        self._criar_tabela()      # Cria a tabela de funcionários
        self._criar_cadastro()    # Cria o formulário de cadastro

        # Popula a tabela com dados de exemplo para demonstração
        self._popular_exemplo()

    # ===== SEÇÃO DE INTERFACE DO USUÁRIO (UI) =====

    def _criar_topo(self):
        # Cria o rótulo principal com o título da página
        ctk.CTkLabel(
            self,
            text="Administração • Funcionários",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO,
            fg_color="transparent"
        ).grid(row=0, column=0, columnspan=2, padx=30, pady=(14, 6), sticky="w")

        # Cria o rótulo descritivo com instruções para o usuário
        ctk.CTkLabel(
            self,
            text="Gerencie os funcionários da empresa, adicione novos membros à equipe e mantenha as informações atualizadas.",
            font=ctk.CTkFont(family=theme.FONTE, size=13),
            text_color=theme.COR_TEXTO_SEC
        ).grid(row=1, column=0, columnspan=2, padx=30, pady=(0, 12), sticky="w")
    
    def _criar_busca(self):
        # Cria um frame (container) transparente para organizar o campo de busca
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=2, column=0, padx=(30, 12), pady=(0, 10), sticky="ew")
        # Faz a coluna do frame crescer para ocupar todo o espaço disponível
        frame.grid_columnconfigure(0, weight=1)

        # Variável que armazena o texto digitado no campo de busca
        # Será atualizada automaticamente quando o usuário digita
        self._busca_var = ctk.StringVar(value="")

        # Cria o campo de entrada de texto para busca
        self._busca_entry = ctk.CTkEntry(
            frame,
            textvariable=self._busca_var,
            placeholder_text="Buscar por nome, cpf ou telefone",  # Texto que aparece quando vazio
            height=36,
        )
        self._busca_entry.grid(row=0, column=0, sticky="ew")

        # Vincula o evento de digitação ao método que atualiza a tabela
        # A cada tecla liberada, a tabela é filtrada com base no texto digitado
        self._busca_entry.bind("<KeyRelease>", lambda e: self._atualizar_tabela())


    def _criar_tabela(self):
        # Cria um container com fundo cinza para abrigar a tabela
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=3, column=0, padx=(30, 12), pady=(0, 20), sticky="nsew")
        # Faz a linha da tabela crescer quando a janela é redimensionada
        box.grid_rowconfigure(0, weight=1)
        # Faz a tabela ocupar toda a largura do container
        box.grid_columnconfigure(0, weight=1)

        # estilo
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            font=(theme.FONTE, 11),
            rowheight=28,
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
        )
        style.configure(
            "Treeview.Heading",
            font=(theme.FONTE, 11, "bold"),
        )

        colunas = ("id", "nome", "cpf", "telefone")
        self.tree = ttk.Treeview(box, columns=colunas, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("nome", text="Nome")
        self.tree.heading("cpf", text="CPF")
        self.tree.heading("telefone", text="Telefone")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("nome", width=240, anchor="w")
        self.tree.column("cpf", width=140, anchor="center")
        self.tree.column("telefone", width=140, anchor="center")

        # scrollbar
        scroll = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns", padx=(0, 12), pady=12)

        # clique na linha > carregar no formulário
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._carregar_selecionado_no_form())

    def _criar_cadastro(self):
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=2, column=1, rowspan=2, padx=(12, 30), pady=(0, 20), sticky="nsew")
        box.grid_rowconfigure(0, weight=0)  # título

        # Titutlo do formulário de cadastro
        ctk.CTkLabel(
            box,
            text="Cadastro de Funcionário",
            font=ctk.CTkFont(famaly=theme.FONTE, size=16, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, padx=16, pady=(16, 10), sticky="w")

        self.lbl_status = ctk.CTkLabel(
            box,
            text="",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC,
        )
        self.lbl_status.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="w")

        # Campos do formulário
        self.nome_var = ctk.StringVar()
        self.cpf_var = ctk.StringVar()
        self.telefone_var = ctk.StringVar()
        self.id_selecionado = None  # Armazena o ID do funcionário selecionado para edição

        def label(texto, r):
            ctk.CTkLabel(
                ctk.CTkFrame(
                    box,
                    text=texto,
                    font=ctk.CTkFont(family=theme.FONTE, size=12), weight="bold"),
                    text_color=theme.COR_TEXTO_SEC
                ).grid(row=r, column=0, padx=16, pady=(10, 4), sticky="w")

        label("Nome", 2)
        self.entry_nome = ctk.CTkEntry(box, textvariable=self.nome_var, height=36)
        self.entry_nome.grid(row=3, column=0, padx=16, pady=(0, 10), sticky="ew")

        label("CPF", 4)
        self.entry_cpf = ctk.CTkEntry(box, textvariable=self.cpf_var, height=36)
        self.entry_cpf.grid(row=5, column=0, padx=16, sticky="ew")
        
        label("Telefone", 6)
        self.entry_tel = ctk.CTkEntry(box, textvariable=self.telefone_var, height=36)
        self.entry_tel.grid(row=7, column=0, padx=16, sticky="ew")




