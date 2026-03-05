# -*- coding: utf-8 -*-
"""
Página com abas:
  - Agendamentos de carrinhos
  - Agenda do dia
  - Delivery
  - Carrinhos (CRUD)
  - Motoristas (CRUD)

Requisitos: customtkinter, tkinter
"""

from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk, messagebox
import datetime as dt

from app.config import theme


# ===========================================================
# DELIVERY (inalterado)
# ===========================================================
try:
    from app.pages.servicos.delivery_inalterado import PaginaDelivery
except Exception:
    class PaginaDelivery(ctk.CTkFrame):
        def __init__(self, master, sistema):
            super().__init__(master, fg_color=theme.COR_FUNDO)
            ctk.CTkLabel(
                self,
                text="Delivery não carregado",
                font=ctk.CTkFont(family=theme.FONTE, size=16, weight="bold"),
                text_color=theme.COR_TEXTO
            ).pack(padx=20, pady=(20, 6), anchor="w")

            ctk.CTkLabel(
                self,
                text="Crie o arquivo app/pages/servicos/delivery_inalterado.py "
                     "e mova sua classe PaginaDelivery atual para lá.",
                font=ctk.CTkFont(family=theme.FONTE, size=12),
                text_color=theme.COR_TEXTO_SEC,
                wraplength=900,
                justify="left"
            ).pack(padx=20, pady=(0, 20), anchor="w")


# ===========================================================
# HELPERS UI
# ===========================================================
_STYLE_OK = False


def _ensure_tree_styles():
    """
    Configura estilos ttk para Treeview (compatível com theme).
    Executa uma vez por arquivo, para evitar reconfigurações repetidas.
    """
    global _STYLE_OK
    if _STYLE_OK:
        return
    _STYLE_OK = True

    try:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Carrinhos CRUD
        style.configure(
            "Geladoce.Treeview",
            font=(theme.FONTE, 11),
            rowheight=32,
            background=theme.COR_BOTAO,
            fieldbackground=theme.COR_BOTAO,
            foreground=theme.COR_TEXTO,
            borderwidth=0,
            relief="flat",
        )
        style.configure(
            "Geladoce.Treeview.Heading",
            font=(theme.FONTE, 11, "bold"),
            background=theme.COR_PAINEL,
            foreground=theme.COR_TEXTO,
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Geladoce.Treeview",
            background=[("selected", theme.COR_SELECIONADO)],
            foreground=[("selected", theme.COR_TEXTO)],
        )

        # Agenda/Agendamentos (mesmo estilo)
        style.configure(
            "Geladoce.Agenda.Treeview",
            font=(theme.FONTE, 11),
            rowheight=34,
            background=theme.COR_BOTAO,
            fieldbackground=theme.COR_BOTAO,
            foreground=theme.COR_TEXTO,
            borderwidth=0,
            relief="flat",
        )
        style.configure(
            "Geladoce.Agenda.Treeview.Heading",
            font=(theme.FONTE, 11, "bold"),
            background=theme.COR_PAINEL,
            foreground=theme.COR_TEXTO,
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Geladoce.Agenda.Treeview",
            background=[("selected", theme.COR_SELECIONADO)],
            foreground=[("selected", theme.COR_TEXTO)],
        )

    except Exception:
        # se der qualquer erro no ttk Style, a UI ainda funciona
        pass


def _digits(valor: str) -> str:
    return "".join(ch for ch in str(valor or "") if ch.isdigit())


# ===========================================================
# ABA EXTRA: CRUD CARRINHOS
# ===========================================================
class PaginaCadastroCarrinhos(ctk.CTkFrame):
    def __init__(self, master, sistema=None, on_changed=None):
        super().__init__(master, fg_color=theme.COR_FUNDO)
        _ensure_tree_styles()

        self.sistema = sistema
        self.on_changed = on_changed

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        self.termo_var = ctk.StringVar(value="")
        self.status_filtro_var = ctk.StringVar(value="Todos")

        self.id_externo_var = ctk.StringVar(value="")
        self.nome_var = ctk.StringVar(value="")
        self.capacidade_var = ctk.StringVar(value="0")
        self.status_var = ctk.StringVar(value="Disponível")
        self.qtd_lote_var = ctk.StringVar(value="1")

        self._em_edicao_id = None

        self.tree = None
        self._frame_tree = None

        self._montar_ui()
        self._render()

    def _montar_ui(self):
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.grid(row=0, column=0, columnspan=2, padx=18, pady=(14, 10), sticky="ew")
        topo.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            topo,
            text="Carrinhos",
            font=ctk.CTkFont(family=theme.FONTE, size=18, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, sticky="w")

        # LEFT
        left = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        left.grid(row=1, column=0, padx=(18, 10), pady=(0, 18), sticky="nsew")
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(2, weight=1)

        filtros = ctk.CTkFrame(left, fg_color="transparent")
        filtros.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="ew")
        filtros.grid_columnconfigure(0, weight=1)

        ent = ctk.CTkEntry(
            filtros,
            textvariable=self.termo_var,
            placeholder_text="🔎 Buscar por nome/ID externo…",
            height=34,
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        )
        ent.grid(row=0, column=0, sticky="ew")
        ent.bind("<KeyRelease>", lambda e: self._render())

        combo = ctk.CTkComboBox(
            filtros,
            values=["Todos", "Disponível", "Em rota", "Manutenção"],
            width=160,
            variable=self.status_filtro_var,
            command=lambda _: self._render(),
            fg_color=theme.COR_BOTAO,
            button_color=theme.COR_SELECIONADO,
            button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_BOTAO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        )
        combo.set("Todos")
        combo.grid(row=0, column=1, padx=(10, 0))

        ctk.CTkLabel(
            left,
            text="Lista",
            font=ctk.CTkFont(family=theme.FONTE, size=13, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=1, column=0, padx=12, pady=(0, 6), sticky="w")

        self._frame_tree = ctk.CTkFrame(left, fg_color=theme.COR_BOTAO, corner_radius=12)
        self._frame_tree.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self._frame_tree.grid_columnconfigure(0, weight=1)
        self._frame_tree.grid_rowconfigure(0, weight=1)
        self._frame_tree.bind("<Configure>", self._ajustar_colunas_tree)

        self.tree = ttk.Treeview(
            self._frame_tree,
            columns=("idext", "status", "cap"),
            show="headings",
            style="Geladoce.Treeview",
        )
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)

        self.tree.heading("idext", text="ID Externo", anchor="w")
        self.tree.heading("status", text="Status", anchor="w")
        self.tree.heading("cap", text="Capacidade", anchor="w")
        self.tree.bind("<Double-1>", lambda e: self._carregar_edicao())

        scroll = ttk.Scrollbar(self._frame_tree, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns", padx=(8, 8), pady=8)
        self.tree.configure(yscrollcommand=scroll.set)

        # RIGHT
        right = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        right.grid(row=1, column=1, padx=(10, 18), pady=(0, 18), sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right,
            text="Novo / Editar",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        form = ctk.CTkFrame(right, fg_color=theme.COR_BOTAO, corner_radius=12)
        form.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="ew")
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="ID externo (opcional)", text_color=theme.COR_TEXTO).grid(
            row=0, column=0, padx=10, pady=(10, 4), sticky="w"
        )
        ctk.CTkLabel(form, text="Status", text_color=theme.COR_TEXTO).grid(
            row=0, column=1, padx=10, pady=(10, 4), sticky="w"
        )

        ctk.CTkEntry(
            form,
            textvariable=self.id_externo_var,
            height=34,
            placeholder_text="CAR-0001 (vazio = automático)",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        ).grid(row=1, column=0, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkComboBox(
            form,
            values=["Disponível", "Em rota", "Manutenção"],
            variable=self.status_var,
            height=34,
            fg_color=theme.COR_BOTAO,
            button_color=theme.COR_SELECIONADO,
            button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_BOTAO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        ).grid(row=1, column=1, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(form, text="Nome", text_color=theme.COR_TEXTO).grid(
            row=2, column=0, padx=10, pady=(6, 4), sticky="w"
        )
        ctk.CTkLabel(form, text="Capacidade", text_color=theme.COR_TEXTO).grid(
            row=2, column=1, padx=10, pady=(6, 4), sticky="w"
        )

        ctk.CTkEntry(
            form,
            textvariable=self.nome_var,
            height=34,
            placeholder_text="Ex.: Carrinho Picolé",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        ).grid(row=3, column=0, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkEntry(
            form,
            textvariable=self.capacidade_var,
            height=34,
            placeholder_text="0",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        ).grid(row=3, column=1, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(form, text="Quantidade (cadastro em lote)", text_color=theme.COR_TEXTO).grid(
            row=4, column=0, padx=10, pady=(6, 4), sticky="w"
        )
        ctk.CTkEntry(
            form,
            textvariable=self.qtd_lote_var,
            height=34,
            placeholder_text="1",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        ).grid(row=5, column=0, padx=10, pady=(0, 10), sticky="ew")

        linha_btns = ctk.CTkFrame(right, fg_color="transparent")
        linha_btns.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="ew")
        linha_btns.grid_columnconfigure(0, weight=1)
        linha_btns.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            linha_btns,
            text="Salvar",
            height=36,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._salvar,
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            linha_btns,
            text="Limpar",
            height=36,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._limpar,
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        ctk.CTkButton(
            right,
            text="Inativar selecionado",
            height=36,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._inativar,
        ).grid(row=3, column=0, padx=12, pady=(0, 12), sticky="ew")

    def _ajustar_colunas_tree(self, event=None):
        if not self.tree or not self._frame_tree:
            return
        largura = max(self._frame_tree.winfo_width() - 28, 340)
        c1 = int(largura * 0.45)
        c2 = int(largura * 0.30)
        c3 = max(largura - c1 - c2, 80)
        self.tree.column("idext", width=c1, anchor="w")
        self.tree.column("status", width=c2, anchor="w")
        self.tree.column("cap", width=c3, anchor="w")

    def _listar(self):
        if not self.sistema:
            return []
        try:
            return self.sistema.listar_carrinhos(
                termo=self.termo_var.get().strip(),
                status=self.status_filtro_var.get().strip()
            )
        except Exception:
            return []

    def _render(self):
        if not self.tree:
            return
        for i in self.tree.get_children():
            self.tree.delete(i)

        itens = self._listar()
        for c in itens:
            self.tree.insert(
                "",
                "end",
                values=(
                    c.get("id_externo") or "",   # id_externo pode ser None
                    c.get("status") or "",
                    c.get("capacidade") or 0
                ),
                tags=(f'id-{c.get("id")}',)
            )

    def _id_selecionado(self):
        sel = self.tree.selection()
        if not sel:
            return None
        tags = self.tree.item(sel[0], "tags")
        for t in tags:
            if str(t).startswith("id-"):
                return int(str(t).split("-")[1])
        return None

    def _carregar_edicao(self):
        cid = self._id_selecionado()
        if cid is None or not self.sistema:
            return
        try:
            c = self.sistema.obter_carrinho(cid)
        except Exception:
            c = None
        if not c:
            return

        self._em_edicao_id = cid
        self.id_externo_var.set(c.get("id_externo") or "")
        self.nome_var.set(c.get("nome") or "")
        self.capacidade_var.set(str(c.get("capacidade") or 0))
        self.status_var.set(c.get("status") or "Disponível")
        self.qtd_lote_var.set("1")

    def _salvar(self):
        if not self.sistema:
            return

        nome = self.nome_var.get().strip()
        if not nome:
            messagebox.showwarning("Validação", "Informe o nome do carrinho.")
            return

        try:
            cap = int(self.capacidade_var.get().strip() or "0")
        except ValueError:
            messagebox.showwarning("Validação", "Capacidade inválida.")
            return

        st = self.status_var.get().strip()

        # ✅ REGRA CRÍTICA: nunca enviar "" para id_externo
        idext = self.id_externo_var.get().strip() or None

        try:
            qtd = int(self.qtd_lote_var.get().strip() or "1")
            if qtd <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Validação", "Quantidade inválida.")
            return

        try:
            if self._em_edicao_id is not None:
                # edição: se idext=None, mantém o atual no repo/service
                self.sistema.salvar_carrinho(
                    nome=nome,
                    capacidade=cap,
                    status=st,
                    id_externo=idext,
                    carrinho_id=self._em_edicao_id
                )
            else:
                # ✅ cadastro em lote: SEMPRE gerar automático para evitar duplicidade
                if qtd > 1 and idext is not None:
                    messagebox.showwarning(
                        "Aviso",
                        "Cadastro em lote: o ID externo deve ficar vazio para gerar automaticamente.\n"
                        "O sistema vai gerar CAR-0001, CAR-0002, ..."
                    )
                for _ in range(qtd):
                    self.sistema.salvar_carrinho(
                        nome=nome,
                        capacidade=cap,
                        status=st,
                        id_externo=None,     # <<< aqui está a correção principal
                        carrinho_id=None
                    )

            self._render()
            self._limpar()

            if callable(self.on_changed):
                self.on_changed()

            messagebox.showinfo("Carrinhos", "Carrinho(s) salvo(s) com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar carrinho(s).\n\n{e}")

    def _inativar(self):
        cid = self._id_selecionado()
        if cid is None or not self.sistema:
            messagebox.showwarning("Inativar", "Selecione um carrinho na lista.")
            return
        if not messagebox.askyesno("Confirmar", "Deseja inativar este carrinho?"):
            return
        try:
            self.sistema.excluir_carrinho(cid)
            self._render()
            self._limpar()

            if callable(self.on_changed):
                self.on_changed()

            messagebox.showinfo("Carrinhos", "Carrinho inativado.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao inativar.\n\n{e}")

    def _limpar(self):
        self._em_edicao_id = None
        self.id_externo_var.set("")
        self.nome_var.set("")
        self.capacidade_var.set("0")
        self.status_var.set("Disponível")
        self.qtd_lote_var.set("1")


# ===========================================================
# ABA EXTRA: CRUD MOTORISTAS
# ===========================================================
class PaginaCadastroMotoristas(ctk.CTkFrame):
    def __init__(self, master, sistema=None, on_changed=None):
        super().__init__(master, fg_color=theme.COR_FUNDO)
        _ensure_tree_styles()

        self.sistema = sistema
        self.on_changed = on_changed

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        self.termo_var = ctk.StringVar(value="")

        self.nome_var = ctk.StringVar(value="")
        self.cpf_var = ctk.StringVar(value="")
        self.tel_var = ctk.StringVar(value="")

        self._em_edicao_id = None
        self.tree = None
        self._frame_tree = None

        self._montar_ui()
        self._render()

    def _montar_ui(self):
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.grid(row=0, column=0, columnspan=2, padx=18, pady=(14, 10), sticky="ew")
        topo.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            topo,
            text="Motoristas (externos)",
            font=ctk.CTkFont(family=theme.FONTE, size=18, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, sticky="w")

        left = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        left.grid(row=1, column=0, padx=(18, 10), pady=(0, 18), sticky="nsew")
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(2, weight=1)

        filtros = ctk.CTkFrame(left, fg_color="transparent")
        filtros.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="ew")
        filtros.grid_columnconfigure(0, weight=1)

        ent = ctk.CTkEntry(
            filtros,
            textvariable=self.termo_var,
            placeholder_text="🔎 Buscar por nome/CPF/telefone…",
            height=34,
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        )
        ent.grid(row=0, column=0, sticky="ew")
        ent.bind("<KeyRelease>", lambda e: self._render())

        ctk.CTkLabel(
            left,
            text="Lista",
            font=ctk.CTkFont(family=theme.FONTE, size=13, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=1, column=0, padx=12, pady=(0, 6), sticky="w")

        self._frame_tree = ctk.CTkFrame(left, fg_color=theme.COR_BOTAO, corner_radius=12)
        self._frame_tree.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self._frame_tree.grid_columnconfigure(0, weight=1)
        self._frame_tree.grid_rowconfigure(0, weight=1)
        self._frame_tree.bind("<Configure>", self._ajustar_colunas_tree)

        self.tree = ttk.Treeview(
            self._frame_tree,
            columns=("cpf", "tel"),
            show="tree headings",
            style="Geladoce.Treeview",
        )
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)

        self.tree.heading("#0", text="Nome", anchor="w")
        self.tree.heading("cpf", text="CPF", anchor="w")
        self.tree.heading("tel", text="Telefone", anchor="w")
        self.tree.bind("<Double-1>", lambda e: self._carregar_edicao())

        scroll = ttk.Scrollbar(self._frame_tree, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns", padx=(8, 8), pady=8)
        self.tree.configure(yscrollcommand=scroll.set)

        right = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        right.grid(row=1, column=1, padx=(10, 18), pady=(0, 18), sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right,
            text="Novo / Editar",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        form = ctk.CTkFrame(right, fg_color=theme.COR_BOTAO, corner_radius=12)
        form.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="ew")
        form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(form, text="Nome", text_color=theme.COR_TEXTO).grid(
            row=0, column=0, padx=10, pady=(10, 4), sticky="w"
        )
        ctk.CTkEntry(
            form,
            textvariable=self.nome_var,
            height=34,
            placeholder_text="Nome do motorista",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        ).grid(row=1, column=0, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(form, text="CPF (11 dígitos)", text_color=theme.COR_TEXTO).grid(
            row=2, column=0, padx=10, pady=(6, 4), sticky="w"
        )
        ctk.CTkEntry(
            form,
            textvariable=self.cpf_var,
            height=34,
            placeholder_text="Somente números",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        ).grid(row=3, column=0, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(form, text="Telefone", text_color=theme.COR_TEXTO).grid(
            row=4, column=0, padx=10, pady=(6, 4), sticky="w"
        )
        ctk.CTkEntry(
            form,
            textvariable=self.tel_var,
            height=34,
            placeholder_text="(xx) xxxxx-xxxx",
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
        ).grid(row=5, column=0, padx=10, pady=(0, 10), sticky="ew")

        linha_btns = ctk.CTkFrame(right, fg_color="transparent")
        linha_btns.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="ew")
        linha_btns.grid_columnconfigure(0, weight=1)
        linha_btns.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            linha_btns,
            text="Salvar",
            height=36,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._salvar,
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            linha_btns,
            text="Limpar",
            height=36,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._limpar,
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        ctk.CTkButton(
            right,
            text="Inativar selecionado",
            height=36,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER,
            command=self._inativar,
        ).grid(row=3, column=0, padx=12, pady=(0, 12), sticky="ew")

    def _ajustar_colunas_tree(self, event=None):
        if not self.tree or not self._frame_tree:
            return
        largura = max(self._frame_tree.winfo_width() - 28, 380)
        c0 = int(largura * 0.45)
        c1 = int(largura * 0.25)
        c2 = max(largura - c0 - c1, 120)
        self.tree.column("#0", width=c0, anchor="w")
        self.tree.column("cpf", width=c1, anchor="w")
        self.tree.column("tel", width=c2, anchor="w")

    def _listar(self):
        if not self.sistema:
            return []
        try:
            return self.sistema.listar_motoristas(termo=self.termo_var.get().strip())
        except Exception:
            return []

    def _render(self):
        if not self.tree:
            return
        for i in self.tree.get_children():
            self.tree.delete(i)

        itens = self._listar()
        for m in itens:
            self.tree.insert(
                "",
                "end",
                text=m.get("nome", "") or "",
                values=(m.get("cpf", "") or "", m.get("telefone", "") or ""),
                tags=(f'id-{m.get("id")}',)
            )

    def _id_selecionado(self):
        sel = self.tree.selection()
        if not sel:
            return None
        tags = self.tree.item(sel[0], "tags")
        for t in tags:
            if str(t).startswith("id-"):
                return int(str(t).split("-")[1])
        return None

    def _carregar_edicao(self):
        mid = self._id_selecionado()
        if mid is None or not self.sistema:
            return
        try:
            m = self.sistema.obter_motorista(mid)
        except Exception:
            m = None
        if not m:
            return

        self._em_edicao_id = mid
        self.nome_var.set(m.get("nome", "") or "")
        self.cpf_var.set(m.get("cpf", "") or "")
        self.tel_var.set(m.get("telefone", "") or "")

    def _salvar(self):
        if not self.sistema:
            return

        nome = self.nome_var.get().strip()
        cpf = _digits(self.cpf_var.get())
        tel = self.tel_var.get().strip()

        if not nome:
            messagebox.showwarning("Validação", "Informe o nome.")
            return
        if len(cpf) != 11:
            messagebox.showwarning("Validação", "CPF inválido (11 dígitos).")
            return
        if not tel:
            messagebox.showwarning("Validação", "Informe o telefone.")
            return

        try:
            self.sistema.salvar_motorista(
                nome=nome,
                cpf=cpf,
                telefone=tel,
                motorista_id=self._em_edicao_id
            )
            self._render()
            self._limpar()

            if callable(self.on_changed):
                self.on_changed()

            messagebox.showinfo("Motoristas", "Motorista salvo com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar motorista.\n\n{e}")

    def _inativar(self):
        mid = self._id_selecionado()
        if mid is None or not self.sistema:
            messagebox.showwarning("Inativar", "Selecione um motorista na lista.")
            return
        if not messagebox.askyesno("Confirmar", "Deseja inativar este motorista?"):
            return
        try:
            self.sistema.excluir_motorista(mid)
            self._render()
            self._limpar()

            if callable(self.on_changed):
                self.on_changed()

            messagebox.showinfo("Motoristas", "Motorista inativado.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao inativar.\n\n{e}")

    def _limpar(self):
        self._em_edicao_id = None
        self.nome_var.set("")
        self.cpf_var.set("")
        self.tel_var.set("")


# ===========================================================
# ABA 1: AGENDAMENTOS
# ===========================================================
class PaginaAgendamentoCarrinhos(ctk.CTkFrame):
    """
    - Esquerda: filtros + lista de carrinhos (duplo clique = preferir)
    - Direita: formulário (quantidade + motorista opcional)
    """

    def __init__(self, master, sistema=None, on_open_agenda=None, on_agenda_changed=None):
        super().__init__(master, fg_color=theme.COR_FUNDO)
        _ensure_tree_styles()

        self.sistema = sistema
        self.on_open_agenda = on_open_agenda
        self.on_agenda_changed = on_agenda_changed

        self.grid_columnconfigure(0, weight=3, uniform="ag_cols")
        self.grid_columnconfigure(1, weight=2, uniform="ag_cols")
        self.grid_rowconfigure(0, weight=1)

        self.busca_carrinho_var = ctk.StringVar(value="")
        self.status_carrinho_var = ctk.StringVar(value="Todos")

        hoje = dt.date.today().strftime("%Y-%m-%d")
        self.data_var = ctk.StringVar(value=hoje)
        self.hora_ini_var = ctk.StringVar(value="08:00")
        self.hora_fim_var = ctk.StringVar(value="12:00")
        self.local_var = ctk.StringVar(value="")
        self.status_ag_var = ctk.StringVar(value="Agendado")

        self.qtd_carrinhos_var = ctk.StringVar(value="1")
        self.motorista_var = ctk.StringVar(value="(sem motorista)")

        self.observacoes_widget = None
        self._agendamento_em_edicao_id = None

        self.carrinhos = []
        self.motoristas = []
        self.agendamentos = []

        self.tree_carrinhos = None
        self._frame_tree_carrinhos = None

        self._carregar_dados_operacionais()

        self._painel_carrinhos_ui()
        self._form_agendamento_ui()

        self._atualizar_combos_operacionais()
        self._render_lista_carrinhos()

    def _obter_metodo_sistema(self, *nomes):
        if not self.sistema:
            return None
        for nome in nomes:
            metodo = getattr(self.sistema, nome, None)
            if callable(metodo):
                return metodo
        return None

    def _listar_carrinhos_sistema(self):
        metodo = self._obter_metodo_sistema("listar_carrinhos")
        if not metodo:
            return False, []
        try:
            itens = metodo(termo="", status="Todos")
        except TypeError:
            try:
                itens = metodo()
            except Exception:
                return True, []
        except Exception:
            return True, []

        if not isinstance(itens, list):
            return True, []

        normalizados = []
        for c in itens:
            if not isinstance(c, dict):
                continue
            try:
                cid = int(c.get("id"))
            except Exception:
                continue
            normalizados.append({
                "id": cid,
                "id_externo": str(c.get("id_externo") or f"CAR-{cid:04d}"),
                "nome": str(c.get("nome") or f"Carrinho {cid}"),
                "capacidade": int(c.get("capacidade", 0) or 0),
                "status": str(c.get("status") or "Disponível"),
            })
        return True, normalizados

    def _listar_motoristas_sistema(self):
        metodo = self._obter_metodo_sistema("listar_motoristas")
        if not metodo:
            return False, []
        try:
            itens = metodo(termo="")
        except TypeError:
            try:
                itens = metodo()
            except Exception:
                return True, []
        except Exception:
            return True, []

        if not isinstance(itens, list):
            return True, []

        normalizados = []
        for m in itens:
            if not isinstance(m, dict):
                continue
            try:
                mid = int(m.get("id"))
            except Exception:
                continue
            normalizados.append({
                "id": mid,
                "nome": str(m.get("nome") or f"Motorista {mid}"),
                "telefone": str(m.get("telefone") or ""),
                "cpf": str(m.get("cpf") or ""),
            })
        return True, normalizados

    def _parse_data_agendamento(self, valor):
        if isinstance(valor, dt.date):
            return valor
        if isinstance(valor, str):
            txt = valor.strip()
            for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                try:
                    return dt.datetime.strptime(txt, fmt).date()
                except ValueError:
                    pass
        return None

    def _listar_agendamentos_sistema(self):
        metodo = self._obter_metodo_sistema("listar_agendamentos")
        if not metodo:
            return False, []
        try:
            itens = metodo(data=self.data_var.get().strip())
        except TypeError:
            try:
                itens = metodo()
            except Exception:
                return True, []
        except Exception:
            return True, []

        if not isinstance(itens, list):
            return True, []

        normalizados = []
        for a in itens:
            if not isinstance(a, dict):
                continue

            data_obj = self._parse_data_agendamento(a.get("data"))
            if not data_obj:
                continue

            inicio = str(a.get("inicio") or "08:00")
            fim = str(a.get("fim") or "12:00")

            inicio_min = self._parse_hora(inicio)
            fim_min = self._parse_hora(fim)
            if inicio_min is None or fim_min is None:
                continue

            try:
                aid = int(a.get("id"))
            except Exception:
                continue

            try:
                carrinho_id = int(a.get("carrinho_id")) if a.get("carrinho_id") is not None else None
            except Exception:
                carrinho_id = None

            try:
                motorista_id = int(a.get("motorista_id")) if a.get("motorista_id") is not None else None
            except Exception:
                motorista_id = None

            qtd_carrinhos = int(a.get("qtd_carrinhos") or 1)
            carrinhos_texto = str(a.get("carrinhos_texto") or "")

            carrinho = next((c for c in self.carrinhos if c["id"] == carrinho_id), None)
            motorista = next((m for m in self.motoristas if m["id"] == motorista_id), None)

            normalizados.append({
                "id": aid,
                "data": data_obj,
                "inicio": inicio,
                "fim": fim,
                "inicio_min": inicio_min,
                "fim_min": fim_min,
                "carrinho_id": carrinho_id,
                "carrinho_nome": (carrinho["nome"] if carrinho else str(a.get("carrinho_nome") or "")),
                "carrinho_id_externo": (carrinho["id_externo"] if carrinho else str(a.get("carrinho_id_externo") or "")),
                "qtd_carrinhos": qtd_carrinhos,
                "carrinhos_texto": carrinhos_texto,
                "motorista_id": motorista_id,
                "motorista_nome": (motorista["nome"] if motorista else str(a.get("motorista_nome") or "")),
                "local": str(a.get("local") or ""),
                "status": str(a.get("status") or "Agendado"),
                "obs": str(a.get("obs") or ""),
            })

        return True, normalizados

    def _carregar_dados_operacionais(self):
        ok_car, carrinhos = self._listar_carrinhos_sistema()
        if ok_car or not self.carrinhos:
            self.carrinhos = carrinhos

        ok_mot, motos = self._listar_motoristas_sistema()
        if ok_mot or not self.motoristas:
            self.motoristas = motos

        ok_ag, ags = self._listar_agendamentos_sistema()
        if ok_ag or not self.agendamentos:
            self.agendamentos = ags

    def _atualizar_combos_operacionais(self):
        if hasattr(self, "combo_carrinho"):
            atual = self.combo_carrinho.get().strip()
            opcoes = ["(auto selecionar)"] + [f'{c["nome"]} ({c["id_externo"]})' for c in self.carrinhos]
            self.combo_carrinho.configure(values=opcoes)
            self.combo_carrinho.set(atual if atual in opcoes else opcoes[0])

        if hasattr(self, "combo_motorista"):
            atual = self.combo_motorista.get().strip()
            opcoes = ["(sem motorista)"] + [f'{m["nome"]} • {m["telefone"]}' for m in self.motoristas]
            self.combo_motorista.configure(values=opcoes)
            self.combo_motorista.set(atual if atual in opcoes else opcoes[0])

    def _salvar_agendamento_no_sistema(self, payload):
        """
        Salva agendamento usando SistemaService.salvar_agendamento()
        com os parâmetros corretos.
        """
        metodo = self._obter_metodo_sistema("salvar_agendamento")
        if not metodo:
            return False, "SistemaService não expõe salvar_agendamento."

        data_txt = payload["data"].strftime("%Y-%m-%d")
        try:
            metodo(
                data=data_txt,
                hora_inicio=payload["inicio"],
                hora_fim=payload["fim"],
                carrinho_id=payload.get("carrinho_preferido_id") or 1,  # ID padrão se não houver
                funcionario_id=payload.get("motorista_id") or 1,  # ID padrão se não houver
                local=payload["local"],
                status=payload["status"],
                observacao=payload["obs"],
                agendamento_id=self._agendamento_em_edicao_id,
                quantidade_carrinhos=payload.get("quantidade_carrinhos", 1),
                carrinhos_texto=payload.get("carrinhos_texto", ""),
            )
            return True, ""
        except TypeError as e:
            # Se houver erro de tipo, tenta com menos parâmetros (compatibilidade)
            try:
                metodo(
                    data=data_txt,
                    hora_inicio=payload["inicio"],
                    hora_fim=payload["fim"],
                    carrinho_id=payload.get("carrinho_preferido_id") or 1,
                    funcionario_id=payload.get("motorista_id") or 1,
                    local=payload["local"],
                    status=payload["status"],
                    observacao=payload["obs"],
                    agendamento_id=self._agendamento_em_edicao_id,
                )
                return True, ""
            except Exception as e2:
                return False, f"Erro ao salvar: {str(e2)}"
        except Exception as e:
            return False, str(e)

    def _remover_agendamento_do_sistema(self, aid):
        metodo = self._obter_metodo_sistema("excluir_agendamento", "remover_agendamento")
        if not metodo:
            return False
        try:
            metodo(aid)
            return True
        except Exception:
            return False

    # -------------------- UI ESQ --------------------
    def _painel_carrinhos_ui(self):
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=0, column=0, padx=(30, 12), pady=(10, 20), sticky="nsew")
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(2, weight=1)

        filtros = ctk.CTkFrame(box, fg_color="transparent")
        filtros.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="ew")
        filtros.grid_columnconfigure(0, weight=1)

        self.entry_busca_car = ctk.CTkEntry(
            filtros,
            textvariable=self.busca_carrinho_var,
            placeholder_text="🔎 Buscar carrinho por nome/ID…",
            height=36,
            fg_color=theme.COR_BOTAO,
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        )
        self.entry_busca_car.grid(row=0, column=0, sticky="ew")
        self.entry_busca_car.bind("<KeyRelease>", lambda e: self._render_lista_carrinhos())

        self.combo_status_car = ctk.CTkComboBox(
            filtros,
            values=["Todos", "Disponível", "Em rota", "Manutenção"],
            width=170,
            command=lambda _: self._render_lista_carrinhos(),
            fg_color=theme.COR_BOTAO,
            button_color=theme.COR_SELECIONADO,
            button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            dropdown_fg_color=theme.COR_BOTAO,
            dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO,
            border_width=1,
            border_color=theme.COR_HOVER
        )
        self.combo_status_car.set("Todos")
        self.combo_status_car.grid(row=0, column=1, padx=(10, 0))

        ctk.CTkLabel(
            box,
            text="Carrinhos (duplo clique = preferir)",
            font=ctk.CTkFont(family=theme.FONTE, size=14, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=1, column=0, padx=12, pady=(0, 4), sticky="w")

        self._frame_tree_carrinhos = ctk.CTkFrame(box, fg_color=theme.COR_BOTAO, corner_radius=12)
        self._frame_tree_carrinhos.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self._frame_tree_carrinhos.grid_rowconfigure(0, weight=1)
        self._frame_tree_carrinhos.grid_columnconfigure(0, weight=1)
        self._frame_tree_carrinhos.bind("<Configure>", self._ajustar_colunas_tree_carrinhos)

        self.tree_carrinhos = ttk.Treeview(
            self._frame_tree_carrinhos,
            columns=("status", "capacidade"),
            show="tree headings",
            style="Geladoce.Agenda.Treeview",
        )
        self.tree_carrinhos.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)

        self.tree_carrinhos.heading("#0", text="Identificação", anchor="w")
        self.tree_carrinhos.heading("status", text="Status", anchor="w")
        self.tree_carrinhos.heading("capacidade", text="Capacidade", anchor="w")

        scroll_y = ttk.Scrollbar(self._frame_tree_carrinhos, orient="vertical", command=self.tree_carrinhos.yview)
        scroll_y.grid(row=0, column=1, sticky="ns", padx=(8, 8), pady=8)
        self.tree_carrinhos.configure(yscrollcommand=scroll_y.set)

        self.tree_carrinhos.bind("<Double-1>", lambda e: self._usar_carrinho_selecionado())

    # -------------------- UI DIR --------------------
    def _form_agendamento_ui(self):
        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=0, column=1, padx=(12, 30), pady=(10, 24), sticky="nsew")
        box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            box,
            text="Novo agendamento",
            font=ctk.CTkFont(family=theme.FONTE, size=16, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=16, pady=(16, 10), sticky="w")

        linha_data = ctk.CTkFrame(box, fg_color="transparent")
        linha_data.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")
        linha_data.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            linha_data, text="←", width=38, height=34,
            fg_color=theme.COR_BOTAO, hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
            border_width=1, border_color=theme.COR_HOVER,
            command=lambda: self._navegar_data(-1)
        ).grid(row=0, column=0, padx=(0, 6))

        ctk.CTkEntry(
            linha_data, textvariable=self.data_var, height=34, placeholder_text="AAAA-MM-DD",
            fg_color=theme.COR_BOTAO, text_color=theme.COR_TEXTO, border_width=1, border_color=theme.COR_HOVER
        ).grid(row=0, column=1, sticky="ew")

        ctk.CTkButton(
            linha_data, text="→", width=38, height=34,
            fg_color=theme.COR_BOTAO, hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
            border_width=1, border_color=theme.COR_HOVER,
            command=lambda: self._navegar_data(1)
        ).grid(row=0, column=2, padx=(6, 0))

        ctk.CTkButton(
            linha_data, text="Hoje", width=70, height=34,
            fg_color=theme.COR_BOTAO, hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
            border_width=1, border_color=theme.COR_HOVER,
            command=lambda: self._set_data(dt.date.today())
        ).grid(row=0, column=3, padx=(8, 0))

        form = ctk.CTkFrame(box, fg_color=theme.COR_BOTAO, corner_radius=12)
        form.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="ew")
        form.grid_columnconfigure(0, weight=1, uniform="form_ag_2x2")
        form.grid_columnconfigure(1, weight=1, uniform="form_ag_2x2")

        ctk.CTkLabel(form, text="Início (HH:MM)", text_color=theme.COR_TEXTO).grid(row=0, column=0, padx=10, pady=(12, 4), sticky="w")
        ctk.CTkLabel(form, text="Fim (HH:MM)", text_color=theme.COR_TEXTO).grid(row=0, column=1, padx=10, pady=(12, 4), sticky="w")

        ctk.CTkComboBox(
            form, values=self._horarios_padrao(), variable=self.hora_ini_var, height=34,
            fg_color=theme.COR_BOTAO, button_color=theme.COR_SELECIONADO, button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO, dropdown_fg_color=theme.COR_BOTAO, dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO, border_width=1, border_color=theme.COR_HOVER
        ).grid(row=1, column=0, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkComboBox(
            form, values=self._horarios_padrao(), variable=self.hora_fim_var, height=34,
            fg_color=theme.COR_BOTAO, button_color=theme.COR_SELECIONADO, button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO, dropdown_fg_color=theme.COR_BOTAO, dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO, border_width=1, border_color=theme.COR_HOVER
        ).grid(row=1, column=1, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(form, text="Carrinho (opcional)", text_color=theme.COR_TEXTO).grid(row=2, column=0, padx=10, pady=(6, 4), sticky="w")
        ctk.CTkLabel(form, text="Quantidade de carrinhos", text_color=theme.COR_TEXTO).grid(row=2, column=1, padx=10, pady=(6, 4), sticky="w")

        self.combo_carrinho = ctk.CTkComboBox(
            form, values=["(auto selecionar)"], height=34,
            fg_color=theme.COR_BOTAO, button_color=theme.COR_SELECIONADO, button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO, dropdown_fg_color=theme.COR_BOTAO, dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO, border_width=1, border_color=theme.COR_HOVER
        )
        self.combo_carrinho.grid(row=3, column=0, padx=10, pady=(0, 8), sticky="ew")
        self.combo_carrinho.set("(auto selecionar)")

        ctk.CTkEntry(
            form, textvariable=self.qtd_carrinhos_var, height=34, placeholder_text="1",
            fg_color=theme.COR_BOTAO, text_color=theme.COR_TEXTO, border_width=1, border_color=theme.COR_HOVER
        ).grid(row=3, column=1, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(form, text="Motorista (opcional)", text_color=theme.COR_TEXTO).grid(row=4, column=0, padx=10, pady=(6, 4), sticky="w")
        ctk.CTkLabel(form, text="Status", text_color=theme.COR_TEXTO).grid(row=4, column=1, padx=10, pady=(6, 4), sticky="w")

        self.combo_motorista = ctk.CTkComboBox(
            form, values=["(sem motorista)"], variable=self.motorista_var, height=34,
            fg_color=theme.COR_BOTAO, button_color=theme.COR_SELECIONADO, button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO, dropdown_fg_color=theme.COR_BOTAO, dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO, border_width=1, border_color=theme.COR_HOVER
        )
        self.combo_motorista.grid(row=5, column=0, padx=10, pady=(0, 8), sticky="ew")
        self.combo_motorista.set("(sem motorista)")

        self.combo_status_ag = ctk.CTkComboBox(
            form, values=["Agendado", "Confirmado", "Cancelado"], height=34,
            fg_color=theme.COR_BOTAO, button_color=theme.COR_SELECIONADO, button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO, dropdown_fg_color=theme.COR_BOTAO, dropdown_hover_color=theme.COR_HOVER,
            dropdown_text_color=theme.COR_TEXTO, border_width=1, border_color=theme.COR_HOVER
        )
        self.combo_status_ag.set("Agendado")
        self.combo_status_ag.grid(row=5, column=1, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(form, text="Local / Evento", text_color=theme.COR_TEXTO).grid(row=6, column=0, padx=10, pady=(6, 4), sticky="w")
        ctk.CTkEntry(
            form, textvariable=self.local_var, height=34,
            placeholder_text="Ex.: Escola Alfa, Praça X…",
            fg_color=theme.COR_BOTAO, text_color=theme.COR_TEXTO, border_width=1, border_color=theme.COR_HOVER
        ).grid(row=7, column=0, padx=10, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(form, text="Observações", text_color=theme.COR_TEXTO).grid(row=8, column=0, columnspan=2, padx=10, pady=(6, 4), sticky="w")
        self.observacoes_widget = ctk.CTkTextbox(
            form, height=60, fg_color=theme.COR_BOTAO, text_color=theme.COR_TEXTO, border_width=1, border_color=theme.COR_HOVER
        )
        self.observacoes_widget.grid(row=9, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")

        linha_btns = ctk.CTkFrame(box, fg_color="transparent")
        linha_btns.grid(row=3, column=0, padx=16, pady=(12, 14), sticky="ew")
        linha_btns.grid_columnconfigure(0, weight=1)
        linha_btns.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            linha_btns, text="Salvar agendamento", height=38,
            fg_color=theme.COR_BOTAO, hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
            border_width=1, border_color=theme.COR_HOVER,
            command=self._salvar_agendamento
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            linha_btns, text="Limpar", height=38,
            fg_color=theme.COR_BOTAO, hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
            border_width=1, border_color=theme.COR_HOVER,
            command=self._limpar_form
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        ctk.CTkButton(
            box, text="Ir para aba Agenda do dia", height=38,
            fg_color=theme.COR_BOTAO, hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
            border_width=1, border_color=theme.COR_HOVER,
            command=self._abrir_aba_agenda
        ).grid(row=4, column=0, padx=16, pady=(0, 16), sticky="ew")

    def _ajustar_colunas_tree_carrinhos(self, event=None):
        if not self.tree_carrinhos or not self._frame_tree_carrinhos:
            return
        largura = max(self._frame_tree_carrinhos.winfo_width() - 28, 220)
        col0 = int(largura * 0.52)
        col1 = int(largura * 0.26)
        col2 = max(largura - col0 - col1, 80)
        self.tree_carrinhos.column("#0", width=col0, anchor="w")
        self.tree_carrinhos.column("status", width=col1, anchor="w")
        self.tree_carrinhos.column("capacidade", width=col2, anchor="w")

    def _render_lista_carrinhos(self):
        if not self.tree_carrinhos:
            return

        self._carregar_dados_operacionais()
        self._atualizar_combos_operacionais()

        for item in self.tree_carrinhos.get_children():
            self.tree_carrinhos.delete(item)

        termo = self.busca_carrinho_var.get().strip().lower()
        status_filtro = self.combo_status_car.get().strip() if self.combo_status_car else "Todos"

        for carrinho in self.carrinhos:
            if status_filtro != "Todos" and carrinho["status"] != status_filtro:
                continue
            texto_busca = f'{carrinho["nome"]} {carrinho["id_externo"]}'.lower()
            if termo and termo not in texto_busca:
                continue

            self.tree_carrinhos.insert(
                "",
                "end",
                text=f'{carrinho["nome"]} ({carrinho["id_externo"]})',
                values=(carrinho["status"], carrinho["capacidade"]),
                tags=(f'id-{carrinho["id"]}',)
            )

    def _usar_carrinho_selecionado(self):
        sel = self.tree_carrinhos.selection()
        if not sel:
            return

        tags = self.tree_carrinhos.item(sel[0], "tags")
        cid = None
        for t in tags:
            if str(t).startswith("id-"):
                cid = int(str(t).split("-")[1])
                break
        if cid is None:
            return

        car = next((x for x in self.carrinhos if x["id"] == cid), None)
        if not car:
            return
        self.combo_carrinho.set(f'{car["nome"]} ({car["id_externo"]})')

    def _abrir_aba_agenda(self):
        if callable(self.on_open_agenda):
            self.on_open_agenda()

    def _notificar_agenda(self):
        if callable(self.on_agenda_changed):
            self.on_agenda_changed()

    def _set_data(self, date_obj: dt.date):
        self.data_var.set(date_obj.strftime("%Y-%m-%d"))
        self._notificar_agenda()

    def _navegar_data(self, delta_days: int):
        try:
            d = dt.date.fromisoformat(self.data_var.get())
        except ValueError:
            d = dt.date.today()
        self._set_data(d + dt.timedelta(days=delta_days))

    def _horarios_padrao(self):
        horarios = []
        h, m = 6, 0
        while h < 23 or (h == 23 and m == 0):
            horarios.append(f"{h:02d}:{m:02d}")
            m += 30
            if m >= 60:
                m = 0
                h += 1
        return horarios

    def _pegar_obs(self):
        return self.observacoes_widget.get("1.0", "end").strip()

    def _set_obs(self, text: str):
        self.observacoes_widget.delete("1.0", "end")
        if text:
            self.observacoes_widget.insert("1.0", text)

    def _parse_hora(self, s: str):
        try:
            h, m = s.split(":")
            h = int(h); m = int(m)
            if 0 <= h <= 23 and 0 <= m <= 59:
                return h * 60 + m
        except Exception:
            return None
        return None

    def _resolver_carrinho_preferido_id(self):
        txt = self.combo_carrinho.get().strip()
        if not txt or txt == "(auto selecionar)":
            return None
        for c in self.carrinhos:
            if txt.startswith(c["nome"]) and c["id_externo"] in txt:
                return int(c["id"])
        return None

    def _resolver_motorista_id(self):
        txt = self.combo_motorista.get().strip()
        if not txt or txt == "(sem motorista)":
            return None
        nome = txt.split("•")[0].strip()
        for m in self.motoristas:
            if m["nome"] == nome:
                return int(m["id"])
        return None

    def _validar_inputs(self):
        try:
            dt.date.fromisoformat(self.data_var.get().strip())
        except ValueError:
            return False, "Data inválida. Use AAAA-MM-DD."

        ini = self._parse_hora(self.hora_ini_var.get().strip())
        fim = self._parse_hora(self.hora_fim_var.get().strip())
        if ini is None or fim is None:
            return False, "Horários inválidos. Use HH:MM."
        if fim <= ini:
            return False, "Hora de fim deve ser maior que a de início."

        try:
            qtd = int(self.qtd_carrinhos_var.get().strip() or "1")
            if qtd <= 0:
                raise ValueError
        except ValueError:
            return False, "Quantidade de carrinhos inválida."

        if not self.local_var.get().strip():
            return False, "Informe o local/evento."

        return True, ""

    def _salvar_agendamento(self):
        self._carregar_dados_operacionais()
        self._atualizar_combos_operacionais()

        ok, msg = self._validar_inputs()
        if not ok:
            messagebox.showwarning("Validação", msg)
            return

        data = dt.date.fromisoformat(self.data_var.get().strip())
        ini_txt = self.hora_ini_var.get().strip()
        fim_txt = self.hora_fim_var.get().strip()

        payload = {
            "data": data,
            "inicio": ini_txt,
            "fim": fim_txt,
            "local": self.local_var.get().strip(),
            "status": self.combo_status_ag.get().strip(),
            "obs": self._pegar_obs(),
            "quantidade_carrinhos": int(self.qtd_carrinhos_var.get().strip() or "1"),
            "carrinhos_texto": "",
            "carrinho_preferido_id": self._resolver_carrinho_preferido_id(),
            "motorista_id": self._resolver_motorista_id(),
        }

        ok, err = self._salvar_agendamento_no_sistema(payload)
        if not ok:
            messagebox.showerror("Erro", f"Não foi possível salvar o agendamento.\n\n{err}")
            return

        self._carregar_dados_operacionais()
        self._limpar_form()
        self._notificar_agenda()
        self._render_lista_carrinhos()
        messagebox.showinfo("Agendamento", "Agendamento salvo com sucesso!")

    def _limpar_form(self):
        self._agendamento_em_edicao_id = None
        self.hora_ini_var.set("08:00")
        self.hora_fim_var.set("12:00")
        self.local_var.set("")
        self.combo_status_ag.set("Agendado")
        self.qtd_carrinhos_var.set("1")
        self.combo_motorista.set("(sem motorista)")
        self.combo_carrinho.set("(auto selecionar)")
        self._set_obs("")

    def remover_agendamento_por_id(self, aid: int):
        removido_no_sistema = self._remover_agendamento_do_sistema(aid)
        if not removido_no_sistema:
            self.agendamentos = [x for x in self.agendamentos if x["id"] != aid]
        self._carregar_dados_operacionais()
        if self._agendamento_em_edicao_id == aid:
            self._limpar_form()
        self._notificar_agenda()

    def obter_agendamentos_do_dia(self):
        self._carregar_dados_operacionais()
        try:
            data = dt.date.fromisoformat(self.data_var.get().strip())
        except ValueError:
            return []
        do_dia = [a for a in self.agendamentos if a["data"] == data]
        do_dia.sort(key=lambda x: x["inicio_min"])
        return do_dia


# ===========================================================
# ABA 2: AGENDA DO DIA
# ===========================================================
class PaginaAgendaDoDia(ctk.CTkFrame):
    def __init__(self, master, pagina_agendamento: PaginaAgendamentoCarrinhos, on_back_to_agendamento=None):
        super().__init__(master, fg_color=theme.COR_FUNDO)
        _ensure_tree_styles()

        self.pagina_agendamento = pagina_agendamento
        self.on_back_to_agendamento = on_back_to_agendamento

        self.tree_agenda = None
        self._frame_tree_agenda = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._montar_ui()
        self.renderizar()

    def _montar_ui(self):
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.grid(row=0, column=0, padx=24, pady=(14, 8), sticky="ew")
        topo.grid_columnconfigure(0, weight=1)

        self.lbl_titulo = ctk.CTkLabel(
            topo, text="Agenda do dia",
            font=ctk.CTkFont(family=theme.FONTE, size=20, weight="bold"),
            text_color=theme.COR_TEXTO
        )
        self.lbl_titulo.grid(row=0, column=0, sticky="w")

        self.lbl_sub = ctk.CTkLabel(
            topo, text="Agendamentos da data selecionada na aba Agendamentos.",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC
        )
        self.lbl_sub.grid(row=1, column=0, pady=(2, 0), sticky="w")

        linha_btns = ctk.CTkFrame(self, fg_color="transparent")
        linha_btns.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="ew")
        linha_btns.grid_columnconfigure(0, weight=1)
        linha_btns.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            linha_btns, text="Atualizar agenda", height=36,
            fg_color=theme.COR_BOTAO, hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
            border_width=1, border_color=theme.COR_HOVER,
            command=self.renderizar
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            linha_btns, text="Voltar para Agendamentos", height=36,
            fg_color=theme.COR_BOTAO, hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
            border_width=1, border_color=theme.COR_HOVER,
            command=self._voltar_para_agendamentos
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        box = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        box.grid(row=2, column=0, padx=24, pady=(0, 20), sticky="nsew")
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(0, weight=1)

        self._frame_tree_agenda = ctk.CTkFrame(box, fg_color=theme.COR_BOTAO, corner_radius=12)
        self._frame_tree_agenda.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="nsew")
        self._frame_tree_agenda.grid_rowconfigure(0, weight=1)
        self._frame_tree_agenda.grid_columnconfigure(0, weight=1)
        self._frame_tree_agenda.bind("<Configure>", self._ajustar_colunas_tree_agenda)

        self.tree_agenda = ttk.Treeview(
            self._frame_tree_agenda,
            columns=("hora", "carrinhos", "motorista", "local", "status"),
            show="headings",
            style="Geladoce.Agenda.Treeview",
        )
        self.tree_agenda.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)

        self.tree_agenda.heading("hora", text="Horário", anchor="w")
        self.tree_agenda.heading("carrinhos", text="Carrinhos", anchor="w")
        self.tree_agenda.heading("motorista", text="Motorista", anchor="w")
        self.tree_agenda.heading("local", text="Local/Evento", anchor="w")
        self.tree_agenda.heading("status", text="Status", anchor="w")

        scroll = ttk.Scrollbar(self._frame_tree_agenda, orient="vertical", command=self.tree_agenda.yview)
        scroll.grid(row=0, column=1, sticky="ns", padx=(8, 8), pady=8)
        self.tree_agenda.configure(yscrollcommand=scroll.set)

        ctk.CTkButton(
            box, text="Remover agendamento selecionado", height=36,
            fg_color=theme.COR_BOTAO, hover_color=theme.COR_HOVER, text_color=theme.COR_TEXTO,
            border_width=1, border_color=theme.COR_HOVER,
            command=self._remover_selecionado
        ).grid(row=1, column=0, padx=12, pady=(0, 12), sticky="ew")

    def _ajustar_colunas_tree_agenda(self, event=None):
        if not self.tree_agenda or not self._frame_tree_agenda:
            return
        largura = max(self._frame_tree_agenda.winfo_width() - 28, 520)
        c1 = int(largura * 0.14)
        c2 = int(largura * 0.28)
        c3 = int(largura * 0.18)
        c4 = int(largura * 0.30)
        c5 = max(largura - c1 - c2 - c3 - c4, 70)

        self.tree_agenda.column("hora", width=c1, anchor="w")
        self.tree_agenda.column("carrinhos", width=c2, anchor="w")
        self.tree_agenda.column("motorista", width=c3, anchor="w")
        self.tree_agenda.column("local", width=c4, anchor="w")
        self.tree_agenda.column("status", width=c5, anchor="w")

    def renderizar(self):
        if not self.tree_agenda:
            return

        for item in self.tree_agenda.get_children():
            self.tree_agenda.delete(item)

        data_txt = self.pagina_agendamento.data_var.get().strip()
        self.lbl_titulo.configure(text=f"Agenda do dia • {data_txt}")

        do_dia = self.pagina_agendamento.obter_agendamentos_do_dia()

        for a in do_dia:
            carrinhos_txt = a.get("carrinhos_texto") or ""
            if not carrinhos_txt:
                q = int(a.get("qtd_carrinhos") or 1)
                if q > 1:
                    carrinhos_txt = f"{q} carrinhos"
                else:
                    base = f'{a.get("carrinho_nome","")} ({a.get("carrinho_id_externo","")})'.strip()
                    carrinhos_txt = base if base.strip("() ") else "1 carrinho"

            mot_txt = a.get("motorista_nome") or "—"

            self.tree_agenda.insert(
                "",
                "end",
                values=(
                    f'{a["inicio"]}–{a["fim"]}',
                    carrinhos_txt,
                    mot_txt,
                    a.get("local", ""),
                    a.get("status", "")
                ),
                tags=(f'ag-{a["id"]}',)
            )

    def _voltar_para_agendamentos(self):
        if callable(self.on_back_to_agendamento):
            self.on_back_to_agendamento()

    def _obter_id_selecionado(self):
        sel = self.tree_agenda.selection()
        if not sel:
            return None
        tags = self.tree_agenda.item(sel[0], "tags")
        if not tags:
            return None
        tag = tags[0]
        if not str(tag).startswith("ag-"):
            return None
        return int(str(tag).split("-")[1])

    def _remover_selecionado(self):
        aid = self._obter_id_selecionado()
        if aid is None:
            messagebox.showwarning("Remover", "Selecione um agendamento na lista.")
            return
        if not messagebox.askyesno("Confirmar", "Deseja remover este agendamento?"):
            return
        self.pagina_agendamento.remover_agendamento_por_id(aid)
        self.renderizar()
        messagebox.showinfo("Removido", "Agendamento removido.")


# ===========================================================
# WRAPPER: ABAS
# ===========================================================
class PaginaOperacaoCarrinhos(ctk.CTkFrame):
    def __init__(self, master, sistema):
        super().__init__(master, fg_color=theme.COR_FUNDO)
        self.sistema = sistema

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            self,
            text="Operação • Serviços",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO
        ).grid(row=0, column=0, padx=30, pady=(14, 6), sticky="w")

        ctk.CTkLabel(
            self,
            text="Agende eventos, gerencie carrinhos e cadastre motoristas.",
            font=ctk.CTkFont(family=theme.FONTE, size=13),
            text_color=theme.COR_TEXTO_SEC
        ).grid(row=1, column=0, padx=30, pady=(0, 10), sticky="w")

        self.tabs = ctk.CTkTabview(
            self,
            fg_color=theme.COR_PAINEL,
            segmented_button_fg_color=theme.COR_BOTAO,
            segmented_button_selected_color=theme.COR_SELECIONADO,
            segmented_button_selected_hover_color=theme.COR_HOVER,
            segmented_button_unselected_color=theme.COR_BOTAO,
            segmented_button_unselected_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            corner_radius=14,
            anchor="w"
        )
        self.tabs.grid(row=2, column=0, padx=24, pady=(0, 20), sticky="nsew")

        tab_ag = self.tabs.add("Agendamentos")
        tab_agenda = self.tabs.add("Agenda do dia")
        tab_dl = self.tabs.add("Delivery")
        tab_carrinhos = self.tabs.add("Carrinhos")
        tab_motoristas = self.tabs.add("Motoristas")

        self.pg_ag = PaginaAgendamentoCarrinhos(
            tab_ag,
            sistema=self.sistema,
            on_open_agenda=self._ir_para_aba_agenda,
            on_agenda_changed=self._atualizar_aba_agenda
        )
        self.pg_ag.pack(fill="both", expand=True, padx=6, pady=6)

        self.pg_agenda = PaginaAgendaDoDia(
            tab_agenda,
            pagina_agendamento=self.pg_ag,
            on_back_to_agendamento=self._ir_para_aba_agendamentos
        )
        self.pg_agenda.pack(fill="both", expand=True, padx=6, pady=6)

        self.pg_dl = PaginaDelivery(tab_dl, self.sistema)
        self.pg_dl.pack(fill="both", expand=True, padx=6, pady=6)

        self.pg_carrinhos = PaginaCadastroCarrinhos(
            tab_carrinhos,
            sistema=self.sistema,
            on_changed=self._refresh_agendamento_dependencias
        )
        self.pg_carrinhos.pack(fill="both", expand=True, padx=6, pady=6)

        self.pg_motoristas = PaginaCadastroMotoristas(
            tab_motoristas,
            sistema=self.sistema,
            on_changed=self._refresh_agendamento_dependencias
        )
        self.pg_motoristas.pack(fill="both", expand=True, padx=6, pady=6)

    def _refresh_agendamento_dependencias(self):
        # quando cadastra carrinho/motorista, atualiza combos da aba agendamentos
        if hasattr(self, "pg_ag") and self.pg_ag:
            try:
                self.pg_ag._carregar_dados_operacionais()
                self.pg_ag._atualizar_combos_operacionais()
                self.pg_ag._render_lista_carrinhos()
            except Exception:
                pass

    def _ir_para_aba_agenda(self):
        self.pg_agenda.renderizar()
        self.tabs.set("Agenda do dia")

    def _ir_para_aba_agendamentos(self):
        self.tabs.set("Agendamentos")

    def _atualizar_aba_agenda(self):
        self.pg_agenda.renderizar()