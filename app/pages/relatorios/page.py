import customtkinter as ctk
import datetime as dt
from pathlib import Path
import textwrap

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter, MaxNLocator

from app.config.theme import (
    COR_FUNDO, COR_PAINEL, COR_TEXTO, COR_TEXTO_SEC, FONTE
)

from app.pages.relatorios.export import exportar_excel, exportar_pdf


# ============================================================
# Cores auxiliares dos gráficos
# ============================================================
COR_GRAFICO_PRIMARIA = "#38BDF8"
COR_GRAFICO_SECUNDARIA = "#0EA5E9"
COR_GRAFICO_SUAVE = "#E0F2FE"
COR_BORDA_SUAVE = "#E5E7EB"
COR_EIXO = "#CBD5E1"
COR_GRID = "#94A3B8"


# ============================================================
# Widget: Card de gráfico responsivo
# ============================================================
class CardGraficoResponsivo(ctk.CTkFrame):
    def __init__(self, master, titulo: str, ratio: float = 0.60):
        super().__init__(
            master,
            fg_color="#FFFFFF",
            corner_radius=14,
            border_width=1,
            border_color=COR_BORDA_SUAVE
        )

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
        self.lbl_titulo.grid(row=0, column=0, padx=14, pady=(12, 8), sticky="w")

        self.fig = Figure(figsize=(5, 3), dpi=self.dpi, facecolor="#FFFFFF")
        self.ax = self.fig.add_subplot(111)
        self._estilizar_eixos_base(self.ax)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.configure(bg="#FFFFFF", highlightthickness=0, bd=0)
        self.canvas_widget.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")

        self.bind("<Configure>", self._ao_redimensionar)

    def _estilizar_eixos_base(self, ax):
        ax.set_facecolor("#FFFFFF")

        # bordas
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(COR_EIXO)
        ax.spines["bottom"].set_color(COR_EIXO)
        ax.spines["left"].set_linewidth(1.0)
        ax.spines["bottom"].set_linewidth(1.0)

        # ticks
        ax.tick_params(axis="x", colors=COR_TEXTO_SEC, labelsize=9, length=0, pad=6)
        ax.tick_params(axis="y", colors=COR_TEXTO_SEC, labelsize=9, length=0, pad=6)

        # grid padrão: só no eixo Y para reduzir ruído
        ax.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.18, color=COR_GRID)
        ax.grid(axis="x", visible=False)

        # margens internas melhores
        ax.margins(x=0.03)

    def _ao_redimensionar(self, event):
        # Evita redraw excessivo quando a largura praticamente não mudou
        if abs(event.width - self._ultimo_w) < 6:
            return

        self._ultimo_w = event.width

        largura_px = max(260, event.width - 24)
        altura_px = max(220, int(largura_px * self.ratio))

        self.fig.set_size_inches(
            largura_px / self.dpi,
            altura_px / self.dpi,
            forward=True
        )
        self.fig.subplots_adjust(left=0.10, right=0.98, top=0.95, bottom=0.18)
        self.canvas.draw_idle()

    def atualizar_plot(self, plot_fn):
        self.ax.clear()
        self._estilizar_eixos_base(self.ax)
        plot_fn(self.ax)
        self.fig.subplots_adjust(left=0.10, right=0.98, top=0.95, bottom=0.18)
        self.canvas.draw_idle()


# ============================================================
# Página: Relatórios
# ============================================================
class PaginaAdminRelatorios(ctk.CTkFrame):
    def __init__(self, master, sistema=None):
        super().__init__(master, fg_color=COR_FUNDO)

        self.sistema = sistema
        self._dados_dashboard = {
            "faturamento": 0.0,
            "qtd_vendas": 0,
            "ticket_medio": 0.0,
            "serie_por_dia": {},
            "top_produtos": [],
            "vendas": [],
            "taxas_entrega": 0.0,
        }

        # Caminho fixo para exportações:
        # geladocesistema/exports/relatorios
        self.diretorio_exports_relatorios = Path(__file__).resolve().parents[3] / "exports" / "relatorios"
        self.diretorio_exports_relatorios.mkdir(parents=True, exist_ok=True)

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
    # UI: KPIs
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
    # Helpers
    # -------------------------
    def _fmt_dinheiro(self, valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _fmt_dinheiro_curto(self, valor):
        valor = float(valor)
        abs_v = abs(valor)

        if abs_v >= 1_000_000:
            txt = f"R$ {valor / 1_000_000:.1f} mi"
        elif abs_v >= 1_000:
            txt = f"R$ {valor / 1_000:.1f} mil"
        else:
            txt = f"R$ {valor:.0f}"

        return txt.replace(".", ",")

    def _formatter_moeda_eixo(self, valor, _pos):
        return self._fmt_dinheiro_curto(valor)

    def _quebrar_rotulo(self, texto, largura=18):
        texto = str(texto).strip()
        if not texto:
            return ""
        return textwrap.fill(texto, width=largura)

    def _desenhar_estado_vazio(self, ax, titulo, subtitulo):
        ax.text(
            0.5, 0.57,
            titulo,
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=11,
            fontweight="bold",
            color=COR_TEXTO
        )
        ax.text(
            0.5, 0.45,
            subtitulo,
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=9,
            color=COR_TEXTO_SEC
        )
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_visible(False)

    def _ordenar_dias_serie(self, serie):
        def chave(valor):
            try:
                return (0, int(valor))
            except (TypeError, ValueError):
                return (1, str(valor))

        dias = sorted(serie.keys(), key=chave)
        valores = []
        for d in dias:
            try:
                valores.append(float(serie[d]))
            except Exception:
                valores.append(0.0)
        return dias, valores

    # -------------------------
    # Estado da tela
    # -------------------------
    def get_state(self):
        return {
            "mes": self.mes,
            "ano": self.ano,
            "tipo": self.combo_tipo.get(),
            "categoria": self.combo_categoria.get(),
            "periodo": self.lbl_periodo.cget("text"),
            "dados_relatorio": self._dados_dashboard,
            "output_dir": self.diretorio_exports_relatorios,
        }

    # -------------------------
    # Atualização geral (KPIs + gráficos)
    # -------------------------
    def atualizar_dashboard(self):
        nomes_meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        self.lbl_periodo.configure(text=f"{nomes_meses[self.mes - 1]}/{self.ano}")

        try:
            dados = self.sistema.dados_relatorio(
                mes=self.mes,
                ano=self.ano,
                tipo=self.combo_tipo.get(),
                categoria=self.combo_categoria.get(),
            )
        except Exception:
            dados = {
                "faturamento": 0,
                "qtd_vendas": 0,
                "ticket_medio": 0,
                "serie_por_dia": {},
                "top_produtos": [],
                "vendas": [],
                "taxas_entrega": 0,
            }

        self._dados_dashboard = dados

        faturamento = float(dados.get("faturamento", 0))
        vendas = int(dados.get("qtd_vendas", 0))
        ticket = float(dados.get("ticket_medio", 0))

        # KPI: Faturamento
        lbl_v, lbl_d, lbl_s = self.kpis["faturamento"]
        lbl_v.configure(text=self._fmt_dinheiro(faturamento))
        lbl_d.configure(text="")
        lbl_s.configure(text="Valor real do período")

        # KPI: Vendas
        lbl_v, lbl_d, lbl_s = self.kpis["vendas"]
        lbl_v.configure(text=str(vendas))
        lbl_d.configure(text="")
        lbl_s.configure(text="Quantidade real de vendas")

        # KPI: Ticket médio
        lbl_v, lbl_d, lbl_s = self.kpis["ticket"]
        lbl_v.configure(text=self._fmt_dinheiro(ticket))
        lbl_d.configure(text="")
        lbl_s.configure(text="Faturamento ÷ Vendas")

        # --------- Gráfico 1: faturamento por dia
        serie = dados.get("serie_por_dia", {}) or {}
        dias, valores = self._ordenar_dias_serie(serie)

        def plot_faturamento(ax):
            ax.set_ylabel("Faturamento", color=COR_TEXTO_SEC, fontsize=10)
            ax.yaxis.set_major_formatter(FuncFormatter(self._formatter_moeda_eixo))

            if dias and valores:
                x_pos = list(range(len(dias)))
                labels_dias = [str(d) for d in dias]

                # linha principal
                ax.plot(
                    x_pos, valores,
                    linewidth=2.4,
                    marker="o",
                    markersize=5.5,
                    color=COR_GRAFICO_SECUNDARIA,
                    solid_capstyle="round",
                    zorder=3
                )

                # preenchimento suave
                ax.fill_between(
                    x_pos, valores, 0,
                    color=COR_GRAFICO_SUAVE,
                    alpha=0.75,
                    zorder=1
                )

                # linha de média
                media = sum(valores) / len(valores) if valores else 0
                ax.axhline(
                    media,
                    linestyle="--",
                    linewidth=1.0,
                    color=COR_GRAFICO_PRIMARIA,
                    alpha=0.55,
                    zorder=2
                )

                # controle de densidade do eixo X
                if len(labels_dias) <= 8:
                    ticks = x_pos
                else:
                    passo = max(1, len(labels_dias) // 7)
                    ticks = list(range(0, len(labels_dias), passo))
                    if ticks[-1] != len(labels_dias) - 1:
                        ticks.append(len(labels_dias) - 1)

                ax.set_xticks(ticks)
                ax.set_xticklabels([labels_dias[i] for i in ticks])

                # limites e respiro
                maior = max(valores) if valores else 0
                topo = maior * 1.22 if maior > 0 else 1
                ax.set_ylim(bottom=0, top=topo)

                # marcação dos valores
                if len(valores) <= 8:
                    for x, y in zip(x_pos, valores):
                        ax.annotate(
                            self._fmt_dinheiro_curto(y),
                            (x, y),
                            textcoords="offset points",
                            xytext=(0, 8),
                            ha="center",
                            fontsize=8,
                            color=COR_TEXTO_SEC
                        )
                else:
                    idx_max = valores.index(max(valores))
                    ax.scatter(
                        [x_pos[idx_max]], [valores[idx_max]],
                        s=58,
                        color=COR_GRAFICO_PRIMARIA,
                        edgecolors="#FFFFFF",
                        linewidth=1.5,
                        zorder=4
                    )
                    ax.annotate(
                        f"Pico: {self._fmt_dinheiro_curto(valores[idx_max])}",
                        (x_pos[idx_max], valores[idx_max]),
                        textcoords="offset points",
                        xytext=(0, 10),
                        ha="center",
                        fontsize=8.5,
                        color=COR_TEXTO
                    )

                ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            else:
                self._desenhar_estado_vazio(
                    ax,
                    "Sem vendas no período",
                    "Altere o mês, ano ou os filtros para visualizar o histórico."
                )
                ax.set_ylabel("Faturamento", color=COR_TEXTO_SEC, fontsize=10)

        self.graf1.atualizar_plot(plot_faturamento)

        # --------- Gráfico 2: top produtos
        top = dados.get("top_produtos", []) or []

        def plot_produtos(ax):
            ax.set_xlabel("Quantidade vendida", color=COR_TEXTO_SEC, fontsize=10)

            if top:
                pares = []
                for item in top:
                    try:
                        nome = str(item[0])
                        qtd = float(item[1])
                        pares.append((nome, qtd))
                    except Exception:
                        continue

                if not pares:
                    self._desenhar_estado_vazio(
                        ax,
                        "Sem produtos vendidos",
                        "Não há dados válidos de produtos para os filtros selecionados."
                    )
                    ax.set_xlabel("Quantidade vendida", color=COR_TEXTO_SEC, fontsize=10)
                    return

                # Ordena do maior para o menor e limita visualmente aos 8 primeiros
                pares.sort(key=lambda x: x[1], reverse=True)
                pares = pares[:8]

                nomes = [self._quebrar_rotulo(p[0], largura=18) for p in pares]
                qtds = [p[1] for p in pares]

                y_pos = list(range(len(nomes)))

                barras = ax.barh(
                    y_pos, qtds,
                    height=0.58,
                    color=COR_GRAFICO_PRIMARIA,
                    alpha=0.88,
                    zorder=3
                )

                ax.set_yticks(y_pos)
                ax.set_yticklabels(nomes)
                ax.invert_yaxis()

                ax.grid(axis="x", linestyle="--", linewidth=0.8, alpha=0.18, color=COR_GRID)
                ax.grid(axis="y", visible=False)
                ax.xaxis.set_major_locator(MaxNLocator(integer=True))

                maior = max(qtds) if qtds else 0
                ax.set_xlim(0, maior * 1.20 if maior > 0 else 1)

                for barra, valor in zip(barras, qtds):
                    ax.text(
                        barra.get_width() + (maior * 0.02 if maior > 0 else 0.2),
                        barra.get_y() + barra.get_height() / 2,
                        f"{int(valor) if float(valor).is_integer() else valor}",
                        va="center",
                        ha="left",
                        fontsize=9,
                        color=COR_TEXTO
                    )
            else:
                self._desenhar_estado_vazio(
                    ax,
                    "Sem produtos vendidos",
                    "Ainda não há itens suficientes para montar o ranking."
                )
                ax.set_xlabel("Quantidade vendida", color=COR_TEXTO_SEC, fontsize=10)

        self.graf2.atualizar_plot(plot_produtos)

    # -------------------------
    # Botões exportação
    # -------------------------
    def on_export_excel(self):
        exportar_excel(self, output_dir=self.diretorio_exports_relatorios)

    def on_export_pdf(self):
        exportar_pdf(self, output_dir=self.diretorio_exports_relatorios)