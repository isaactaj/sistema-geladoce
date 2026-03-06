import customtkinter as ctk
from datetime import date, datetime, timedelta
from pathlib import Path

from app.config import theme
from app.pages.fechamento.comprovante_fechamento import GeradorComprovanteFechamento


class PaginaFechamento(ctk.CTkFrame):
    def __init__(self, master, sistema=None):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        self.sistema = sistema

        # Diretório de exportação:
        # page.py -> app/pages/fechamento/page.py
        # parents[3] = raiz do projeto (geladocesistema)
        base_project_dir = Path(__file__).resolve().parents[3]
        self.diretorio_exports_fechamentos = base_project_dir / "exports" / "fechamentos"
        self.diretorio_exports_fechamentos.mkdir(parents=True, exist_ok=True)

        self.gerador_comprovante = GeradorComprovanteFechamento(
            output_dir=self.diretorio_exports_fechamentos
        )

        # Layout principal
        self.grid_columnconfigure(0, weight=2, uniform="cols")
        self.grid_columnconfigure(1, weight=3, uniform="cols")
        self.grid_rowconfigure(1, weight=1)

        # Estado
        self.data_fechamento = date.today()
        self.data_fechamento_var = ctk.StringVar(value=self._formatar_data_exibicao(self.data_fechamento))

        # Vars automáticas (vindas da base de vendas)
        self.vendas_brutas_var = ctk.StringVar(value="0,00")
        self.descontos_var = ctk.StringVar(value="0,00")
        self.cancelamentos_var = ctk.StringVar(value="0,00")

        self.dinheiro_var = ctk.StringVar(value="0,00")
        self.pix_var = ctk.StringVar(value="0,00")
        self.cartao_var = ctk.StringVar(value="0,00")

        # Vars manuais do fechamento
        self.sangria_var = ctk.StringVar(value="0,00")
        self.caixa_inicial_var = ctk.StringVar(value="0,00")
        self.contado_caixa_var = ctk.StringVar(value="0,00")
        self.observacoes_var = ctk.StringVar(value="")

        # Referências de UI
        self.txt_obs = None
        self.lbl_status = None
        self.entry_data_topo = None

        # UI
        self._criar_topo()
        self._criar_coluna_esquerda()
        self._criar_coluna_direita()

        # Carrega automaticamente os dados do dia
        self.carregar_dados_do_dia()

    # =========================================================
    # UI
    # =========================================================
    def _criar_topo(self):
        topo = ctk.CTkFrame(self, fg_color=theme.COR_HOVER, corner_radius=16, height=96)
        topo.grid(row=0, column=0, columnspan=2, padx=30, pady=(20, 12), sticky="ew")
        topo.grid_columnconfigure(0, weight=1)
        topo.grid_columnconfigure(1, weight=0)
        topo.grid_propagate(False)

        ctk.CTkLabel(
            topo,
            text="Fechamento de Caixa",
            font=ctk.CTkFont(family=theme.FONTE, size=28, weight="bold"),
            text_color=theme.COR_TEXTO_SEC,
        ).grid(row=0, column=0, padx=20, pady=(16, 16), sticky="w")

        linha_data = ctk.CTkFrame(topo, fg_color="transparent")
        linha_data.grid(row=0, column=1, padx=(10, 20), pady=(16, 16), sticky="e")

        ctk.CTkLabel(
            linha_data,
            text="Data",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO_SEC,
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        btn_anterior = ctk.CTkButton(
            linha_data,
            text="←",
            width=36,
            height=32,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._voltar_um_dia,
        )
        btn_anterior.grid(row=0, column=1, padx=(0, 6))

        self.entry_data_topo = ctk.CTkEntry(
            linha_data,
            textvariable=self.data_fechamento_var,
            width=118,
            height=32
        )
        self.entry_data_topo.grid(row=0, column=2, padx=(0, 6))
        self.entry_data_topo.bind("<Return>", self._aplicar_data_digitada)

        btn_proximo = ctk.CTkButton(
            linha_data,
            text="→",
            width=36,
            height=32,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._avancar_um_dia,
        )
        btn_proximo.grid(row=0, column=3, padx=(0, 6))

        btn_hoje = ctk.CTkButton(
            linha_data,
            text="Hoje",
            width=64,
            height=32,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._ir_para_hoje,
        )
        btn_hoje.grid(row=0, column=4)

    def _criar_coluna_esquerda(self):
        coluna = ctk.CTkFrame(self, fg_color="transparent")
        coluna.grid(row=1, column=0, padx=(30, 12), pady=(0, 24), sticky="nsew")
        coluna.grid_columnconfigure(0, weight=1)
        coluna.grid_rowconfigure(0, weight=1)
        coluna.grid_rowconfigure(1, weight=1)

        # Conferência no topo da esquerda
        self._criar_card_conferencia(coluna)
        self._criar_card_movimentacoes(coluna)

    def _criar_coluna_direita(self):
        coluna = ctk.CTkFrame(self, fg_color="transparent")
        coluna.grid(row=1, column=1, padx=(12, 30), pady=(0, 24), sticky="nsew")
        coluna.grid_columnconfigure(0, weight=1)
        coluna.grid_rowconfigure(0, weight=1)
        coluna.grid_rowconfigure(1, weight=1)

        # Resumo no topo da direita (coluna mais larga)
        self._criar_card_resumo(coluna)
        self._criar_card_acoes(coluna)

    # =========================================================
    # Cards - Resumo / Movimentações / Conferência / Ações
    # =========================================================
    def _criar_card_resumo(self, master):
        card = ctk.CTkFrame(master, fg_color=theme.COR_PAINEL, corner_radius=14)
        card.grid(row=0, column=0, sticky="nsew", pady=(8, 10))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="Resumo do dia",
            font=ctk.CTkFont(family=theme.FONTE, size=17, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, padx=16, pady=(14, 10), sticky="w")

        self.lbl_resumo_vendas_brutas = self._linha_resumo(card, 1, "Vendas brutas")
        self.lbl_resumo_descontos = self._linha_resumo(card, 2, "Descontos")
        self.lbl_resumo_cancelamentos = self._linha_resumo(card, 3, "Cancelamentos")
        self.lbl_resumo_liquido = self._linha_resumo(card, 4, "Total líquido", destaque=True)

        sep = ctk.CTkFrame(card, fg_color=theme.COR_BOTAO, height=1)
        sep.grid(row=5, column=0, padx=16, pady=8, sticky="ew")

        self.lbl_resumo_receb_dinheiro = self._linha_resumo(card, 6, "Recebido em dinheiro")
        self.lbl_resumo_receb_pix = self._linha_resumo(card, 7, "Recebido em Pix")
        self.lbl_resumo_receb_cartao = self._linha_resumo(card, 8, "Recebido em cartão")
        self.lbl_resumo_receb_total = self._linha_resumo(card, 9, "Total recebido", destaque=True)

        ctk.CTkLabel(card, text="").grid(row=10, column=0, pady=(0, 8))

    def _linha_resumo(self, master, row, titulo, destaque=False):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.grid(row=row, column=0, padx=14, pady=2, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, minsize=120)

        font_label = ctk.CTkFont(
            family=theme.FONTE,
            size=11 if not destaque else 12,
            weight="bold" if destaque else "normal"
        )
        font_valor = ctk.CTkFont(family=theme.FONTE, size=12, weight="bold")

        ctk.CTkLabel(
            frame,
            text=titulo,
            font=font_label,
            text_color=theme.COR_TEXTO if destaque else theme.COR_TEXTO_SEC,
            anchor="w",
            justify="left",
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        lbl_valor = ctk.CTkLabel(
            frame,
            text="R$ 0,00",
            width=120,
            font=font_valor,
            text_color=theme.COR_TEXTO,
            anchor="e",
            justify="right",
        )
        lbl_valor.grid(row=0, column=1, sticky="e")
        return lbl_valor

    def _criar_card_movimentacoes(self, master):
        card = ctk.CTkFrame(master, fg_color=theme.COR_PAINEL, corner_radius=14)
        card.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text="Lançamentos do fechamento",
            font=ctk.CTkFont(family=theme.FONTE, size=17, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, columnspan=2, padx=16, pady=(14, 10), sticky="w")

        self._campo_valor(card, "Vendas brutas", self.vendas_brutas_var, 1, 0, somente_leitura=True)
        self._campo_valor(card, "Descontos", self.descontos_var, 2, 0, somente_leitura=True)
        self._campo_valor(card, "Cancelamentos", self.cancelamentos_var, 3, 0, somente_leitura=True)
        self._campo_valor(card, "Caixa inicial", self.caixa_inicial_var, 4, 0)

        self._campo_valor(card, "Dinheiro", self.dinheiro_var, 1, 1, somente_leitura=True)
        self._campo_valor(card, "Pix", self.pix_var, 2, 1, somente_leitura=True)
        self._campo_valor(card, "Cartão", self.cartao_var, 3, 1, somente_leitura=True)
        self._campo_valor(card, "Sangria", self.sangria_var, 4, 1)

        ctk.CTkLabel(
            card,
            text="(Campos de vendas e recebimentos são automáticos. Use vírgula ou ponto. Ex: 120,50)",
            font=ctk.CTkFont(family=theme.FONTE, size=11),
            text_color=theme.COR_TEXTO_SEC,
        ).grid(row=5, column=0, columnspan=2, padx=16, pady=(8, 12), sticky="w")

    def _campo_valor(self, master, label, var, row, col, somente_leitura=False):
        box = ctk.CTkFrame(master, fg_color="transparent")
        box.grid(row=row, column=col, padx=16, pady=4, sticky="ew")
        master.grid_columnconfigure(col, weight=1)

        ctk.CTkLabel(
            box,
            text=label,
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO,
        ).pack(anchor="w")

        entry = ctk.CTkEntry(
            box,
            textvariable=var,
            height=34,
            state="readonly" if somente_leitura else "normal"
        )
        entry.pack(fill="x", pady=(4, 0))

        if not somente_leitura:
            entry.bind("<KeyRelease>", lambda e: self._atualizar_resumo())

        return entry

    def _criar_card_conferencia(self, master):
        card = ctk.CTkFrame(master, fg_color=theme.COR_PAINEL, corner_radius=14)
        card.grid(row=0, column=0, sticky="nsew", pady=(8, 10))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="Conferência de caixa",
            font=ctk.CTkFont(family=theme.FONTE, size=17, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, padx=16, pady=(14, 10), sticky="w")

        self._campo_valor_unico(card, "Valor contado no caixa (dinheiro físico)", self.contado_caixa_var, 1)

        self.lbl_previsto = self._linha_conferencia(card, 2, "Previsto em caixa")
        self.lbl_contado = self._linha_conferencia(card, 3, "Contado em caixa")
        self.lbl_diferenca = self._linha_conferencia(card, 4, "Diferença", destaque=True)

        ctk.CTkLabel(
            card,
            text="Observações",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO,
        ).grid(row=5, column=0, padx=16, pady=(10, 4), sticky="w")

        self.txt_obs = ctk.CTkTextbox(card, height=100)
        self.txt_obs.grid(row=6, column=0, padx=16, pady=(0, 14), sticky="ew")

    def _campo_valor_unico(self, master, label, var, row):
        ctk.CTkLabel(
            master,
            text=label,
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO,
            justify="left",
            anchor="w",
            wraplength=300,
        ).grid(row=row, column=0, padx=16, pady=(0, 4), sticky="w")

        entry = ctk.CTkEntry(master, textvariable=var, height=34)
        entry.grid(row=row + 1, column=0, padx=16, pady=(0, 8), sticky="ew")
        entry.bind("<KeyRelease>", lambda e: self._atualizar_resumo())

    def _linha_conferencia(self, master, row, titulo, destaque=False):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.grid(row=row + 2, column=0, padx=16, pady=3, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text=titulo,
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold" if destaque else "normal"),
            text_color=theme.COR_TEXTO if destaque else theme.COR_TEXTO_SEC,
        ).grid(row=0, column=0, sticky="w")

        lbl = ctk.CTkLabel(
            frame,
            text="R$ 0,00",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO,
        )
        lbl.grid(row=0, column=1, sticky="e")
        return lbl

    def _criar_card_acoes(self, master):
        card = ctk.CTkFrame(master, fg_color=theme.COR_PAINEL, corner_radius=14)
        card.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="Ações",
            font=ctk.CTkFont(family=theme.FONTE, size=17, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, padx=16, pady=(14, 10), sticky="w")

        self.lbl_status = ctk.CTkLabel(
            card,
            text="Status: aguardando conferência",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC,
            anchor="w",
            justify="left",
            wraplength=420,
        )
        self.lbl_status.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")

        btn_conferir = ctk.CTkButton(
            card,
            text="Conferir fechamento",
            height=38,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._conferir_fechamento,
        )
        btn_conferir.grid(row=2, column=0, padx=16, pady=4, sticky="ew")

        btn_salvar = ctk.CTkButton(
            card,
            text="Salvar fechamento",
            height=40,
            fg_color="#FFFFFF",
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._salvar_fechamento,
        )
        btn_salvar.grid(row=3, column=0, padx=16, pady=4, sticky="ew")

        btn_imprimir = ctk.CTkButton(
            card,
            text="Gerar comprovante / imprimir",
            height=38,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._gerar_resumo,
        )
        btn_imprimir.grid(row=4, column=0, padx=16, pady=(4, 14), sticky="ew")

    # =========================================================
    # Helpers
    # =========================================================
    def _formatar_data_exibicao(self, valor):
        if isinstance(valor, datetime):
            valor = valor.date()
        if isinstance(valor, date):
            return valor.strftime("%d/%m/%Y")
        return date.today().strftime("%d/%m/%Y")

    def _sincronizar_data_ui(self):
        self.data_fechamento_var.set(self._formatar_data_exibicao(self.data_fechamento))

    def _parse_moeda(self, txt):
        if txt is None:
            return 0.0

        txt = str(txt).strip()
        if not txt:
            return 0.0

        txt = txt.replace("R$", "").replace(" ", "")

        if "," in txt and "." in txt:
            txt = txt.replace(".", "").replace(",", ".")
        elif "," in txt:
            txt = txt.replace(",", ".")

        try:
            return float(txt)
        except ValueError:
            return 0.0

    def _fmt(self, valor):
        try:
            return theme.fmt_dinheiro(valor)
        except Exception:
            s = f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"R$ {s}"

    def _fmt_entry(self, valor):
        try:
            numero = float(valor)
        except Exception:
            numero = 0.0
        return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _set_textbox(self, texto):
        if self.txt_obs is None:
            return
        self.txt_obs.delete("1.0", "end")
        if texto:
            self.txt_obs.insert("1.0", str(texto))

    def _get_textbox(self):
        if self.txt_obs is None:
            return ""
        return self.txt_obs.get("1.0", "end").strip()

    def _obter_historico_fechamentos(self):
        try:
            if hasattr(self.sistema, "listar_fechamentos"):
                dados = self.sistema.listar_fechamentos()
                return dados if isinstance(dados, list) else []
            if hasattr(self.sistema, "listar_fechamento"):
                dados = self.sistema.listar_fechamento()
                return dados if isinstance(dados, list) else []
        except Exception:
            pass
        return []

    def _obter_fechamento_atual(self):
        try:
            if self.sistema and hasattr(self.sistema, "obter_fechamento_por_data"):
                return self.sistema.obter_fechamento_por_data(self.data_fechamento)
        except Exception:
            pass
        return None

    def _montar_payload_fechamento(self):
        obs = self._get_textbox()
        self.observacoes_var.set(obs)

        return {
            "data_fechamento": self.data_fechamento,
            "vendas_brutas": self.vendas_brutas_var.get(),
            "descontos": self.descontos_var.get(),
            "cancelamentos": self.cancelamentos_var.get(),
            "dinheiro": self.dinheiro_var.get(),
            "pix": self.pix_var.get(),
            "cartao": self.cartao_var.get(),
            "sangria": self.sangria_var.get(),
            "caixa_inicial": self.caixa_inicial_var.get(),
            "contado_caixa": self.contado_caixa_var.get(),
            "observacao": obs,
        }

    def _persistir_fechamento(self):
        if not hasattr(self.sistema, "salvar_fechamento"):
            raise AttributeError("SistemaService sem o método salvar_fechamento.")

        payload = self._montar_payload_fechamento()

        try:
            return self.sistema.salvar_fechamento(**payload)
        except TypeError as e:
            if "suprimento" in str(e).lower():
                payload_legado = dict(payload)
                payload_legado["suprimento"] = "0,00"
                return self.sistema.salvar_fechamento(**payload_legado)
            raise

    # =========================================================
    # Seletor de data
    # =========================================================
    def _voltar_um_dia(self):
        self.definir_data_fechamento(self.data_fechamento - timedelta(days=1))

    def _avancar_um_dia(self):
        self.definir_data_fechamento(self.data_fechamento + timedelta(days=1))

    def _ir_para_hoje(self):
        self.definir_data_fechamento(date.today())

    def _aplicar_data_digitada(self, event=None):
        texto = self.data_fechamento_var.get().strip()
        if not texto:
            self._sincronizar_data_ui()
            return

        try:
            self.definir_data_fechamento(texto)
        except Exception:
            self._sincronizar_data_ui()
            if self.lbl_status is not None:
                self.lbl_status.configure(
                    text="Status: data inválida. Use DD/MM/AAAA ou AAAA-MM-DD.",
                    text_color=theme.COR_TEXTO_SEC
                )

    # =========================================================
    # Carga de dados
    # =========================================================
    def _carregar_resumo_automatico(self):
        try:
            resumo = self.sistema.resumo_fechamento(self.data_fechamento)
        except Exception:
            resumo = {
                "vendas_brutas": 0,
                "descontos": 0,
                "cancelamentos": 0,
                "dinheiro": 0,
                "pix": 0,
                "cartao": 0,
            }

        self.vendas_brutas_var.set(self._fmt_entry(resumo.get("vendas_brutas", 0)))
        self.descontos_var.set(self._fmt_entry(resumo.get("descontos", 0)))
        self.cancelamentos_var.set(self._fmt_entry(resumo.get("cancelamentos", 0)))

        self.dinheiro_var.set(self._fmt_entry(resumo.get("dinheiro", 0)))
        self.pix_var.set(self._fmt_entry(resumo.get("pix", 0)))
        self.cartao_var.set(self._fmt_entry(resumo.get("cartao", 0)))

        self._sincronizar_data_ui()

    def _carregar_fechamento_salvo(self, preservar_digitado=False):
        fechamento = self._obter_fechamento_atual()

        if preservar_digitado:
            return fechamento

        if fechamento:
            self.sangria_var.set(self._fmt_entry(fechamento.get("sangria", 0)))
            self.caixa_inicial_var.set(self._fmt_entry(fechamento.get("caixa_inicial", 0)))
            self.contado_caixa_var.set(self._fmt_entry(fechamento.get("contado_caixa", 0)))

            obs = fechamento.get("observacao", "")
            self.observacoes_var.set(str(obs))
            self._set_textbox(obs)
            return fechamento

        self.sangria_var.set("0,00")
        self.caixa_inicial_var.set("0,00")
        self.contado_caixa_var.set("0,00")
        self.observacoes_var.set("")
        self._set_textbox("")

        return None

    def definir_data_fechamento(self, nova_data):
        if isinstance(nova_data, datetime):
            self.data_fechamento = nova_data.date()
        elif isinstance(nova_data, date):
            self.data_fechamento = nova_data
        else:
            txt = str(nova_data).strip()
            try:
                self.data_fechamento = datetime.strptime(txt, "%Y-%m-%d").date()
            except ValueError:
                self.data_fechamento = datetime.strptime(txt, "%d/%m/%Y").date()

        self.carregar_dados_do_dia(preservar_digitado=False)

    def carregar_dados_do_dia(self, preservar_digitado=False):
        self._carregar_resumo_automatico()
        self._carregar_fechamento_salvo(preservar_digitado=preservar_digitado)
        self._atualizar_resumo()

    # =========================================================
    # Lógica
    # =========================================================
    def _atualizar_resumo(self):
        vendas_brutas = self._parse_moeda(self.vendas_brutas_var.get())
        descontos = self._parse_moeda(self.descontos_var.get())
        cancelamentos = self._parse_moeda(self.cancelamentos_var.get())

        dinheiro = self._parse_moeda(self.dinheiro_var.get())
        pix = self._parse_moeda(self.pix_var.get())
        cartao = self._parse_moeda(self.cartao_var.get())

        sangria = self._parse_moeda(self.sangria_var.get())
        caixa_inicial = self._parse_moeda(self.caixa_inicial_var.get())
        contado = self._parse_moeda(self.contado_caixa_var.get())

        total_liquido = max(0.0, vendas_brutas - descontos - cancelamentos)
        total_recebido = dinheiro + pix + cartao

        previsto_em_caixa = caixa_inicial + dinheiro - sangria
        diferenca = contado - previsto_em_caixa

        self.lbl_resumo_vendas_brutas.configure(text=self._fmt(vendas_brutas))
        self.lbl_resumo_descontos.configure(text=self._fmt(descontos))
        self.lbl_resumo_cancelamentos.configure(text=self._fmt(cancelamentos))
        self.lbl_resumo_liquido.configure(text=self._fmt(total_liquido))

        self.lbl_resumo_receb_dinheiro.configure(text=self._fmt(dinheiro))
        self.lbl_resumo_receb_pix.configure(text=self._fmt(pix))
        self.lbl_resumo_receb_cartao.configure(text=self._fmt(cartao))
        self.lbl_resumo_receb_total.configure(text=self._fmt(total_recebido))

        self.lbl_previsto.configure(text=self._fmt(previsto_em_caixa))
        self.lbl_contado.configure(text=self._fmt(contado))
        self.lbl_diferenca.configure(text=self._fmt(diferenca))

        if abs(diferenca) < 0.005:
            cor = "#2E7D32"
            status = "Fechamento conferido sem diferença."
        elif diferenca > 0:
            cor = "#1565C0"
            status = f"Sobra de caixa: {self._fmt(diferenca)}"
        else:
            cor = "#C62828"
            status = f"Falta de caixa: {self._fmt(abs(diferenca))}"

        self.lbl_diferenca.configure(text_color=cor)

        if self.lbl_status is not None:
            self.lbl_status.configure(
                text=f"Status: {status}",
                text_color=theme.COR_TEXTO_SEC
            )

    def _conferir_fechamento(self):
        self._carregar_resumo_automatico()
        self._atualizar_resumo()

        agora = datetime.now().strftime("%H:%M:%S")
        self.lbl_status.configure(
            text=f"Status: conferência atualizada às {agora}",
            text_color=theme.COR_TEXTO_SEC
        )

    def _salvar_fechamento(self):
        self._carregar_resumo_automatico()
        self._atualizar_resumo()

        if not hasattr(self.sistema, "salvar_fechamento"):
            self.lbl_status.configure(
                text=(
                    "Status: o SistemaService ainda não possui salvar_fechamento. "
                    "Implemente o método para persistir o fechamento."
                ),
                wraplength=420,
                text_color=theme.COR_TEXTO_SEC,
            )
            return

        try:
            self._persistir_fechamento()
            self.carregar_dados_do_dia(preservar_digitado=False)

            self.lbl_status.configure(
                text=f"Status: fechamento salvo com sucesso • {self.data_fechamento.strftime('%d/%m/%Y')}",
                wraplength=420,
                text_color=theme.COR_TEXTO_SEC,
            )

        except Exception as e:
            self.lbl_status.configure(
                text=f"Status: erro ao salvar fechamento: {e}",
                wraplength=420,
                text_color=theme.COR_TEXTO_SEC,
            )

    def _gerar_resumo(self):
        self._carregar_resumo_automatico()
        self._atualizar_resumo()

        try:
            fechamento = self._obter_fechamento_atual()

            if not fechamento:
                if not hasattr(self.sistema, "salvar_fechamento"):
                    self.lbl_status.configure(
                        text=(
                            f"Status: ainda não existe fechamento salvo para {self.data_fechamento.strftime('%d/%m/%Y')} "
                            "e o SistemaService não possui salvar_fechamento."
                        ),
                        wraplength=420,
                        text_color=theme.COR_TEXTO_SEC,
                    )
                    return

                fechamento = self._persistir_fechamento()

            caminho_pdf = self.gerador_comprovante.gerar_pdf(fechamento)
            historico = self._obter_historico_fechamentos()
            total_historico = len(historico)

            self.lbl_status.configure(
                text=(
                    f"Status: comprovante gerado com sucesso • "
                    f"{self.data_fechamento.strftime('%d/%m/%Y')} • "
                    f"Histórico: {total_historico} fechamento(s) • "
                    f"Arquivo: {caminho_pdf}"
                ),
                wraplength=420,
                text_color=theme.COR_TEXTO_SEC,
            )

        except Exception as e:
            self.lbl_status.configure(
                text=f"Status: erro ao gerar comprovante: {e}",
                wraplength=420,
                text_color=theme.COR_TEXTO_SEC,
            )