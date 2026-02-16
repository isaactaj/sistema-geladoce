import customtkinter as ctk
import datetime as dt
import random
import calendar

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app.config.theme import (
    COR_FUNDO, COR_PAINEL, COR_TEXTO, COR_TEXTO_SEC, FONTE
)

from app.pages.relatorios.export import exportar_excel, exportar_pdf


# ============================================================
# Widget: Card de gráfico responsivo (mesmo que você já usa)
# ============================================================
class CardGraficoResponsivo(ctk.CTkFrame):
    def __init__(self, master, titulo: str, ratio: float = 0.60):
        super().__init__(master, fg_color="#FFFFFF", corner_radius=14)

        self.ratio = ratio
        self.dpi = 100
        self._ultimo_w = 0

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.lbl_titulo = ctk.CTkLabel(
            self,
            text=titulo,
            font=ctk.CTkFont(family=FONTE, size=13, weight="bold"),
            text_color=COR_TEXTO
        )
        self.lbl_titulo.grid(row=0, column=0, padx=12, pady=(10, 6), sticky="w")

        self.fig = Figure(figsize=(5, 3), dpi=self.dpi)
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")

        self.bind("<Configure>", self._ao_redimensionar)

    def _ao_redimensionar(self, event):
        if event.width == self._ultimo_w:
            return
        self._ultimo_w = event.width

        largura_px = max(240, event.width - 24)
        altura_px = int(largura_px * self.ratio)

        self.fig.set_size_inches(largura_px / self.dpi, altura_px / self.dpi, forward=True)
        self.fig.tight_layout()
        self.canvas.draw_idle()

    def atualizar_plot(self, plot_fn):
        self.ax.clear()
        plot_fn(self.ax)
        self.ax.grid(True, alpha=0.2)
        self.fig.tight_layout()
        self.canvas.draw_idle()


# ============================================================
# Página: Relatórios
# ============================================================
class PaginaAdminRelatorios(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=COR_FUNDO)

        # Grid base da página
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(4, weight=1)                 # área dos gráficos
        self.grid_rowconfigure(5, weight=0, minsize=100)    # respiro + botões export

        # Estado (mês/ano)
        hoje = dt.date.today()
        self.mes = hoje.month
        self.ano = hoje.year

        # Título
        ctk.CTkLabel(
            self, text="Administrativo • Relatórios",
            font=ctk.CTkFont(family=FONTE, size=24, weight="bold"),
            text_color=COR_TEXTO
        ).grid(row=0, column=0, columnspan=2, padx=30, pady=(14, 4), sticky="w")

        ctk.CTkLabel(
            self, text="Visão geral.",
            font=ctk.CTkFont(family=FONTE, size=13),
            text_color=COR_TEXTO_SEC
        ).grid(row=1, column=0, columnspan=2, padx=30, pady=(0, 8), sticky="w")

        # UI
        self._criar_filtros()
        self._criar_cards_kpi()
        self._criar_area_graficos()
        self._criar_frame_exportacao()

        # Primeira renderização
        self.atualizar_dashboard()

    # -------------------------
    # UI: filtros
    # -------------------------
    def _criar_filtros(self):
        self.frame_filtros = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_filtros.grid(row=2, column=0, columnspan=2, padx=30, pady=(0, 10), sticky="ew")
        self.frame_filtros.grid_columnconfigure(0, weight=1)
        self.frame_filtros.grid_columnconfigure(1, weight=0)

        filtros_esq = ctk.CTkFrame(self.frame_filtros, fg_color="transparent")
        filtros_esq.grid(row=0, column=0, sticky="w", padx=(0, 20))

        ctk.CTkLabel(
            filtros_esq, text="Tipo:",
            font=ctk.CTkFont(family=FONTE, size=12, weight="bold"),
            text_color=COR_TEXTO_SEC
        ).grid(row=0, column=0, padx=(0, 6))

        self.combo_tipo = ctk.CTkComboBox(
            filtros_esq,
            values=["Todos", "Balcão", "Revenda", "Serviços"],
            width=140,
            command=lambda _: self.atualizar_dashboard()
        )
        self.combo_tipo.set("Todos")
        self.combo_tipo.grid(row=0, column=1, padx=(0, 12))

        ctk.CTkLabel(
            filtros_esq, text="Categoria:",
            font=ctk.CTkFont(family=FONTE, size=12, weight="bold"),
            text_color=COR_TEXTO_SEC
        ).grid(row=0, column=2, padx=(0, 6))

        self.combo_categoria = ctk.CTkComboBox(
            filtros_esq,
            values=["Todos", "Sorvete", "Picolé", "Açaí", "Outros"],
            width=140,
            command=lambda _: self.atualizar_dashboard()
        )
        self.combo_categoria.set("Todos")
        self.combo_categoria.grid(row=0, column=3)

        bloco_dir = ctk.CTkFrame(self.frame_filtros, fg_color="transparent")
        bloco_dir.grid(row=0, column=1, sticky="e")

        self.btn_mes_prev = ctk.CTkButton(
            bloco_dir, text="◀", width=40, height=34,
            fg_color=COR_PAINEL, hover_color="#C1ECFD",
            text_color=COR_TEXTO, command=self.mes_anterior
        )
        self.btn_mes_prev.grid(row=0, column=0, padx=(0, 6))

        self.lbl_periodo = ctk.CTkLabel(
            bloco_dir, text="",
            font=ctk.CTkFont(family=FONTE, size=12, weight="bold"),
            text_color=COR_TEXTO
        )
        self.lbl_periodo.grid(row=0, column=1, padx=6)

        self.btn_mes_next = ctk.CTkButton(
            bloco_dir, text="▶", width=40, height=34,
            fg_color=COR_PAINEL, hover_color="#C1ECFD",
            text_color=COR_TEXTO, command=self.mes_proximo
        )
        self.btn_mes_next.grid(row=0, column=2, padx=(6, 0))

        self.btn_ano_prev = ctk.CTkButton(
            bloco_dir, text="- Ano", width=70, height=34,
            fg_color=COR_PAINEL, hover_color="#C1ECFD",
            text_color=COR_TEXTO, command=self.ano_anterior
        )
        self.btn_ano_prev.grid(row=0, column=3, padx=(16, 6))

        self.btn_ano_next = ctk.CTkButton(
            bloco_dir, text="+ Ano", width=70, height=34,
            fg_color=COR_PAINEL, hover_color="#C1ECFD",
            text_color=COR_TEXTO, command=self.ano_proximo
        )
        self.btn_ano_next.grid(row=0, column=4, padx=(6, 0))

    # -------------------------
    # UI: KPIs “inteligentes”
    # -------------------------
    def _criar_cards_kpi(self):
        self.container_cards = ctk.CTkFrame(self, fg_color="transparent")
        self.container_cards.grid(row=3, column=0, columnspan=2, padx=30, pady=(0, 12), sticky="ew")
        self.container_cards.grid_columnconfigure((0, 1, 2), weight=1)

        self.kpis = {}

        def criar_kpi(col, titulo):
            box = ctk.CTkFrame(self.container_cards, fg_color=COR_PAINEL, corner_radius=14)
            box.grid(row=0, column=col, padx=8, pady=6, sticky="ew")

            lbl_t = ctk.CTkLabel(
                box, text=titulo,
                font=ctk.CTkFont(family=FONTE, size=12, weight="bold"),
                text_color=COR_TEXTO_SEC
            )
            lbl_t.pack(anchor="w", padx=16, pady=(12, 2))

            linha = ctk.CTkFrame(box, fg_color="transparent")
            linha.pack(fill="x", padx=16, pady=(4, 0))

            lbl_v = ctk.CTkLabel(
                linha, text="—",
                font=ctk.CTkFont(family=FONTE, size=18, weight="bold"),
                text_color=COR_TEXTO
            )
            lbl_v.pack(side="left", anchor="w")

            lbl_delta = ctk.CTkLabel(
                linha, text="",
                font=ctk.CTkFont(family=FONTE, size=12, weight="bold"),
                text_color=COR_TEXTO_SEC
            )
            lbl_delta.pack(side="left", anchor="w", padx=(10, 0))

            lbl_sub = ctk.CTkLabel(
                box, text="",
                font=ctk.CTkFont(family=FONTE, size=12),
                text_color=COR_TEXTO_SEC
            )
            lbl_sub.pack(anchor="w", padx=16, pady=(6, 12))

            return (lbl_v, lbl_delta, lbl_sub)

        self.kpis["faturamento"] = criar_kpi(0, "Faturamento")
        self.kpis["vendas"] = criar_kpi(1, "Vendas")
        self.kpis["ticket"] = criar_kpi(2, "Ticket Médio")

    # -------------------------
    # UI: gráficos
    # -------------------------
    def _criar_area_graficos(self):
        self.frame_graficos = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_graficos.grid(row=4, column=0, columnspan=2, padx=30, pady=(0, 20), sticky="nsew")
        self.frame_graficos.grid_columnconfigure((0, 1), weight=1)
        self.frame_graficos.grid_rowconfigure(0, weight=1)

        self.graf1 = CardGraficoResponsivo(self.frame_graficos, "Faturamento por dia", ratio=0.60)
        self.graf1.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        self.graf2 = CardGraficoResponsivo(self.frame_graficos, "Produtos mais vendidos", ratio=0.60)
        self.graf2.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

    # -------------------------
    # UI: exportações
    # -------------------------
    def _criar_frame_exportacao(self):
        frame_export = ctk.CTkFrame(self, fg_color="transparent")
        frame_export.grid(row=5, column=0, columnspan=2, padx=30, pady=(12, 20), sticky="ew")
        frame_export.grid_columnconfigure(0, weight=1)

        botoes = ctk.CTkFrame(frame_export, fg_color="transparent")
        botoes.grid(row=0, column=1, sticky="e")

        self.btn_export_excel = ctk.CTkButton(
            botoes, text="Exportar Excel", width=130, height=34,
            fg_color=COR_PAINEL, hover_color="#C1ECFD",
            text_color=COR_TEXTO, command=self.on_export_excel
        )
        self.btn_export_excel.grid(row=0, column=0, padx=(0, 6))

        self.btn_export_pdf = ctk.CTkButton(
            botoes, text="Exportar PDF", width=110, height=34,
            fg_color=COR_PAINEL, hover_color="#C1ECFD",
            text_color=COR_TEXTO, command=self.on_export_pdf
        )
        self.btn_export_pdf.grid(row=0, column=1, padx=(6, 0))

    # -------------------------
    # Navegação mês/ano
    # -------------------------
    def mes_anterior(self):
        self.mes -= 1
        if self.mes == 0:
            self.mes = 12
            self.ano -= 1
        self.atualizar_dashboard()

    def mes_proximo(self):
        self.mes += 1
        if self.mes == 13:
            self.mes = 1
            self.ano += 1
        self.atualizar_dashboard()

    def ano_anterior(self):
        self.ano -= 1
        self.atualizar_dashboard()

    def ano_proximo(self):
        self.ano += 1
        self.atualizar_dashboard()

    # -------------------------
    # Helpers KPI
    # -------------------------
    def _mes_ano_anterior(self, mes, ano):
        mes -= 1
        if mes == 0:
            mes = 12
            ano -= 1
        return mes, ano

    def _cor_delta(self, delta):
        if delta is None:
            return COR_TEXTO_SEC
        if delta > 0:
            return "#2E7D32"
        if delta < 0:
            return "#C62828"
        return COR_TEXTO_SEC

    def _fmt_dinheiro(self, valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _fmt_percentual(self, delta):
        # delta vem como 0.12 -> "12%"
        return f"{delta*100:.0f}%"

    # -------------------------
    # Estado da tela (útil pra export e futuro DB)
    # -------------------------
    def get_state(self):
        return {
            "mes": self.mes,
            "ano": self.ano,
            "tipo": self.combo_tipo.get(),
            "categoria": self.combo_categoria.get(),
            "periodo": self.lbl_periodo.cget("text"),
        }

    # -------------------------
    # Atualização geral (KPIs + gráficos)
    # -------------------------
    def atualizar_dashboard(self):
        nomes_meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        self.lbl_periodo.configure(text=f"{nomes_meses[self.mes-1]}/{self.ano}")

        tipo = self.combo_tipo.get()
        categoria = self.combo_categoria.get()

        mes_ant, ano_ant = self._mes_ano_anterior(self.mes, self.ano)

        # seeds consistentes (atual e anterior)
        seed_atual = hash((self.ano, self.mes, tipo, categoria))
        seed_anterior = hash((ano_ant, mes_ant, tipo, categoria))

        rng_atual = random.Random(seed_atual)
        rng_ant = random.Random(seed_anterior)

        # Valores mês atual
        faturamento_mes = rng_atual.randint(12000, 26000)
        vendas_mes = rng_atual.randint(700, 1700)

        # Valores mês anterior
        faturamento_ant = rng_ant.randint(12000, 26000)
        vendas_ant = rng_ant.randint(700, 1700)

        # deltas
        delta_faturamento = None if faturamento_ant == 0 else (faturamento_mes - faturamento_ant) / faturamento_ant
        delta_vendas = None if vendas_ant == 0 else (vendas_mes - vendas_ant) / vendas_ant

        ticket = (faturamento_mes / vendas_mes) if vendas_mes else 0
        ticket_ant = (faturamento_ant / vendas_ant) if vendas_ant else 0
        delta_ticket = None if ticket_ant == 0 else (ticket - ticket_ant) / ticket_ant

        # KPIs: Faturamento
        lbl_v, lbl_d, lbl_s = self.kpis["faturamento"]
        lbl_v.configure(text=self._fmt_dinheiro(faturamento_mes))
        lbl_d.configure(text=self._fmt_percentual(delta_faturamento) if delta_faturamento is not None else "")
        lbl_d.configure(text_color=self._cor_delta(delta_faturamento))
        lbl_s.configure(text=f"vs {calendar.month_name[mes_ant]} {ano_ant}")

        # KPIs: Vendas
        lbl_v, lbl_d, lbl_s = self.kpis["vendas"]
        lbl_v.configure(text=f"{vendas_mes}")
        lbl_d.configure(text=self._fmt_percentual(delta_vendas) if delta_vendas is not None else "")
        lbl_d.configure(text_color=self._cor_delta(delta_vendas))
        lbl_s.configure(text=f"vs {calendar.month_name[mes_ant]} {ano_ant}")

        # KPIs: Ticket médio
        lbl_v, lbl_d, lbl_s = self.kpis["ticket"]
        lbl_v.configure(text=self._fmt_dinheiro(ticket))
        lbl_d.configure(text=self._fmt_percentual(delta_ticket) if delta_ticket is not None else "")
        lbl_d.configure(text_color=self._cor_delta(delta_ticket))
        lbl_s.configure(text="Faturamento ÷ Vendas")

        # --------- Gráfico 1 (linha)
        dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        serie = [rng_atual.randint(600, 2500) for _ in dias]

        def plot_faturamento(ax):
            ax.plot(dias, serie, marker="o")
            ax.set_ylabel("R$")
            ax.set_title("")

        self.graf1.atualizar_plot(plot_faturamento)

        # --------- Gráfico 2 (barras)
        produtos = self._produtos_por_categoria(categoria)
        qtd = [rng_atual.randint(80, 420) for _ in produtos]

        def plot_produtos(ax):
            ax.bar(produtos, qtd)
            ax.set_ylabel("Qtd")
            ax.set_title("")

        self.graf2.atualizar_plot(plot_produtos)

    def _produtos_por_categoria(self, categoria):
        if categoria == "Sorvete":
            return ["Chocolate", "Baunilha", "Morango", "Flocos"]
        if categoria == "Picolé":
            return ["Limão", "Uva", "Abacaxi", "Coco"]
        if categoria == "Açaí":
            return ["Açaí Puro", "Açaí c/ Morango", "Açaí c/ Banana", "Açaí c/ Granola"]
        if categoria == "Outros":
            return ["Caldinho", "Milkshake", "Café Gelado", "Churros"]
        return ["Chocolate", "Açaí", "Café Gelado", "Flocos"]

    # -------------------------
    # Botões exportação -> chamam export.py
    # -------------------------
    def on_export_excel(self):
        exportar_excel(self)

    def on_export_pdf(self):
        exportar_pdf(self)
