# app/pages/estoque/page.py
import customtkinter as ctk
from datetime import datetime

from app.config.theme import (
    COR_FUNDO, COR_PAINEL, COR_TEXTO, COR_TEXTO_SEC, 
    COR_BOTAO, COR_HOVER, COR_SUCESSO, COR_ERRO, FONTE
)

class PaginaEstoque(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=COR_FUNDO)

        # Configuração do Grid Principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # A tabela cresce

        # --- 1. Cabeçalho ---
        self._criar_cabecalho()

        # --- 2. Filtros e Ações ---
        self._criar_barra_acoes()

        # --- 3. Tabela (Lista de itens) ---
        self._criar_tabela_estoque()
        
        # Carregar dados iniciais (simulação)
        self.carregar_dados()

    def _criar_cabecalho(self):
        frame_topo = ctk.CTkFrame(self, fg_color="transparent")
        frame_topo.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))

        ctk.CTkLabel(
            frame_topo, 
            text="Estoque • Gerenciamento",
            font=ctk.CTkFont(family=FONTE, size=24, weight="bold"),
            text_color=COR_TEXTO
        ).pack(side="left")

        # Exemplo de KPI rápido no topo
        self.lbl_status = ctk.CTkLabel(
            frame_topo,
            text="3 itens com estoque baixo",
            font=ctk.CTkFont(family=FONTE, size=12, weight="bold"),
            text_color=COR_ERRO
        )
        self.lbl_status.pack(side="right", anchor="e")

    def _criar_barra_acoes(self):
        frame_acoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_acoes.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 15))
        
        # Campo de Busca
        self.entry_busca = ctk.CTkEntry(
            frame_acoes, 
            placeholder_text="Buscar item...",
            width=250,
            height=34,
            border_color=COR_PAINEL
        )
        self.entry_busca.pack(side="left", padx=(0, 10))
        
        # Filtro de Categoria
        self.combo_filtro = ctk.CTkComboBox(
            frame_acoes,
            values=["Todos", "Matéria Prima", "Embalagem", "Produto Final"],
            width=150,
            command=self.aplicar_filtro
        )
        self.combo_filtro.pack(side="left")

        # Botão Novo Item
        btn_novo = ctk.CTkButton(
            frame_acoes,
            text="+ Novo Movimento",
            height=34,
            fg_color=COR_PAINEL,
            text_color=COR_TEXTO,
            hover_color=COR_HOVER,
            font=ctk.CTkFont(family=FONTE, size=13, weight="bold"),
            command=self.abrir_modal_movimento
        )
        btn_novo.pack(side="right")

    def _criar_tabela_estoque(self):
        # Container da "Tabela"
        self.frame_lista_container = ctk.CTkFrame(self, fg_color=COR_PAINEL, corner_radius=10)
        self.frame_lista_container.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 30))
        self.frame_lista_container.grid_columnconfigure(0, weight=1)
        self.frame_lista_container.grid_rowconfigure(1, weight=1)

        # Cabeçalho da Tabela
        header = ctk.CTkFrame(self.frame_lista_container, fg_color="transparent", height=40)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        colunas = [
            ("Produto / Item", 3), 
            ("Categoria", 2), 
            ("Qtd. Atual", 1), 
            ("Unidade", 1), 
            ("Status", 1), 
            ("Ações", 1)
        ]
        
        for idx, (titulo, peso) in enumerate(colunas):
            lbl = ctk.CTkLabel(
                header, 
                text=titulo, 
                font=ctk.CTkFont(family=FONTE, size=12, weight="bold"),
                text_color=COR_TEXTO_SEC,
                anchor="w" if idx < 2 else "center"
            )
            # Usamos pack com expand/fill proporcional ou grid. 
            # Grid é melhor para alinhar com as linhas abaixo, mas aqui vou usar grid com peso.
            header.grid_columnconfigure(idx, weight=peso)
            lbl.grid(row=0, column=idx, sticky="ew", padx=5)

        # Área rolável para as linhas
        self.scroll_itens = ctk.CTkScrollableFrame(
            self.frame_lista_container, 
            fg_color="transparent"
        )
        self.scroll_itens.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        
        # Configurar colunas do scroll igual ao header
        for idx, (_, peso) in enumerate(colunas):
            self.scroll_itens.grid_columnconfigure(idx, weight=peso)

    def carregar_dados(self):
        # Limpar lista atual
        for widget in self.scroll_itens.winfo_children():
            widget.destroy()

        # Dados Mockados (Simulação de Banco de Dados)
        dados = [
            {"nome": "Leite Condensado", "cat": "Matéria Prima", "qtd": 45, "uni": "cx", "min": 20},
            {"nome": "Creme de Leite", "cat": "Matéria Prima", "qtd": 12, "uni": "cx", "min": 30},
            {"nome": "Embalagem 1L", "cat": "Embalagem", "qtd": 150, "uni": "un", "min": 50},
            {"nome": "Chocolate 50%", "cat": "Matéria Prima", "qtd": 2.5, "uni": "kg", "min": 1.0},
            {"nome": "Picolé Coco", "cat": "Produto Final", "qtd": 8, "uni": "un", "min": 20},
            {"nome": "Açaí 500ml", "cat": "Produto Final", "qtd": 34, "uni": "un", "min": 10},
            {"nome": "Liga Neutra", "cat": "Matéria Prima", "qtd": 500, "uni": "g", "min": 100},
        ]

        # Renderizar linhas
        for i, item in enumerate(dados):
            self._criar_linha_tabela(i, item)

    def _criar_linha_tabela(self, index, item):
        # Cor zebrada opcional ou fundo branco
        bg_color = COR_BOTAO if index % 2 == 0 else "transparent"
        
        # Verificar status
        status_texto = "OK"
        status_cor = COR_SUCESSO
        if item['qtd'] <= item['min']:
            status_texto = "BAIXO"
            status_cor = COR_ERRO

        # Nome
        ctk.CTkLabel(
            self.scroll_itens, text=item['nome'], font=ctk.CTkFont(family=FONTE, size=13),
            text_color=COR_TEXTO, anchor="w"
        ).grid(row=index, column=0, sticky="ew", padx=5, pady=8)

        # Categoria
        ctk.CTkLabel(
            self.scroll_itens, text=item['cat'], font=ctk.CTkFont(family=FONTE, size=13),
            text_color=COR_TEXTO_SEC, anchor="w"
        ).grid(row=index, column=1, sticky="ew", padx=5, pady=8)

        # Qtd
        ctk.CTkLabel(
            self.scroll_itens, text=str(item['qtd']), font=ctk.CTkFont(family=FONTE, size=13, weight="bold"),
            text_color=COR_TEXTO, anchor="center"
        ).grid(row=index, column=2, sticky="ew", padx=5, pady=8)

        # Unidade
        ctk.CTkLabel(
            self.scroll_itens, text=item['uni'], font=ctk.CTkFont(family=FONTE, size=13),
            text_color=COR_TEXTO_SEC, anchor="center"
        ).grid(row=index, column=3, sticky="ew", padx=5, pady=8)

        # Status (Badge)
        frame_status = ctk.CTkFrame(self.scroll_itens, fg_color=status_cor, height=20, corner_radius=6)
        frame_status.grid(row=index, column=4)
        ctk.CTkLabel(
            frame_status, text=status_texto, font=ctk.CTkFont(family=FONTE, size=10, weight="bold"),
            text_color="white"
        ).pack(padx=8, pady=2)

        # Ações (Botão Editar)
        btn_editar = ctk.CTkButton(
            self.scroll_itens, text="✏️", width=30, height=30,
            fg_color="transparent", hover_color=COR_HOVER,
            text_color=COR_TEXTO,
            command=lambda n=item['nome']: self.editar_item(n)
        )
        btn_editar.grid(row=index, column=5)

        # Separador visual (opcional)
        # ctk.CTkFrame(self.scroll_itens, height=1, fg_color="#E0E0E0").grid(row=index+1, column=0, columnspan=6, sticky="ew")

    def aplicar_filtro(self, valor):
        print(f"Filtrando por: {valor}")
        # Aqui você implementaria a lógica de filtrar a lista 'dados' e chamar self.carregar_dados()

    def abrir_modal_movimento(self):
        print("Abrir janela de entrada/saída de estoque")

    def editar_item(self, nome_item):
        print(f"Editando item: {nome_item}")