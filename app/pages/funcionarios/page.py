
import customtkinter as ctk
from tkinter import ttk
from tkinter import messagebox
from app.config import theme

#  Pagina funcionarios 
class PaginaFuncionarios(ctk.CTkFrame):

    
    def __init__(self, master):
        # Inicializa o frame com a cor de fundo do tema
        super().__init__(master, fg_color=theme.COR_FUNDO)

        # ===== CONFIGURAÇÃO DO LAYOUT =====
    
        # ===== CONFIGURAÇÃO DO LAYOUT =====
        self.grid_columnconfigure(0, weight=3)  # Coluna da tabela
        self.grid_columnconfigure(1, weight=2)  # Coluna do cadastro

        self.grid_rowconfigure(2, weight=0)  # busca NÃO cresce
        self.grid_rowconfigure(3, weight=1)  # tabela cresce

        # ===== INICIALIZAÇÃO DO BANCO DE DADOS (SIMULADO) =====
        # Contador para gerar IDs únicos para novos funcionários
        self._proximo_id = 1
        # Lista que armazena todos os funcionários (simula um banco de dados)
        # usamos nome sem underscore para corresponder ao resto do código
        self.funcionarios = []

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
            text="Administrativo • Funcionários",
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
        # a variável de busca é usada em outros métodos sem _
        self.busca_var = ctk.StringVar(value="")

        # Cria o campo de entrada de texto para busca
        self._busca_entry = ctk.CTkEntry(
            frame,
            textvariable=self.busca_var,
            placeholder_text="🔎 Buscar",
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
        style.theme_use("clam")
        style.configure(
            "Treeview",
            font=(theme.FONTE, 16),
            rowheight=37,
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
        )
        style.configure(
            "Treeview.Heading",
            font=(theme.FONTE, 16, "bold"),
        )
        style.map(
            "Treeview",
            background=[("selected", "#C1ECFD")],
            foreground=[("selected", "#000000")],
        )


        colunas = ("id", "nome", "cpf", "telefone")

        self.tree = ttk.Treeview(box, columns=colunas, show="headings", selectmode="browse")
        # posiciona a treeview dentro do container
        self.tree.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

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
        scroll_x = ttk.Scrollbar(box, orient="horizontal", command=self.tree.xview)
        scroll_x.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        # vincula a barra à tabela
        self.tree.configure(yscrollcommand=scroll.set)

        # clique na linha > carregar no formulário
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._carregar_selecionado_no_form())

    def _criar_cadastro(self):
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=2, column=1, rowspan=2, padx=(12, 30), pady=(0, 20), sticky="nsew")
        # adiciona espaçadores para centralizar verticalmente o conteúdo
        box.grid_rowconfigure(0, weight=1)  # espaço superior
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(11, weight=1)  # espaço inferior

        # Titutlo do formulário de cadastro
        ctk.CTkLabel(
            box,
            text="Cadastro de Funcionário",
            font=ctk.CTkFont(family=theme.FONTE, size=16, weight="bold"),
            text_color=theme.COR_TEXTO,
            anchor="center",
        ).grid(row=1, column=0, padx=16, pady=(6, 4), sticky="ew")

        self.lbl_status = ctk.CTkLabel(
            box,
            text="",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC,
        )
        self.lbl_status.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="w")

        # Campos do formulário
        self.nome_var = ctk.StringVar()
        self.cpf_var = ctk.StringVar()
        self.telefone_var = ctk.StringVar()
        self.id_selecionado = None  # Armazena o ID do funcionário selecionado para edição

        # helper para rótulos do formulário
        def label(texto, r):
            ctk.CTkLabel(
                box,
                text=texto,
                font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
                text_color=theme.COR_TEXTO_SEC,
            ).grid(row=r, column=0, padx=16, pady=(10, 4), sticky="w")

        label("Nome", 3)
        self.entry_nome = ctk.CTkEntry(box, textvariable=self.nome_var, height=36)
        self.entry_nome.grid(row=4, column=0, padx=16, pady=(0, 10), sticky="ew")

        label("CPF", 5)
        self.entry_cpf = ctk.CTkEntry(box, textvariable=self.cpf_var, height=36)
        self.entry_cpf.grid(row=6, column=0, padx=16, sticky="ew")
        
        label("Telefone", 7)
        self.entry_tel = ctk.CTkEntry(box, textvariable=self.telefone_var, height=36)
        self.entry_tel.grid(row=8, column=0, padx=16, sticky="ew")

        # botões 
        botoes = ctk.CTkFrame(box, fg_color="transparent")
        botoes.grid(row=9, column=0, padx=16, pady=(16, 16), sticky="ew")
        botoes.grid_columnconfigure((0, 1), weight=1)

        self.btn_salvar = ctk.CTkButton(
            botoes,
            text="Salvar",
            height=36,
            fg_color="#FFFFFF",
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._salvar
        )
        self.btn_salvar.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.btn_limpar = ctk.CTkButton(
            botoes,
            text="Limpar",
            height=36,
            fg_color="#FFFFFF",
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._limpar_form
        )
        self.btn_limpar.grid(row=0, column=1, padx=(8, 0), sticky="ew")

        # excluir

        self.btn_excluir = ctk.CTkButton(
            box,
            text="Excluir selecionado",
            height=36,
            fg_color="#FFFFFF",
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._excluir
        )
        self.btn_excluir.grid(row=10, column=0, padx=16, pady=(0, 16), sticky="ew")

    # Regras / Logica

    def _popular_exemplo(self):
        self._inserir_funcionario("Augusto Junior", "12345678901", "(91) 99999-0001")
        self._inserir_funcionario("Maria Souza", "90903737312", "(91) 99779-1031")
        self._inserir_funcionario("Tercio Anjos", "93029944879", "(91) 98669-7773")
        self._atualizar_tabela()
    
    def _inserir_funcionario(self, nome, cpf, telefone):
        item = {"id": self._proximo_id, "nome": nome, "cpf": cpf, "telefone": telefone}
        self._proximo_id += 1
        self.funcionarios.append(item)

    def _atualizar_tabela(self):
        filtro = self.busca_var.get().strip().lower()
        # limpa
        for i in self.tree.get_children():
            self.tree.delete(i)
        #filtra
        for f in self.funcionarios:
            texto = f'{f["nome"]} {f["cpf"]} {f["telefone"]}'.lower()
            if (not filtro) or (filtro in texto):
                self.tree.insert("", "end", values=(f["id"], f["nome"], f["cpf"], f["telefone"]))

    def _validar(self, nome, cpf, telefone):
        if not nome.strip():
            return "Nome é obrigatório."
        cpf_digits = "".join([c for c in cpf if c.isdigit()])
        if len(cpf_digits) != 11:
            return "CPF deve ter 11 números."
        if not telefone.strip():
            return "Telefone é obrigatório."
        return None

    def _salvar(self):
        nome = self.nome_var.get()
        cpf = self.cpf_var.get()
        telefone = self.telefone_var.get()

        erro = self._validar(nome, cpf, telefone)
        if erro:
            messagebox.showwarning("Campos inválidos", erro)
            return

        cpf_digits = "".join([c for c in cpf if c.isdigit()])

        # editar
        if self.id_selecionado is not None:
            for f in self.funcionarios:
                if f["id"] == self.id_selecionado:
                    f["nome"] = nome.strip()
                    f["cpf"] = cpf_digits
                    f["telefone"] = telefone.strip()
                    break
            self._limpar_form()
            self._atualizar_tabela()
            messagebox.showinfo("Sucesso", "Funcionário atualizado com sucesso")
            return

        # cadastrar novo
        else:
            self._inserir_funcionario(nome.strip(), cpf_digits, telefone.strip())
            self._limpar_form()
            self._atualizar_tabela()
            messagebox.showinfo("Sucesso", "Funcionário adicionado com sucesso")


    def _excluir(self):
        if self.id_selecionado is None:
            messagebox.showwarning("Atenção", "Selecione um funcionário na tabela")
            return
        
        # Confirmação
        confirmar = messagebox.askyesno(
            "Confirmar exclusão",
            "Certeza que quer excluir?"
        )
        if not confirmar:
            return

        self.funcionarios = [f for f in self.funcionarios if f["id"] != self.id_selecionado]
        self._limpar_form()
        self._atualizar_tabela()

        # Mensagem final
        messagebox.showinfo("Sucesso", "Funcionario excluido com sucesso")

    def _limpar_form(self):
        self.id_selecionado = None
        self.nome_var.set("")
        self.cpf_var.set("")
        self.telefone_var.set("")
        self.tree.selection_remove(self.tree.selection())
      

    def _carregar_selecionado_no_form(self):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        if not values:
            return

        fid = int(values[0])
        self.id_selecionado = fid

        for f in self.funcionarios:
            if f["id"] == fid:
                self.nome_var.set(f["nome"])
                self.cpf_var.set(f["cpf"])
                self.telefone_var.set(f["telefone"])
                break

        self.lbl_status.configure(text=f"Editando ID {fid}", text_color=theme.COR_TEXTO_SEC)




