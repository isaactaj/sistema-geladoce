"""
MÓDULO DE REVENDA - Sistema Geladoce
=====================================
Este módulo gerencia revendedores, registra vendas, calcula comissões
e mantém histórico de transações com revendedores.

Funcionalidades:
- Cadastro e edição de revendedores
- Registro de vendas para revendedores
- Cálculo automático de comissões
- Visualização de histórico
- Relatório de faturamento
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
from decimal import Decimal

from app.config import theme





class PaginaRevenda(ctk.CTkFrame):
    """
    Página principal de gerenciamento de revenda.
    
    Estrutura:
    - Abas (Tabs): "Revendedores", "Registrar Venda", "Histórico", "Relatório"
    - Cada aba tem sua própria lógica e UI
    """
    
    def __init__(self, master):
        super().__init__(master, fg_color=theme.COR_FUNDO)
        
        # Configurar grid para que a aba ocupe todo espaço
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Estado da aplicação
        self.revendedores = self._mock_revendedores()
        self.vendas = self._mock_vendas()
        self.produtos = self._mock_produtos()
        
        # UI: Título
        self._render_titulo()
        
        # UI: Abas
        self._render_abas()
    
    # ========================================
    # SEÇÃO 1: UI PRINCIPAL
    # ========================================
    
    def _render_titulo(self):
        """
        Renderiza o cabeçalho da página.
        Exibe título e subtítulo da página de revenda.
        """
        ctk.CTkLabel(
            self,
            text="Revenda",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=30, pady=(14, 6), sticky="w")
        
        ctk.CTkLabel(
            self,
            text="Gerencie revendedores, registre vendas e acompanhe comissões.",
            font=ctk.CTkFont(family=theme.FONTE, size=13),
            text_color=theme.COR_TEXTO_SEC
        ).grid(row=0, column=0, padx=30, pady=(35, 12), sticky="w")
    
    def _render_abas(self):
        """
        Cria o sistema de abas (CTkTabview) com 4 seções principais.
        Cada aba organiza um aspecto diferente da revenda.
        """
        # CTkTabview cria abas nativas do customtkinter
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=theme.COR_PAINEL,
            segmented_button_fg_color=theme.COR_PAINEL,
            text_color=theme.COR_TEXTO
        )
        self.tabview.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="nsew")
        
        # Criar abas
        aba_revendedores = self.tabview.add("Revendedores")
        aba_venda = self.tabview.add("Registrar Venda")
        aba_historico = self.tabview.add("Histórico")
        aba_relatorio = self.tabview.add("Relatório")
        
        # Renderizar conteúdo de cada aba
        self._render_aba_revendedores(aba_revendedores)
        self._render_aba_venda(aba_venda)
        self._render_aba_historico(aba_historico)
        self._render_aba_relatorio(aba_relatorio)
    
    # ========================================
    # SEÇÃO 2: ABA "REVENDEDORES"
    # ========================================
    
    def _render_aba_revendedores(self, parent):
        """
        Aba para gerenciar revendedores.
        Exibe lista de revendedores e botões para adicionar/editar/deletar.
        """
        # Frame superior com título e botão
        top_frame = ctk.CTkFrame(parent, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))
        top_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            top_frame,
            text="Revendedores Cadastrados",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, sticky="w")
        
        ctk.CTkButton(
            top_frame,
            text="+ Novo Revendedor",
            width=150,
            command=self._abrir_dialog_novo_revendedor
        ).grid(row=0, column=1, sticky="e")
        
        # Tabela (Treeview) com revendedores
        table_frame = ctk.CTkFrame(parent, fg_color=theme.COR_PAINEL)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Configurar estilo da tabela
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=(theme.FONTE, 11), rowheight=28)
        style.configure("Treeview.Heading", font=(theme.FONTE, 11, "bold"))
        
        # Criar tabela com colunas
        self.tree_revendedores = ttk.Treeview(
            table_frame,
            columns=("nome", "contato", "endereco", "comissao"),
            show="tree headings",
            height=12
        )
        
        # Definir cabeçalhos e largura
        self.tree_revendedores.heading("#0", text="ID")
        self.tree_revendedores.heading("nome", text="Nome")
        self.tree_revendedores.heading("contato", text="Contato")
        self.tree_revendedores.heading("endereco", text="Endereço")
        self.tree_revendedores.heading("comissao", text="Comissão %")
        
        self.tree_revendedores.column("#0", width=40)
        self.tree_revendedores.column("nome", width=150)
        self.tree_revendedores.column("contato", width=120)
        self.tree_revendedores.column("endereco", width=200)
        self.tree_revendedores.column("comissao", width=80)
        
        self.tree_revendedores.pack(side="left", fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree_revendedores.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.tree_revendedores.configure(yscroll=scrollbar.set)
        
        # Preencher tabela com dados
        self._atualizar_tree_revendedores()
        
        # Frame de botões
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        btn_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkButton(
            btn_frame,
            text="Editar",
            width=100,
            command=self._editar_revendedor
        ).grid(row=0, column=0, sticky="e", padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame,
            text="Deletar",
            width=100,
            fg_color=theme.COR_ERRO,
            command=self._deletar_revendedor
        ).grid(row=0, column=1, sticky="e")
    
    def _atualizar_tree_revendedores(self):
        """
        Atualiza a tabela de revendedores com dados do estado.
        Limpa a tabela e reinsere todos os revendedores.
        """
        # Limpar todos os itens
        for item in self.tree_revendedores.get_children():
            self.tree_revendedores.delete(item)
        
        # Inserir cada revendedor
        for rev_id, rev_data in self.revendedores.items():
            self.tree_revendedores.insert(
                "",
                "end",
                iid=rev_id,
                text=str(rev_id),
                values=(
                    rev_data["nome"],
                    rev_data["contato"],
                    rev_data["endereco"],
                    f"{rev_data['comissao']}%"
                )
            )
    
    def _abrir_dialog_novo_revendedor(self):
        """
        Abre um diálogo para cadastrar um novo revendedor.
        Cria uma janela flutuante com campos para preencher.
        """
        dialog = ctk.CTkToplevel(self)
        dialog.title("Novo Revendedor")
        dialog.geometry("400x350")
        dialog.resizable(False, False)
        
        # Centralizar dialog
        dialog.grab_set()
        
        # Frame de campos
        frame = ctk.CTkFrame(dialog, fg_color=theme.COR_FUNDO)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        frame.grid_columnconfigure(0, weight=1)
        
        # Campo: Nome
        ctk.CTkLabel(frame, text="Nome", text_color=theme.COR_TEXTO).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        entry_nome = ctk.CTkEntry(frame, placeholder_text="Ex: João's Sorveteria")
        entry_nome.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        
        # Campo: Contato
        ctk.CTkLabel(frame, text="Contato (Telefone/Email)", text_color=theme.COR_TEXTO).grid(
            row=2, column=0, sticky="w", pady=(0, 5)
        )
        entry_contato = ctk.CTkEntry(frame, placeholder_text="(xx) 99999-9999")
        entry_contato.grid(row=3, column=0, sticky="ew", pady=(0, 15))
        
        # Campo: Endereço
        ctk.CTkLabel(frame, text="Endereço", text_color=theme.COR_TEXTO).grid(
            row=4, column=0, sticky="w", pady=(0, 5)
        )
        entry_endereco = ctk.CTkEntry(frame, placeholder_text="Rua..., Cidade")
        entry_endereco.grid(row=5, column=0, sticky="ew", pady=(0, 15))
        
        # Campo: Comissão (%)
        ctk.CTkLabel(frame, text="Comissão (%)", text_color=theme.COR_TEXTO).grid(
            row=6, column=0, sticky="w", pady=(0, 5)
        )
        entry_comissao = ctk.CTkEntry(frame, placeholder_text="Ex: 15")
        entry_comissao.grid(row=7, column=0, sticky="ew", pady=(0, 20))
        
        # Frame de botões
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=8, column=0, sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        
        def salvar():
            nome = entry_nome.get().strip()
            contato = entry_contato.get().strip()
            endereco = entry_endereco.get().strip()
            comissao = entry_comissao.get().strip()
            
            # Validar
            if not nome or not contato or not endereco or not comissao:
                messagebox.showerror("Erro", "Preencha todos os campos!")
                return
            
            try:
                comissao = float(comissao)
                if comissao < 0 or comissao > 100:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Erro", "Comissão deve ser um número entre 0 e 100!")
                return
            
            # Adicionar revendedor
            novo_id = max(self.revendedores.keys()) + 1 if self.revendedores else 1
            self.revendedores[novo_id] = {
                "nome": nome,
                "contato": contato,
                "endereco": endereco,
                "comissao": comissao,
                "data_cadastro": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            
            self._atualizar_tree_revendedores()
            messagebox.showinfo("Sucesso", "Revendedor cadastrado com sucesso!")
            dialog.destroy()
        
        ctk.CTkButton(btn_frame, text="Salvar", command=salvar).pack(
            side="right", padx=(5, 0)
        )
        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            fg_color="gray",
            command=dialog.destroy
        ).pack(side="right")
    
    def _editar_revendedor(self):
        """
        Abre diálogo para editar um revendedor selecionado.
        Verifica se há seleção e preenche campos com dados atuais.
        """
        selection = self.tree_revendedores.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um revendedor!")
            return
        
        rev_id = int(selection[0])
        rev_data = self.revendedores[rev_id]
        
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Editar Revendedor - {rev_data['nome']}")
        dialog.geometry("400x350")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        frame = ctk.CTkFrame(dialog, fg_color=theme.COR_FUNDO)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        frame.grid_columnconfigure(0, weight=1)
        
        # Campos pré-preenchidos
        ctk.CTkLabel(frame, text="Nome", text_color=theme.COR_TEXTO).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        entry_nome = ctk.CTkEntry(frame)
        entry_nome.insert(0, rev_data["nome"])
        entry_nome.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        
        ctk.CTkLabel(frame, text="Contato", text_color=theme.COR_TEXTO).grid(
            row=2, column=0, sticky="w", pady=(0, 5)
        )
        entry_contato = ctk.CTkEntry(frame)
        entry_contato.insert(0, rev_data["contato"])
        entry_contato.grid(row=3, column=0, sticky="ew", pady=(0, 15))
        
        ctk.CTkLabel(frame, text="Endereço", text_color=theme.COR_TEXTO).grid(
            row=4, column=0, sticky="w", pady=(0, 5)
        )
        entry_endereco = ctk.CTkEntry(frame)
        entry_endereco.insert(0, rev_data["endereco"])
        entry_endereco.grid(row=5, column=0, sticky="ew", pady=(0, 15))
        
        ctk.CTkLabel(frame, text="Comissão (%)", text_color=theme.COR_TEXTO).grid(
            row=6, column=0, sticky="w", pady=(0, 5)
        )
        entry_comissao = ctk.CTkEntry(frame)
        entry_comissao.insert(0, str(rev_data["comissao"]))
        entry_comissao.grid(row=7, column=0, sticky="ew", pady=(0, 20))
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=8, column=0, sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        
        def atualizar():
            nome = entry_nome.get().strip()
            contato = entry_contato.get().strip()
            endereco = entry_endereco.get().strip()
            comissao = entry_comissao.get().strip()
            
            if not nome or not contato or not endereco or not comissao:
                messagebox.showerror("Erro", "Preencha todos os campos!")
                return
            
            try:
                comissao = float(comissao)
                if comissao < 0 or comissao > 100:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Erro", "Comissão inválida!")
                return
            
            self.revendedores[rev_id].update({
                "nome": nome,
                "contato": contato,
                "endereco": endereco,
                "comissao": comissao
            })
            
            self._atualizar_tree_revendedores()
            messagebox.showinfo("Sucesso", "Revendedor atualizado!")
            dialog.destroy()
        
        ctk.CTkButton(btn_frame, text="Salvar", command=atualizar).pack(
            side="right", padx=(5, 0)
        )
        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            fg_color="gray",
            command=dialog.destroy
        ).pack(side="right")
    
    def _deletar_revendedor(self):
        """
        Deleta um revendedor selecionado com confirmação.
        Pede aprovação antes de remover permanentemente.
        """
        selection = self.tree_revendedores.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um revendedor!")
            return
        
        rev_id = int(selection[0])
        rev_nome = self.revendedores[rev_id]["nome"]
        
        if messagebox.askyesno("Confirmar", f"Deletar '{rev_nome}'?"):
            del self.revendedores[rev_id]
            self._atualizar_tree_revendedores()
            messagebox.showinfo("Sucesso", "Revendedor deletado!")
    
    # ========================================
    # SEÇÃO 3: ABA "REGISTRAR VENDA"
    # ========================================
    
    def _render_aba_venda(self, parent):
        """
        Aba para registrar uma venda para um revendedor.
        Permite selecionar revendedor, produtos, quantidade e calcula comissão.
        """
        parent.grid_rowconfigure(3, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Seção: Selecionar revendedor
        ctk.CTkLabel(
            parent,
            text="Selecione o Revendedor",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        rev_names = ["Selecionar..."] + [
            r["nome"] for r in self.revendedores.values()
        ]
        self.combo_revendedor = ctk.CTkComboBox(
            parent,
            values=rev_names,
            state="readonly",
            width=300
        )
        self.combo_revendedor.set("Selecionar...")
        self.combo_revendedor.grid(row=0, column=0, padx=20, pady=(30, 20), sticky="ew")
        
        # Seção: Seleção de produtos
        ctk.CTkLabel(
            parent,
            text="Adicione Produtos à Venda",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=1, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Frame para seleção de produto
        prod_frame = ctk.CTkFrame(parent, fg_color="transparent")
        prod_frame.grid(row=1, column=0, padx=20, pady=(30, 10), sticky="ew")
        prod_frame.grid_columnconfigure(1, weight=1)
        
        self.combo_produto = ctk.CTkComboBox(
            prod_frame,
            values=list(self.produtos.keys()),
            state="readonly"
        )
        self.combo_produto.set("Selecionar produto...")
        self.combo_produto.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        ctk.CTkLabel(
            prod_frame,
            text="Qtd:",
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=2, padx=(10, 5))
        
        self.entry_qtd = ctk.CTkEntry(prod_frame, width=60, placeholder_text="1")
        self.entry_qtd.grid(row=0, column=3, padx=(0, 10))
        
        ctk.CTkButton(
            prod_frame,
            text="+ Adicionar",
            width=100,
            command=self._adicionar_produto_venda
        ).grid(row=0, column=4)
        
        # Tabela de produtos na venda
        ctk.CTkLabel(
            parent,
            text="Produtos da Venda",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=2, column=0, padx=20, pady=(20, 10), sticky="w")
        
        table_frame = ctk.CTkFrame(parent, fg_color=theme.COR_PAINEL)
        table_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        style = ttk.Style()
        style.configure("Treeview", font=(theme.FONTE, 10), rowheight=24)
        
        self.tree_venda = ttk.Treeview(
            table_frame,
            columns=("preco", "qtd", "total"),
            show="tree headings",
            height=8
        )
        self.tree_venda.heading("#0", text="Produto")
        self.tree_venda.heading("preco", text="Preço")
        self.tree_venda.heading("qtd", text="Qtd")
        self.tree_venda.heading("total", text="Total")
        
        self.tree_venda.column("#0", width=200)
        self.tree_venda.column("preco", width=100)
        self.tree_venda.column("qtd", width=60)
        self.tree_venda.column("total", width=100)
        
        self.tree_venda.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_venda.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        self.tree_venda.configure(yscroll=scrollbar.set)
        
        self.venda_atual = []  # Armazenar produtos da venda atual
        
        # Seção: Resumo e finalização
        resumo_frame = ctk.CTkFrame(parent, fg_color=theme.COR_PAINEL, corner_radius=10)
        resumo_frame.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")
        resumo_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            resumo_frame,
            text="Total da Venda:",
            font=ctk.CTkFont(family=theme.FONTE, size=11, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        self.label_total_venda = ctk.CTkLabel(
            resumo_frame,
            text="R$ 0,00",
            font=ctk.CTkFont(family=theme.FONTE, size=11),
            text_color=theme.COR_SUCESSO
        )
        self.label_total_venda.grid(row=0, column=1, padx=15, pady=10, sticky="e")
        
        ctk.CTkLabel(
            resumo_frame,
            text="Comissão (%):",
            font=ctk.CTkFont(family=theme.FONTE, size=11, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=1, column=0, padx=15, pady=10, sticky="w")
        
        self.label_comissao_valor = ctk.CTkLabel(
            resumo_frame,
            text="R$ 0,00",
            font=ctk.CTkFont(family=theme.FONTE, size=11),
            text_color=theme.COR_SUCESSO
        )
        self.label_comissao_valor.grid(row=1, column=1, padx=15, pady=10, sticky="e")
        
        # Botões
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkButton(
            btn_frame,
            text="Limpar",
            width=100,
            fg_color="gray",
            command=self._limpar_venda
        ).pack(side="right", padx=(5, 0))
        
        ctk.CTkButton(
            btn_frame,
            text="Finalizar Venda",
            width=150,
            command=self._finalizar_venda
        ).pack(side="right")
    
    def _adicionar_produto_venda(self):
        """
        Adiciona um produto selecionado à venda atual.
        Valida quantidade e atualiza a tabela de produtos.
        """
        produto = self.combo_produto.get()
        if produto == "Selecionar produto...":
            messagebox.showwarning("Aviso", "Selecione um produto!")
            return
        
        qtd_str = self.entry_qtd.get().strip()
        if not qtd_str:
            qtd_str = "1"
        
        try:
            qtd = int(qtd_str)
            if qtd <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Quantidade inválida!")
            return
        
        preco = self.produtos[produto]
        total = preco * qtd
        
        # Adicionar à venda
        self.venda_atual.append({
            "produto": produto,
            "preco": preco,
            "qtd": qtd,
            "total": total
        })
        
        # Atualizar Tree
        self.tree_venda.insert(
            "",
            "end",
            text=produto,
            values=(
                f"R$ {preco:.2f}".replace(".", ","),
                qtd,
                f"R$ {total:.2f}".replace(".", ",")
            )
        )
        
        self.combo_produto.set("Selecionar produto...")
        self.entry_qtd.delete(0, "end")
        self.entry_qtd.insert(0, "1")
        
        self._atualizar_resumo_venda()
    
    def _atualizar_resumo_venda(self):
        """
        Recalcula o total da venda, comissão e atualiza os labels.
        Chamado após adicionar ou remover produtos.
        """
        total_venda = sum(item["total"] for item in self.venda_atual)
        
        # Obter comissão do revendedor selecionado
        rev_nome = self.combo_revendedor.get()
        comissao_pct = 0
        
        if rev_nome != "Selecionar...":
            for rev in self.revendedores.values():
                if rev["nome"] == rev_nome:
                    comissao_pct = rev["comissao"]
                    break
        
        comissao_valor = (total_venda * comissao_pct) / 100
        
        # Atualizar labels
        self.label_total_venda.configure(
            text=f"R$ {total_venda:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        self.label_comissao_valor.configure(
            text=f"R$ {comissao_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
    
    def _limpar_venda(self):
        """
        Limpa todos os produtos da venda atual e reseta a interface.
        """
        for item in self.tree_venda.get_children():
            self.tree_venda.delete(item)
        self.venda_atual = []
        self.combo_produto.set("Selecionar produto...")
        self.entry_qtd.delete(0, "end")
        self.entry_qtd.insert(0, "1")
        self._atualizar_resumo_venda()
    
    def _finalizar_venda(self):
        """
        Finaliza a venda registrando no histórico.
        Valida dados e cria registro com timestamp.
        """
        rev_nome = self.combo_revendedor.get()
        if rev_nome == "Selecionar...":
            messagebox.showwarning("Aviso", "Selecione um revendedor!")
            return
        
        if not self.venda_atual:
            messagebox.showwarning("Aviso", "Adicione produtos à venda!")
            return
        
        # Calcular totais
        total_venda = sum(item["total"] for item in self.venda_atual)
        
        # Obter comissão
        comissao_pct = 0
        rev_id = None
        for rid, rev in self.revendedores.items():
            if rev["nome"] == rev_nome:
                comissao_pct = rev["comissao"]
                rev_id = rid
                break
        
        comissao_valor = (total_venda * comissao_pct) / 100
        
        # Registrar venda
        nova_venda_id = max(self.vendas.keys()) + 1 if self.vendas else 1
        self.vendas[nova_venda_id] = {
            "revendedor_id": rev_id,
            "revendedor_nome": rev_nome,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "produtos": self.venda_atual.copy(),
            "total": total_venda,
            "comissao_pct": comissao_pct,
            "comissao_valor": comissao_valor
        }
        
        messagebox.showinfo(
            "Sucesso",
            f"Venda registrada!\n\nTotal: R$ {total_venda:.2f}\nComissão: R$ {comissao_valor:.2f}"
        )
        
        self._limpar_venda()
    
    # ========================================
    # SEÇÃO 4: ABA "HISTÓRICO"
    # ========================================
    
    def _render_aba_historico(self, parent):
        """
        Aba que exibe o histórico de todas as vendas para revendedores.
        Mostra data, revendedor, total e comissão.
        """
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Filtro por revendedor
        filter_frame = ctk.CTkFrame(parent, fg_color="transparent")
        filter_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        ctk.CTkLabel(
            filter_frame,
            text="Filtrar por Revendedor:",
            text_color=theme.COR_TEXTO
        ).pack(side="left", padx=(0, 10))
        
        rev_names = ["Todos"] + [r["nome"] for r in self.revendedores.values()]
        self.combo_filtro_rev = ctk.CTkComboBox(
            filter_frame,
            values=rev_names,
            state="readonly",
            width=250,
            command=self._atualizar_tree_historico
        )
        self.combo_filtro_rev.set("Todos")
        self.combo_filtro_rev.pack(side="left")
        
        # Tabela de histórico
        table_frame = ctk.CTkFrame(parent, fg_color=theme.COR_PAINEL)
        table_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        style = ttk.Style()
        style.configure("Treeview", font=(theme.FONTE, 10), rowheight=26)
        
        self.tree_historico = ttk.Treeview(
            table_frame,
            columns=("data", "revendedor", "total", "comissao"),
            show="tree headings",
            height=15
        )
        
        self.tree_historico.heading("#0", text="ID")
        self.tree_historico.heading("data", text="Data/Hora")
        self.tree_historico.heading("revendedor", text="Revendedor")
        self.tree_historico.heading("total", text="Total Venda")
        self.tree_historico.heading("comissao", text="Comissão")
        
        self.tree_historico.column("#0", width=50)
        self.tree_historico.column("data", width=140)
        self.tree_historico.column("revendedor", width=150)
        self.tree_historico.column("total", width=120)
        self.tree_historico.column("comissao", width=120)
        
        self.tree_historico.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree_historico.yview
        )
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        self.tree_historico.configure(yscroll=scrollbar.set)
        
        # Preencher tabela
        self._atualizar_tree_historico()
    
    def _atualizar_tree_historico(self, *args):
        """
        Atualiza a tabela de histórico com vendas filtradas.
        Filtra por revendedor selecionado se não for "Todos".
        """
        for item in self.tree_historico.get_children():
            self.tree_historico.delete(item)
        
        filtro = self.combo_filtro_rev.get()
        
        for venda_id, venda in self.vendas.items():
            # Aplicar filtro
            if filtro != "Todos" and venda["revendedor_nome"] != filtro:
                continue
            
            self.tree_historico.insert(
                "",
                "end",
                text=str(venda_id),
                values=(
                    venda["data"],
                    venda["revendedor_nome"],
                    f"R$ {venda['total']:.2f}".replace(".", ","),
                    f"R$ {venda['comissao_valor']:.2f}".replace(".", ",")
                )
            )
    
    # ========================================
    # SEÇÃO 5: ABA "RELATÓRIO"
    # ========================================
    
    def _render_aba_relatorio(self, parent):
        """
        Aba de relatório que exibe estatísticas e totalizações de revenda.
        Mostra faturamento total, comissões pagas e desempenho por revendedor.
        """
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)
        
        # Título
        ctk.CTkLabel(
            parent,
            text="Relatório de Revenda",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=20, pady=(20, 20), sticky="w")
        
        # Cards de resumo
        cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        cards_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Calcular métricas
        total_faturamento = sum(v["total"] for v in self.vendas.values())
        total_comissoes = sum(v["comissao_valor"] for v in self.vendas.values())
        num_vendas = len(self.vendas)
        
        # Card 1: Total Faturado
        self._criar_card_relatorio(
            cards_frame, 0,
            "Total Faturado",
            f"R$ {total_faturamento:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        
        # Card 2: Total Comissões
        self._criar_card_relatorio(
            cards_frame, 1,
            "Total de Comissões",
            f"R$ {total_comissoes:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        
        # Card 3: Número de Vendas
        self._criar_card_relatorio(
            cards_frame, 2,
            "Vendas Registradas",
            str(num_vendas)
        )
        
        # Tabela de desempenho por revendedor
        ctk.CTkLabel(
            parent,
            text="Desempenho por Revendedor",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=2, column=0, padx=20, pady=(20, 10), sticky="w")
        
        table_frame = ctk.CTkFrame(parent, fg_color=theme.COR_PAINEL)
        table_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        style = ttk.Style()
        style.configure("Treeview", font=(theme.FONTE, 10), rowheight=26)
        
        tree = ttk.Treeview(
            table_frame,
            columns=("vendas", "total", "comissao"),
            show="tree headings",
            height=10
        )
        
        tree.heading("#0", text="Revendedor")
        tree.heading("vendas", text="# Vendas")
        tree.heading("total", text="Total Faturado")
        tree.heading("comissao", text="Total Comissão")
        
        tree.column("#0", width=200)
        tree.column("vendas", width=100)
        tree.column("total", width=150)
        tree.column("comissao", width=150)
        
        # Agregar dados por revendedor
        dados_rev = {}
        for venda in self.vendas.values():
            rev_nome = venda["revendedor_nome"]
            if rev_nome not in dados_rev:
                dados_rev[rev_nome] = {
                    "vendas": 0,
                    "total": 0,
                    "comissao": 0
                }
            dados_rev[rev_nome]["vendas"] += 1
            dados_rev[rev_nome]["total"] += venda["total"]
            dados_rev[rev_nome]["comissao"] += venda["comissao_valor"]
        
        # Inserir dados
        for rev_nome, dados in sorted(dados_rev.items()):
            tree.insert(
                "",
                "end",
                text=rev_nome,
                values=(
                    dados["vendas"],
                    f"R$ {dados['total']:.2f}".replace(".", ","),
                    f"R$ {dados['comissao']:.2f}".replace(".", ",")
                )
            )
        
        tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        tree.configure(yscroll=scrollbar.set)
    
    def _criar_card_relatorio(self, parent, column, titulo, valor):
        """
        Cria um card visual para exibir uma métrica.
        Usado no relatório para mostrar totalizações.
        
        Args:
            parent: Frame pai para o card
            column: Coluna onde posicionar o card
            titulo: Texto do título
            valor: Valor principal a exibir
        """
        card = ctk.CTkFrame(parent, fg_color=theme.COR_PAINEL, corner_radius=10)
        card.grid(row=0, column=column, padx=5, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            card,
            text=titulo,
            font=ctk.CTkFont(family=theme.FONTE, size=10),
            text_color=theme.COR_TEXTO_SEC
        ).pack(pady=(12, 4), padx=10)
        
        ctk.CTkLabel(
            card,
            text=valor,
            font=ctk.CTkFont(family=theme.FONTE, size=16, weight="bold"),
            text_color=theme.COR_SUCESSO
        ).pack(pady=(0, 12), padx=10)
    
    # ========================================
    # SEÇÃO 6: DADOS MOCK
    # ========================================
    
    def _mock_revendedores(self):
        """
        Retorna dados de exemplo de revendedores para testes.
        No banco de dados real, viria do banco.
        """
        return {
            1: {
                "nome": "Sorveteria João",
                "contato": "(91) 99999-1111",
                "endereco": "Rua das Flores, 100 - Belém",
                "comissao": 15.0,
                "data_cadastro": "01/01/2024 10:00"
            },
            2: {
                "nome": "Gelados & Cia",
                "contato": "(91) 98888-2222",
                "endereco": "Av. Brasil, 250 - Belém",
                "comissao": 12.0,
                "data_cadastro": "05/01/2024 14:30"
            },
            3: {
                "nome": "Sorve-Tudo",
                "contato": "(91) 97777-3333",
                "endereco": "Praça da República, 50 - Belém",
                "comissao": 18.0,
                "data_cadastro": "10/01/2024 09:15"
            }
        }
    
    def _mock_vendas(self):
        """
        Retorna dados de exemplo de vendas para testes.
        No banco real, viria do banco de dados.
        """
        return {
            1: {
                "revendedor_id": 1,
                "revendedor_nome": "Sorveteria João",
                "data": "22/02/2026 10:30",
                "produtos": [
                    {"produto": "Sorvete Morango", "preco": 12.00, "qtd": 5, "total": 60.00},
                    {"produto": "Picolé Frutas", "preco": 5.00, "qtd": 10, "total": 50.00}
                ],
                "total": 110.00,
                "comissao_pct": 15.0,
                "comissao_valor": 16.50
            },
            2: {
                "revendedor_id": 2,
                "revendedor_nome": "Gelados & Cia",
                "data": "23/02/2026 14:15",
                "produtos": [
                    {"produto": "Açaí Premium", "preco": 25.00, "qtd": 3, "total": 75.00}
                ],
                "total": 75.00,
                "comissao_pct": 12.0,
                "comissao_valor": 9.00
            }
        }
    
    def _mock_produtos(self):
        """
        Retorna produtos disponíveis para venda.
        Formato: {nome: preço}
        """
        return {
            "Sorvete Morango": 12.00,
            "Sorvete Chocolate": 12.00,
            "Sorvete Baunilha": 11.00,
            "Picolé Frutas": 5.00,
            "Picolé Açaí": 6.00,
            "Açaí Premium": 25.00,
            "Açaí Tradicional": 20.00,
            "Paleta Gelada": 3.50
        }
