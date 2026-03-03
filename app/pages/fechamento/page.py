import customtkinter as ctk
from datetime import date, datetime

from app.config import theme


class PaginaFechamento(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        # Layout principal
        self.grid_columnconfigure(0, weight=2, uniform="cols")
        self.grid_columnconfigure(1, weight=3, uniform="cols")
        self.grid_rowconfigure(1, weight=1)

        # Estado
        self.data_fechamento = date.today()

        # Vars numéricas
        self.vendas_brutas_var = ctk.StringVar(value="0,00")
        self.descontos_var = ctk.StringVar(value="0,00")
        self.cancelamentos_var = ctk.StringVar(value="0,00")

        self.dinheiro_var = ctk.StringVar(value="0,00")
        self.pix_var = ctk.StringVar(value="0,00")
        self.cartao_var = ctk.StringVar(value="0,00")

        self.sangria_var = ctk.StringVar(value="0,00")
        self.suprimento_var = ctk.StringVar(value="0,00")
        self.caixa_inicial_var = ctk.StringVar(value="0,00")

        self.contado_caixa_var = ctk.StringVar(value="0,00")
        self.observacoes_var = ctk.StringVar(value="")

        # UI
        self._criar_topo()
        self._criar_coluna_esquerda()
        self._criar_coluna_direita()

        # Dados mock iniciais
        self._carregar_mock()
        self._atualizar_resumo()

    # =========================================================
    # UI
    # =========================================================
    def _criar_topo(self):
        topo = ctk.CTkFrame(self, fg_color=theme.COR_HOVER, corner_radius=16, height=110)
        topo.grid(row=0, column=0, columnspan=2, padx=30, pady=(20, 14), sticky="ew")
        topo.grid_columnconfigure(0, weight=1)
        topo.grid_propagate(False)

        ctk.CTkLabel(
            topo,
            text="Fechamento de Caixa",
            font=ctk.CTkFont(family=theme.FONTE, size=28, weight="bold"),
            text_color=theme.COR_TEXTO_SEC,
        ).grid(row=0, column=0, padx=20, pady=(18, 2), sticky="w")

        ctk.CTkLabel(
            topo,
            text=f"Conferência e encerramento do caixa • {self.data_fechamento.strftime('%d/%m/%Y')}",
            font=ctk.CTkFont(family=theme.FONTE, size=13),
            text_color=theme.COR_TEXTO_SEC,
        ).grid(row=1, column=0, padx=20, pady=(0, 14), sticky="w")

    def _criar_coluna_esquerda(self):
        coluna = ctk.CTkFrame(self, fg_color="transparent")
        coluna.grid(row=1, column=0, padx=(30, 12), pady=(0, 24), sticky="nsew")
        coluna.grid_columnconfigure(0, weight=1)
        coluna.grid_rowconfigure(0, weight=1)
        coluna.grid_rowconfigure(1, weight=1)

        self._criar_card_resumo(coluna)
        self._criar_card_movimentacoes(coluna)

    def _criar_coluna_direita(self):
        coluna = ctk.CTkFrame(self, fg_color="transparent")
        coluna.grid(row=1, column=1, padx=(12, 30), pady=(0, 24), sticky="nsew")
        coluna.grid_columnconfigure(0, weight=1)
        coluna.grid_rowconfigure(0, weight=1)
        coluna.grid_rowconfigure(1, weight=1)

        self._criar_card_conferencia(coluna)
        self._criar_card_acoes(coluna)

    # =========================================================
    # Cards - Esquerda
    # =========================================================
    def _criar_card_resumo(self, master):
        card = ctk.CTkFrame(master, fg_color=theme.COR_PAINEL, corner_radius=14)
        card.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
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

        self.lbl_resumo_receb_dinheiro = self._linha_resumo(card, 6, "Recebido em Dinheiro")
        self.lbl_resumo_receb_pix = self._linha_resumo(card, 7, "Recebido em Pix")
        self.lbl_resumo_receb_cartao = self._linha_resumo(card, 8, "Recebido em Cartão")
        self.lbl_resumo_receb_total = self._linha_resumo(card, 9, "Total recebido", destaque=True)

        ctk.CTkLabel(card, text="").grid(row=10, column=0, pady=(0, 6))

    def _linha_resumo(self, master, row, titulo, destaque=False):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.grid(row=row, column=0, padx=16, pady=3, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        font_label = ctk.CTkFont(family=theme.FONTE, size=12, weight="bold" if destaque else "normal")
        font_valor = ctk.CTkFont(family=theme.FONTE, size=12, weight="bold")

        ctk.CTkLabel(
            frame,
            text=titulo,
            font=font_label,
            text_color=theme.COR_TEXTO if destaque else theme.COR_TEXTO_SEC,
        ).grid(row=0, column=0, sticky="w")

        lbl_valor = ctk.CTkLabel(
            frame,
            text="R$ 0,00",
            font=font_valor,
            text_color=theme.COR_TEXTO,
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

        # Coluna esquerda
        self._campo_valor(card, "Vendas brutas", self.vendas_brutas_var, 1, 0)
        self._campo_valor(card, "Descontos", self.descontos_var, 2, 0)
        self._campo_valor(card, "Cancelamentos", self.cancelamentos_var, 3, 0)
        self._campo_valor(card, "Caixa inicial", self.caixa_inicial_var, 4, 0)

        # Coluna direita
        self._campo_valor(card, "Dinheiro", self.dinheiro_var, 1, 1)
        self._campo_valor(card, "Pix", self.pix_var, 2, 1)
        self._campo_valor(card, "Cartão", self.cartao_var, 3, 1)
        self._campo_valor(card, "Sangria", self.sangria_var, 4, 1)
        self._campo_valor(card, "Suprimento", self.suprimento_var, 5, 1)

        ctk.CTkLabel(
            card,
            text="(Use vírgula ou ponto. Ex: 120,50)",
            font=ctk.CTkFont(family=theme.FONTE, size=11),
            text_color=theme.COR_TEXTO_SEC,
        ).grid(row=6, column=0, columnspan=2, padx=16, pady=(8, 12), sticky="w")

    def _campo_valor(self, master, label, var, row, col):
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
            height=34
        )
        entry.pack(fill="x", pady=(4, 0))
        entry.bind("<KeyRelease>", lambda e: self._atualizar_resumo())

    # =========================================================
    # Cards - Direita
    # =========================================================
    def _criar_card_conferencia(self, master):
        card = ctk.CTkFrame(master, fg_color=theme.COR_PAINEL, corner_radius=14)
        card.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
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
            text="Gerar resumo / imprimir",
            height=38,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._gerar_resumo,
        )
        btn_imprimir.grid(row=4, column=0, padx=16, pady=(4, 14), sticky="ew")

    # =========================================================
    # Lógica
    # =========================================================
    def _parse_moeda(self, txt):
        if txt is None:
            return 0.0
        txt = str(txt).strip()
        if not txt:
            return 0.0

        txt = txt.replace("R$", "").replace(" ", "")
        txt = txt.replace(".", "").replace(",", ".")
        try:
            return float(txt)
        except ValueError:
            return 0.0

    def _fmt(self, valor):
        try:
            return theme.fmt_dinheiro(valor)
        except Exception:
            s = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"R$ {s}"

    def _atualizar_resumo(self):
        vendas_brutas = self._parse_moeda(self.vendas_brutas_var.get())
        descontos = self._parse_moeda(self.descontos_var.get())
        cancelamentos = self._parse_moeda(self.cancelamentos_var.get())

        dinheiro = self._parse_moeda(self.dinheiro_var.get())
        pix = self._parse_moeda(self.pix_var.get())
        cartao = self._parse_moeda(self.cartao_var.get())

        sangria = self._parse_moeda(self.sangria_var.get())
        suprimento = self._parse_moeda(self.suprimento_var.get())
        caixa_inicial = self._parse_moeda(self.caixa_inicial_var.get())

        contado = self._parse_moeda(self.contado_caixa_var.get())

        total_liquido = max(0.0, vendas_brutas - descontos - cancelamentos)
        total_recebido = dinheiro + pix + cartao

        previsto_em_caixa = caixa_inicial + dinheiro + suprimento - sangria
        diferenca = contado - previsto_em_caixa

        # Resumo esquerdo
        self.lbl_resumo_vendas_brutas.configure(text=self._fmt(vendas_brutas))
        self.lbl_resumo_descontos.configure(text=self._fmt(descontos))
        self.lbl_resumo_cancelamentos.configure(text=self._fmt(cancelamentos))
        self.lbl_resumo_liquido.configure(text=self._fmt(total_liquido))

        self.lbl_resumo_receb_dinheiro.configure(text=self._fmt(dinheiro))
        self.lbl_resumo_receb_pix.configure(text=self._fmt(pix))
        self.lbl_resumo_receb_cartao.configure(text=self._fmt(cartao))
        self.lbl_resumo_receb_total.configure(text=self._fmt(total_recebido))

        # Conferência direita
        self.lbl_previsto.configure(text=self._fmt(previsto_em_caixa))
        self.lbl_contado.configure(text=self._fmt(contado))
        self.lbl_diferenca.configure(text=self._fmt(diferenca))

        # Cor da diferença
        if abs(diferenca) < 0.005:
            cor = "#2E7D32"  # verde
            status = "Fechamento conferido sem diferença."
        elif diferenca > 0:
            cor = "#1565C0"  # azul
            status = f"Sobra de caixa: {self._fmt(diferenca)}"
        else:
            cor = "#C62828"  # vermelho
            status = f"Falta de caixa: {self._fmt(abs(diferenca))}"

        self.lbl_diferenca.configure(text_color=cor)
        self.lbl_status.configure(text=f"Status: {status}")

    def _conferir_fechamento(self):
        self._atualizar_resumo()
        agora = datetime.now().strftime("%H:%M:%S")
        self.lbl_status.configure(
            text=f"Status: conferência atualizada às {agora}",
            text_color=theme.COR_TEXTO_SEC
        )

    def _salvar_fechamento(self):
        self._atualizar_resumo()

        obs = self.txt_obs.get("1.0", "end").strip()
        # depois você troca por persistência no banco
        # ex.: repository.salvar_fechamento({...})

        resumo = (
            "Fechamento salvo (mock)\n"
            f"Data: {self.data_fechamento.strftime('%d/%m/%Y')}\n"
            f"Observações: {obs if obs else 'Sem observações'}"
        )
        self.lbl_status.configure(text=f"Status: {resumo}", wraplength=420)

    def _gerar_resumo(self):
        # depois: gerar PDF / impressão
        self.lbl_status.configure(
            text="Status: geração de resumo/comprovante ainda será integrada (mock)."
        )

    def _carregar_mock(self):
        # Mock para você visualizar a tela preenchida
        self.vendas_brutas_var.set("1250,00")
        self.descontos_var.set("35,00")
        self.cancelamentos_var.set("20,00")

        self.dinheiro_var.set("420,00")
        self.pix_var.set("500,00")
        self.cartao_var.set("295,00")

        self.sangria_var.set("150,00")
        self.suprimento_var.set("0,00")
        self.caixa_inicial_var.set("100,00")

        self.contado_caixa_var.set("370,00")