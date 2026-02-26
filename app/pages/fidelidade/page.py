import customtkinter as ctk
from datetime import datetime

from app.config.theme import (
    COR_FUNDO,
    COR_PAINEL,
    COR_BOTAO,
    COR_HOVER,
    COR_TEXTO,
    COR_TEXTO_SEC,
    COR_SUCESSO,
    COR_ERRO,
    FONTE,
    fmt_dinheiro,
)


class PaginaFidelidade(ctk.CTkFrame):
    """
    Página de Fidelidade - Geladoce

    Estrutura responsiva (baseada em 1100x680):
    - Linha superior:
        1) Resumo do cliente
        2) Buscar cliente
    - Linha inferior:
        3) Cálculo automático de pontos
        4) Ações de fidelidade

    RN05:
    - Varejo: 1 ponto a cada R$ 5,00 gasto
    - Revendedor: 2 pontos a cada R$ 50,00 gastos
    """

    LARGURA_BASE = 1100
    ALTURA_BASE = 680

    def __init__(self, master):
        super().__init__(master, fg_color=COR_FUNDO)

        self.cliente_selecionado = None

        # =====================================================
        # Fontes (criadas uma vez, depois apenas reconfiguradas)
        # =====================================================
        self.font_titulo = ctk.CTkFont(family=FONTE, size=22, weight="bold")
        self.font_subtitulo = ctk.CTkFont(family=FONTE, size=11)
        self.font_card_titulo = ctk.CTkFont(family=FONTE, size=16, weight="bold")
        self.font_label = ctk.CTkFont(family=FONTE, size=11, weight="bold")
        self.font_valor = ctk.CTkFont(family=FONTE, size=11)
        self.font_botao = ctk.CTkFont(family=FONTE, size=11, weight="bold")
        self.font_feedback = ctk.CTkFont(family=FONTE, size=11)
        self.font_destaque = ctk.CTkFont(family=FONTE, size=24, weight="bold")
        self.font_segmented = ctk.CTkFont(family=FONTE, size=10, weight="bold")

        # alturas dinâmicas
        self.entry_height = 38
        self.button_height = 36
        self.segmented_height = 34
        self.textbox_height = 84

        self._criar_layout_principal()
        self._criar_frame_resumo_cliente()
        self._criar_frame_busca_cliente()
        self._criar_frame_calculo_automatico()
        self._criar_frame_acoes_fidelidade()

        self._carregar_cliente_exemplo()
        self._atualizar_interface_cliente()

        # Responsividade real conforme a área renderizada
        self.bind("<Configure>", self._ao_redimensionar)

    # =========================================================
    # LAYOUT PRINCIPAL
    # =========================================================
    def _criar_layout_principal(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.frame_topo = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_topo.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 10))
        self.frame_topo.grid_columnconfigure(0, weight=1)

        self.label_titulo = ctk.CTkLabel(
            self.frame_topo,
            text="Fidelidade",
            font=self.font_titulo,
            text_color=COR_TEXTO,
        )
        self.label_titulo.grid(row=0, column=0, sticky="w")

        self.label_subtitulo = ctk.CTkLabel(
            self.frame_topo,
            text="Gerencie clientes, pontuação e movimentações do programa de fidelidade.",
            font=self.font_subtitulo,
            text_color=COR_TEXTO_SEC,
        )
        self.label_subtitulo.grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.label_regra = ctk.CTkLabel(
            self.frame_topo,
            text="RN05 • Varejo: 1 ponto / R$ 5,00 • Revendedor: 2 pontos / R$ 50,00",
            font=self.font_subtitulo,
            text_color=COR_TEXTO,
        )
        self.label_regra.grid(row=2, column=0, sticky="w", pady=(6, 0))

        self.frame_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_grid.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))

        # 2 colunas iguais
        self.frame_grid.grid_columnconfigure(0, weight=1, uniform="col")
        self.frame_grid.grid_columnconfigure(1, weight=1, uniform="col")

        # Linha superior recebe mais espaço para evitar corte no resumo
        self.frame_grid.grid_rowconfigure(0, weight=11)
        self.frame_grid.grid_rowconfigure(1, weight=9)

    # =========================================================
    # FRAME 1 - RESUMO DO CLIENTE
    # =========================================================
    def _criar_frame_resumo_cliente(self):
        self.frame_resumo = ctk.CTkFrame(
            self.frame_grid,
            fg_color=COR_PAINEL,
            corner_radius=14,
        )
        self.frame_resumo.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        self.frame_resumo.grid_columnconfigure(1, weight=1)
        self.frame_resumo.grid_rowconfigure(10, weight=1)

        self.label_resumo_titulo = ctk.CTkLabel(
            self.frame_resumo,
            text="Resumo do cliente",
            font=self.font_card_titulo,
            text_color=COR_TEXTO,
        )
        self.label_resumo_titulo.grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 8))

        self.var_nome = ctk.StringVar(value="-")
        self.var_telefone = ctk.StringVar(value="-")
        self.var_cadastro = ctk.StringVar(value="-")
        self.var_tipo_cliente = ctk.StringVar(value="-")
        self.var_pontos_atuais = ctk.StringVar(value="0")
        self.var_total_acumulado = ctk.StringVar(value="0")
        self.var_ultima_compra = ctk.StringVar(value="-")
        self.var_status = ctk.StringVar(value="Inativo")
        self.var_nivel = ctk.StringVar(value="-")

        self._resumo_rotulos = []
        self._resumo_valores = []

        campos = [
            ("Nome", self.var_nome),
            ("Telefone", self.var_telefone),
            ("Cadastro", self.var_cadastro),
            ("Tipo", self.var_tipo_cliente),
            ("Pontos atuais", self.var_pontos_atuais),
            ("Total acumulado", self.var_total_acumulado),
            ("Última compra", self.var_ultima_compra),
            ("Status", self.var_status),
            ("Nível", self.var_nivel),
        ]

        for i, (rotulo, variavel) in enumerate(campos, start=1):
            lbl_rotulo = ctk.CTkLabel(
                self.frame_resumo,
                text=f"{rotulo}:",
                font=self.font_label,
                text_color=COR_TEXTO,
            )
            lbl_rotulo.grid(row=i, column=0, sticky="w", padx=(14, 8), pady=3)

            lbl_valor = ctk.CTkLabel(
                self.frame_resumo,
                textvariable=variavel,
                font=self.font_valor,
                text_color=COR_TEXTO_SEC,
                anchor="w",
            )
            lbl_valor.grid(row=i, column=1, sticky="w", padx=(0, 14), pady=3)

            self._resumo_rotulos.append(lbl_rotulo)
            self._resumo_valores.append(lbl_valor)

        self.label_status_operacao = ctk.CTkLabel(
            self.frame_resumo,
            text="Selecione ou busque um cliente para começar.",
            font=self.font_feedback,
            text_color=COR_TEXTO_SEC,
            wraplength=420,
            justify="left",
        )
        self.label_status_operacao.grid(
            row=10,
            column=0,
            columnspan=2,
            sticky="sw",
            padx=14,
            pady=(8, 12),
        )

    # =========================================================
    # FRAME 2 - BUSCAR CLIENTE
    # =========================================================
    def _criar_frame_busca_cliente(self):
        self.frame_busca = ctk.CTkFrame(
            self.frame_grid,
            fg_color=COR_PAINEL,
            corner_radius=14,
        )
        self.frame_busca.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))
        self.frame_busca.grid_columnconfigure(0, weight=1)
        self.frame_busca.grid_rowconfigure(5, weight=1)

        self.label_busca_titulo = ctk.CTkLabel(
            self.frame_busca,
            text="Buscar cliente",
            font=self.font_card_titulo,
            text_color=COR_TEXTO,
        )
        self.label_busca_titulo.grid(row=0, column=0, sticky="w", padx=14, pady=(12, 8))

        self.entry_nome = ctk.CTkEntry(
            self.frame_busca,
            placeholder_text="Nome",
            height=self.entry_height,
            corner_radius=10,
        )
        self.entry_nome.grid(row=1, column=0, sticky="ew", padx=14, pady=5)

        self.entry_telefone = ctk.CTkEntry(
            self.frame_busca,
            placeholder_text="Telefone",
            height=self.entry_height,
            corner_radius=10,
        )
        self.entry_telefone.grid(row=2, column=0, sticky="ew", padx=14, pady=5)

        self.entry_codigo = ctk.CTkEntry(
            self.frame_busca,
            placeholder_text="Código / ID",
            height=self.entry_height,
            corner_radius=10,
        )
        self.entry_codigo.grid(row=3, column=0, sticky="ew", padx=14, pady=5)

        # Botões reorganizados para não cortar em 1100x680
        self.frame_botoes_busca = ctk.CTkFrame(self.frame_busca, fg_color="transparent")
        self.frame_botoes_busca.grid(row=4, column=0, sticky="ew", padx=14, pady=(8, 12))
        self.frame_botoes_busca.grid_columnconfigure(0, weight=1)
        self.frame_botoes_busca.grid_columnconfigure(1, weight=1)

        self.btn_buscar = ctk.CTkButton(
            self.frame_botoes_busca,
            text="Buscar",
            height=self.button_height,
            fg_color=COR_BOTAO,
            hover_color=COR_HOVER,
            text_color=COR_TEXTO,
            font=self.font_botao,
            command=self.buscar_cliente,
        )
        self.btn_buscar.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=(0, 5))

        self.btn_limpar = ctk.CTkButton(
            self.frame_botoes_busca,
            text="Limpar",
            height=self.button_height,
            fg_color=COR_BOTAO,
            hover_color=COR_HOVER,
            text_color=COR_TEXTO,
            font=self.font_botao,
            command=self.limpar_busca,
        )
        self.btn_limpar.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=(0, 5))

        self.btn_novo_cliente = ctk.CTkButton(
            self.frame_botoes_busca,
            text="Novo cliente",
            height=self.button_height,
            fg_color=COR_BOTAO,
            hover_color=COR_HOVER,
            text_color=COR_TEXTO,
            font=self.font_botao,
            command=self.novo_cliente,
        )
        self.btn_novo_cliente.grid(row=1, column=0, columnspan=2, sticky="ew")

    # =========================================================
    # FRAME 3 - CÁLCULO AUTOMÁTICO
    # =========================================================
    def _criar_frame_calculo_automatico(self):
        self.frame_calculo = ctk.CTkFrame(
            self.frame_grid,
            fg_color=COR_PAINEL,
            corner_radius=14,
        )
        self.frame_calculo.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(8, 0))
        self.frame_calculo.grid_columnconfigure(0, weight=1)
        self.frame_calculo.grid_rowconfigure(6, weight=1)

        self.label_calculo_titulo = ctk.CTkLabel(
            self.frame_calculo,
            text="Cálculo automático de pontos",
            font=self.font_card_titulo,
            text_color=COR_TEXTO,
        )
        self.label_calculo_titulo.grid(row=0, column=0, sticky="w", padx=14, pady=(12, 8))

        self.combo_tipo_cliente = ctk.CTkOptionMenu(
            self.frame_calculo,
            values=["Varejo", "Revendedor"],
            height=self.entry_height,
            corner_radius=10,
            fg_color=COR_BOTAO,
            button_color=COR_HOVER,
            button_hover_color=COR_HOVER,
            text_color=COR_TEXTO,
            dropdown_fg_color=COR_BOTAO,
            dropdown_text_color=COR_TEXTO,
            dropdown_hover_color=COR_HOVER,
            font=self.font_botao,
        )
        self.combo_tipo_cliente.grid(row=1, column=0, sticky="ew", padx=14, pady=5)
        self.combo_tipo_cliente.set("Varejo")

        self.entry_valor_compra = ctk.CTkEntry(
            self.frame_calculo,
            placeholder_text="Valor da compra (ex.: 50,00)",
            height=self.entry_height,
            corner_radius=10,
        )
        self.entry_valor_compra.grid(row=2, column=0, sticky="ew", padx=14, pady=5)

        self.btn_calcular = ctk.CTkButton(
            self.frame_calculo,
            text="Calcular pontos",
            height=self.button_height,
            fg_color=COR_BOTAO,
            hover_color=COR_HOVER,
            text_color=COR_TEXTO,
            font=self.font_botao,
            command=self.calcular_pontos_interface,
        )
        self.btn_calcular.grid(row=3, column=0, sticky="ew", padx=14, pady=(8, 6))

        self.var_pontos_calculados = ctk.StringVar(value="0")
        self.var_regra_aplicada = ctk.StringVar(value="Aguardando cálculo.")

        self.label_pontos_calculados = ctk.CTkLabel(
            self.frame_calculo,
            text="Pontos calculados",
            font=self.font_label,
            text_color=COR_TEXTO,
        )
        self.label_pontos_calculados.grid(row=4, column=0, sticky="w", padx=14, pady=(6, 0))

        self.label_pontos_valor = ctk.CTkLabel(
            self.frame_calculo,
            textvariable=self.var_pontos_calculados,
            font=self.font_destaque,
            text_color=COR_SUCESSO,
        )
        self.label_pontos_valor.grid(row=5, column=0, sticky="w", padx=14, pady=(0, 2))

        self.label_regra_aplicada = ctk.CTkLabel(
            self.frame_calculo,
            textvariable=self.var_regra_aplicada,
            font=self.font_feedback,
            text_color=COR_TEXTO_SEC,
            wraplength=420,
            justify="left",
        )
        self.label_regra_aplicada.grid(row=6, column=0, sticky="sw", padx=14, pady=(2, 12))

    # =========================================================
    # FRAME 4 - AÇÕES DE FIDELIDADE
    # =========================================================
    def _criar_frame_acoes_fidelidade(self):
        self.frame_acoes = ctk.CTkFrame(
            self.frame_grid,
            fg_color=COR_PAINEL,
            corner_radius=14,
        )
        self.frame_acoes.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(8, 0))
        self.frame_acoes.grid_columnconfigure(0, weight=1)
        self.frame_acoes.grid_rowconfigure(7, weight=1)

        self.label_acoes_titulo = ctk.CTkLabel(
            self.frame_acoes,
            text="Ações de fidelidade",
            font=self.font_card_titulo,
            text_color=COR_TEXTO,
        )
        self.label_acoes_titulo.grid(row=0, column=0, sticky="w", padx=14, pady=(12, 8))

        self.segmented_acao = ctk.CTkSegmentedButton(
            self.frame_acoes,
            values=["Adicionar", "Remover", "Resgatar", "Bônus", "Zerar"],
            height=self.segmented_height,
            fg_color=COR_BOTAO,
            selected_color=COR_HOVER,
            selected_hover_color=COR_HOVER,
            unselected_color=COR_BOTAO,
            unselected_hover_color=COR_HOVER,
            text_color=COR_TEXTO,
            font=self.font_segmented,
        )
        self.segmented_acao.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        self.segmented_acao.set("Adicionar")

        self.entry_quantidade_pontos = ctk.CTkEntry(
            self.frame_acoes,
            placeholder_text="Quantidade de pontos",
            height=self.entry_height,
            corner_radius=10,
        )
        self.entry_quantidade_pontos.grid(row=2, column=0, sticky="ew", padx=14, pady=5)

        self.entry_valor_compra_acao = ctk.CTkEntry(
            self.frame_acoes,
            placeholder_text="Valor da compra (opcional para adicionar)",
            height=self.entry_height,
            corner_radius=10,
        )
        self.entry_valor_compra_acao.grid(row=3, column=0, sticky="ew", padx=14, pady=5)

        self.entry_motivo = ctk.CTkEntry(
            self.frame_acoes,
            placeholder_text="Motivo da movimentação",
            height=self.entry_height,
            corner_radius=10,
        )
        self.entry_motivo.grid(row=4, column=0, sticky="ew", padx=14, pady=5)

        self.text_observacao = ctk.CTkTextbox(
            self.frame_acoes,
            height=self.textbox_height,
            corner_radius=10,
            fg_color=COR_BOTAO,
            text_color=COR_TEXTO,
            border_width=0,
            font=self.font_valor,
        )
        self.text_observacao.grid(row=5, column=0, sticky="ew", padx=14, pady=5)
        self.text_observacao.insert("1.0", "Observação...")

        self.frame_botoes_acao = ctk.CTkFrame(self.frame_acoes, fg_color="transparent")
        self.frame_botoes_acao.grid(row=6, column=0, sticky="ew", padx=14, pady=(8, 6))
        self.frame_botoes_acao.grid_columnconfigure(0, weight=1)
        self.frame_botoes_acao.grid_columnconfigure(1, weight=1)

        self.btn_confirmar = ctk.CTkButton(
            self.frame_botoes_acao,
            text="Confirmar",
            height=self.button_height,
            fg_color=COR_BOTAO,
            hover_color=COR_HOVER,
            text_color=COR_TEXTO,
            font=self.font_botao,
            command=self.executar_acao_fidelidade,
        )
        self.btn_confirmar.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.btn_cancelar = ctk.CTkButton(
            self.frame_botoes_acao,
            text="Cancelar",
            height=self.button_height,
            fg_color=COR_BOTAO,
            hover_color=COR_HOVER,
            text_color=COR_TEXTO,
            font=self.font_botao,
            command=self.cancelar_acao,
        )
        self.btn_cancelar.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        self.var_feedback_acao = ctk.StringVar(value="Nenhuma ação executada.")
        self.label_feedback_acao = ctk.CTkLabel(
            self.frame_acoes,
            textvariable=self.var_feedback_acao,
            font=self.font_feedback,
            text_color=COR_TEXTO_SEC,
            wraplength=420,
            justify="left",
        )
        self.label_feedback_acao.grid(row=7, column=0, sticky="sw", padx=14, pady=(2, 12))

    # =========================================================
    # RESPONSIVIDADE
    # =========================================================
    def _ao_redimensionar(self, event):
        largura = max(event.width, 760)
        altura = max(event.height, 520)

        escala_w = largura / self.LARGURA_BASE
        escala_h = altura / self.ALTURA_BASE
        escala = min(escala_w, escala_h)

        # tamanhos de fonte limitados para não explodir nem ficar minúsculos
        titulo_size = self._clamp(int(22 * escala), 18, 26)
        subtitulo_size = self._clamp(int(11 * escala), 10, 13)
        card_titulo_size = self._clamp(int(16 * escala), 13, 18)
        label_size = self._clamp(int(11 * escala), 10, 12)
        valor_size = self._clamp(int(11 * escala), 10, 12)
        botao_size = self._clamp(int(11 * escala), 10, 12)
        feedback_size = self._clamp(int(11 * escala), 10, 12)
        destaque_size = self._clamp(int(24 * escala), 20, 28)
        segmented_size = self._clamp(int(10 * escala), 9, 11)

        self.font_titulo.configure(size=titulo_size)
        self.font_subtitulo.configure(size=subtitulo_size)
        self.font_card_titulo.configure(size=card_titulo_size)
        self.font_label.configure(size=label_size)
        self.font_valor.configure(size=valor_size)
        self.font_botao.configure(size=botao_size)
        self.font_feedback.configure(size=feedback_size)
        self.font_destaque.configure(size=destaque_size)
        self.font_segmented.configure(size=segmented_size)

        # alturas responsivas
        self.entry_height = self._clamp(int(38 * escala_h), 34, 44)
        self.button_height = self._clamp(int(36 * escala_h), 34, 42)
        self.segmented_height = self._clamp(int(34 * escala_h), 32, 40)
        self.textbox_height = self._clamp(int(84 * escala_h), 72, 105)

        widgets_altura = [
            self.entry_nome,
            self.entry_telefone,
            self.entry_codigo,
            self.entry_valor_compra,
            self.entry_quantidade_pontos,
            self.entry_valor_compra_acao,
            self.entry_motivo,
            self.combo_tipo_cliente,
        ]
        for widget in widgets_altura:
            widget.configure(height=self.entry_height)

        botoes = [
            self.btn_buscar,
            self.btn_limpar,
            self.btn_novo_cliente,
            self.btn_calcular,
            self.btn_confirmar,
            self.btn_cancelar,
        ]
        for botao in botoes:
            botao.configure(height=self.button_height)

        self.segmented_acao.configure(height=self.segmented_height)
        self.text_observacao.configure(height=self.textbox_height)

        # wrap adaptável ao tamanho do card
        largura_wrap = self._clamp(int((largura / 2) - 80), 280, 460)
        self.label_status_operacao.configure(wraplength=largura_wrap)
        self.label_regra_aplicada.configure(wraplength=largura_wrap)
        self.label_feedback_acao.configure(wraplength=largura_wrap)

    # =========================================================
    # DADOS DE EXEMPLO
    # =========================================================
    def _carregar_cliente_exemplo(self):
        self.cliente_selecionado = {
            "id": "CLI-001",
            "nome": "Maria Souza",
            "telefone": "(91) 99999-0000",
            "cadastro": "12/01/2026",
            "tipo_cliente": "Varejo",
            "pontos_atuais": 48,
            "total_acumulado": 132,
            "ultima_compra": "24/02/2026",
            "status": "Ativo",
        }

    # =========================================================
    # BUSCA / CLIENTE
    # =========================================================
    def buscar_cliente(self):
        if self.cliente_selecionado is None:
            self._carregar_cliente_exemplo()

        nome = self.entry_nome.get().strip()
        telefone = self.entry_telefone.get().strip()
        codigo = self.entry_codigo.get().strip()

        if nome:
            self.cliente_selecionado["nome"] = nome
        if telefone:
            self.cliente_selecionado["telefone"] = telefone
        if codigo:
            self.cliente_selecionado["id"] = codigo

        self.cliente_selecionado["status"] = "Ativo"

        self._atualizar_interface_cliente()
        self.label_status_operacao.configure(
            text="Cliente localizado com sucesso.",
            text_color=COR_SUCESSO,
        )

    def limpar_busca(self):
        self.entry_nome.delete(0, "end")
        self.entry_telefone.delete(0, "end")
        self.entry_codigo.delete(0, "end")

        self.label_status_operacao.configure(
            text="Campos de busca limpos.",
            text_color=COR_TEXTO_SEC,
        )

    def novo_cliente(self):
        self.entry_nome.delete(0, "end")
        self.entry_telefone.delete(0, "end")
        self.entry_codigo.delete(0, "end")

        self.cliente_selecionado = {
            "id": "NOVO",
            "nome": "Novo cliente",
            "telefone": "-",
            "cadastro": datetime.now().strftime("%d/%m/%Y"),
            "tipo_cliente": "Varejo",
            "pontos_atuais": 0,
            "total_acumulado": 0,
            "ultima_compra": "-",
            "status": "Ativo",
        }

        self._atualizar_interface_cliente()
        self.label_status_operacao.configure(
            text="Novo cliente preparado.",
            text_color=COR_SUCESSO,
        )

    # =========================================================
    # RN05
    # =========================================================
    def calcular_pontos_por_compra(self, tipo_cliente: str, valor_compra: float) -> int:
        if valor_compra <= 0:
            return 0

        tipo = tipo_cliente.strip().lower()

        if tipo == "varejo":
            return int(valor_compra // 5)

        if tipo == "revendedor":
            return int(valor_compra // 50) * 2

        return 0

    def calcular_nivel(self, pontos_atuais: int) -> str:
        if pontos_atuais >= 200:
            return "Ouro"
        if pontos_atuais >= 100:
            return "Prata"
        if pontos_atuais > 0:
            return "Bronze"
        return "-"

    def calcular_pontos_interface(self):
        tipo_cliente = self.combo_tipo_cliente.get()
        valor = self._obter_float(self.entry_valor_compra.get())
        pontos = self.calcular_pontos_por_compra(tipo_cliente, valor)

        self.var_pontos_calculados.set(str(pontos))

        if tipo_cliente == "Varejo":
            regra = (
                f"{fmt_dinheiro(valor)} em Varejo gera {pontos} ponto(s) "
                f"pela regra de 1 ponto a cada R$ 5,00."
            )
        else:
            regra = (
                f"{fmt_dinheiro(valor)} em Revendedor gera {pontos} ponto(s) "
                f"pela regra de 2 pontos a cada R$ 50,00."
            )

        self.var_regra_aplicada.set(regra)

        self.entry_quantidade_pontos.delete(0, "end")
        self.entry_quantidade_pontos.insert(0, str(pontos))

        self.var_feedback_acao.set("Pontos calculados e enviados para o campo de quantidade.")
        self.label_feedback_acao.configure(text_color=COR_SUCESSO)

    # =========================================================
    # AÇÕES DE FIDELIDADE
    # =========================================================
    def executar_acao_fidelidade(self):
        if not self.cliente_selecionado:
            self.var_feedback_acao.set("Selecione um cliente antes de executar uma ação.")
            self.label_feedback_acao.configure(text_color=COR_ERRO)
            return

        acao = self.segmented_acao.get()
        quantidade = self._obter_int(self.entry_quantidade_pontos.get())
        valor_compra = self._obter_float(self.entry_valor_compra_acao.get())
        motivo = self.entry_motivo.get().strip() or "Sem motivo informado"

        tipo_cliente = self.cliente_selecionado.get("tipo_cliente", "Varejo")
        pontos_atuais = int(self.cliente_selecionado.get("pontos_atuais", 0))
        total_acumulado = int(self.cliente_selecionado.get("total_acumulado", 0))

        if acao == "Adicionar" and valor_compra > 0:
            quantidade = self.calcular_pontos_por_compra(tipo_cliente, valor_compra)
            self.entry_quantidade_pontos.delete(0, "end")
            self.entry_quantidade_pontos.insert(0, str(quantidade))

        if acao in ("Adicionar", "Remover", "Resgatar", "Bônus") and quantidade <= 0:
            self.var_feedback_acao.set("Informe uma quantidade válida de pontos.")
            self.label_feedback_acao.configure(text_color=COR_ERRO)
            return

        if acao == "Adicionar":
            pontos_atuais += quantidade
            total_acumulado += quantidade
            if valor_compra > 0:
                self.cliente_selecionado["ultima_compra"] = datetime.now().strftime("%d/%m/%Y")
            mensagem = f"{quantidade} ponto(s) adicionados. Motivo: {motivo}"

        elif acao == "Remover":
            pontos_atuais = max(0, pontos_atuais - quantidade)
            mensagem = f"{quantidade} ponto(s) removidos. Motivo: {motivo}"

        elif acao == "Resgatar":
            if quantidade > pontos_atuais:
                self.var_feedback_acao.set("O cliente não possui pontos suficientes para resgate.")
                self.label_feedback_acao.configure(text_color=COR_ERRO)
                return
            pontos_atuais -= quantidade
            mensagem = f"{quantidade} ponto(s) resgatados. Motivo: {motivo}"

        elif acao == "Bônus":
            pontos_atuais += quantidade
            total_acumulado += quantidade
            mensagem = f"{quantidade} ponto(s) de bônus aplicados. Motivo: {motivo}"

        elif acao == "Zerar":
            quantidade_zerada = pontos_atuais
            pontos_atuais = 0
            mensagem = f"Pontos zerados com sucesso ({quantidade_zerada} ponto(s)). Motivo: {motivo}"

        else:
            self.var_feedback_acao.set("Ação inválida.")
            self.label_feedback_acao.configure(text_color=COR_ERRO)
            return

        self.cliente_selecionado["pontos_atuais"] = pontos_atuais
        self.cliente_selecionado["total_acumulado"] = total_acumulado
        self.cliente_selecionado["status"] = "Ativo" if pontos_atuais > 0 else "Inativo"

        self._atualizar_interface_cliente()

        self.var_feedback_acao.set(mensagem)
        self.label_feedback_acao.configure(text_color=COR_SUCESSO)

        self.label_status_operacao.configure(
            text="Movimentação aplicada no cliente atual.",
            text_color=COR_SUCESSO,
        )

    def cancelar_acao(self):
        self.segmented_acao.set("Adicionar")
        self.entry_quantidade_pontos.delete(0, "end")
        self.entry_valor_compra_acao.delete(0, "end")
        self.entry_motivo.delete(0, "end")
        self.text_observacao.delete("1.0", "end")
        self.text_observacao.insert("1.0", "Observação...")

        self.var_feedback_acao.set("Campos da ação foram limpos.")
        self.label_feedback_acao.configure(text_color=COR_TEXTO_SEC)

    # =========================================================
    # ATUALIZAÇÃO DE INTERFACE
    # =========================================================
    def _atualizar_interface_cliente(self):
        if not self.cliente_selecionado:
            return

        pontos = int(self.cliente_selecionado.get("pontos_atuais", 0))
        status = self.cliente_selecionado.get("status", "Inativo")

        self.var_nome.set(self.cliente_selecionado.get("nome", "-"))
        self.var_telefone.set(self.cliente_selecionado.get("telefone", "-"))
        self.var_cadastro.set(self.cliente_selecionado.get("cadastro", "-"))
        self.var_tipo_cliente.set(self.cliente_selecionado.get("tipo_cliente", "-"))
        self.var_pontos_atuais.set(str(pontos))
        self.var_total_acumulado.set(str(self.cliente_selecionado.get("total_acumulado", 0)))
        self.var_ultima_compra.set(self.cliente_selecionado.get("ultima_compra", "-"))
        self.var_status.set(status)
        self.var_nivel.set(self.calcular_nivel(pontos))

        # Destaques visuais
        self._aplicar_destaques_resumo()

    def _aplicar_destaques_resumo(self):
        pontos = int(self.var_pontos_atuais.get())
        status = self.var_status.get()
        nivel = self.var_nivel.get()

        # Reseta cor padrão de todos os valores
        for lbl in self._resumo_valores:
            lbl.configure(text_color=COR_TEXTO_SEC)

        # Índices fixos dos campos no array:
        # 0 nome, 1 telefone, 2 cadastro, 3 tipo, 4 pontos, 5 total, 6 última compra, 7 status, 8 nível
        self._resumo_valores[4].configure(text_color=COR_SUCESSO if pontos > 0 else COR_TEXTO)
        self._resumo_valores[7].configure(text_color=COR_SUCESSO if status == "Ativo" else COR_ERRO)

        if nivel == "Ouro":
            self._resumo_valores[8].configure(text_color="#B8860B")
        elif nivel == "Prata":
            self._resumo_valores[8].configure(text_color="#7A7A7A")
        elif nivel == "Bronze":
            self._resumo_valores[8].configure(text_color="#A56A43")
        else:
            self._resumo_valores[8].configure(text_color=COR_TEXTO_SEC)

    # =========================================================
    # HELPERS
    # =========================================================
    def _obter_float(self, valor_texto: str) -> float:
        try:
            texto = valor_texto.strip().replace("R$", "").replace(".", "").replace(",", ".")
            if not texto:
                return 0.0
            return float(texto)
        except ValueError:
            return 0.0

    def _obter_int(self, valor_texto: str) -> int:
        try:
            if not valor_texto.strip():
                return 0
            return int(valor_texto)
        except ValueError:
            return 0

    @staticmethod
    def _clamp(valor: int, minimo: int, maximo: int) -> int:
        return max(minimo, min(valor, maximo))