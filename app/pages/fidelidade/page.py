# app/pages/fidelidade/page.py

import customtkinter as ctk

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
        2) Cálculo automático de pontos
    - Linha inferior:
        3) Buscar cliente
        4) Ações de fidelidade
    """

    LARGURA_BASE = 1100
    ALTURA_BASE = 680

    def __init__(self, master, sistema):
        super().__init__(master, fg_color=COR_FUNDO)

        self.sistema = sistema
        self.cliente_selecionado = None

        # =====================================================
        # Fontes (mais compactas para caber melhor em 1100x680)
        # =====================================================
        self.font_titulo = ctk.CTkFont(family=FONTE, size=20, weight="bold")
        self.font_card_titulo = ctk.CTkFont(family=FONTE, size=14, weight="bold")
        self.font_label = ctk.CTkFont(family=FONTE, size=10, weight="bold")
        self.font_valor = ctk.CTkFont(family=FONTE, size=10)
        self.font_botao = ctk.CTkFont(family=FONTE, size=10, weight="bold")
        self.font_feedback = ctk.CTkFont(family=FONTE, size=10)
        self.font_destaque = ctk.CTkFont(family=FONTE, size=20, weight="bold")
        self.font_segmented = ctk.CTkFont(family=FONTE, size=9, weight="bold")

        # alturas dinâmicas (mais compactas)
        self.entry_height = 34
        self.button_height = 34
        self.segmented_height = 30
        self.textbox_height = 68

        self._criar_layout_principal()
        self._criar_frame_resumo_cliente()
        self._criar_frame_calculo_automatico()
        self._criar_frame_busca_cliente()
        self._criar_frame_acoes_fidelidade()

        self._limpar_interface_cliente()

        # Responsividade real conforme a área renderizada
        self.bind("<Configure>", self._ao_redimensionar)

    # =========================================================
    # LAYOUT PRINCIPAL
    # =========================================================
    def _criar_layout_principal(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.frame_topo = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_topo.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 6))
        self.frame_topo.grid_columnconfigure(0, weight=1)

        self.label_titulo = ctk.CTkLabel(
            self.frame_topo,
            text="Fidelidade",
            font=self.font_titulo,
            text_color=COR_TEXTO,
        )
        self.label_titulo.grid(row=0, column=0, sticky="w")

        self.frame_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_grid.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 14))

        self.frame_grid.grid_columnconfigure(0, weight=1, uniform="col")
        self.frame_grid.grid_columnconfigure(1, weight=1, uniform="col")

        # Linhas iguais para dar mais espaço ao card de ações
        self.frame_grid.grid_rowconfigure(0, weight=1, uniform="row")
        self.frame_grid.grid_rowconfigure(1, weight=1, uniform="row")

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

        self.label_resumo_titulo = ctk.CTkLabel(
            self.frame_resumo,
            text="Resumo do cliente",
            font=self.font_card_titulo,
            text_color=COR_TEXTO,
        )
        self.label_resumo_titulo.grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(10, 6))

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
            lbl_rotulo.grid(row=i, column=0, sticky="w", padx=(14, 8), pady=2)

            lbl_valor = ctk.CTkLabel(
                self.frame_resumo,
                textvariable=variavel,
                font=self.font_valor,
                text_color=COR_TEXTO_SEC,
                anchor="w",
            )
            lbl_valor.grid(row=i, column=1, sticky="w", padx=(0, 14), pady=2)

            self._resumo_rotulos.append(lbl_rotulo)
            self._resumo_valores.append(lbl_valor)

        self.label_status_operacao = ctk.CTkLabel(
            self.frame_resumo,
            text="Selecione ou busque um cliente para começar.",
            font=self.font_feedback,
            text_color=COR_TEXTO_SEC,
            wraplength=360,
            justify="left",
        )
        self.label_status_operacao.grid(
            row=10,
            column=0,
            columnspan=2,
            sticky="w",
            padx=14,
            pady=(4, 8),
        )

    # =========================================================
    # FRAME 2 - CÁLCULO AUTOMÁTICO
    # =========================================================
    def _criar_frame_calculo_automatico(self):
        self.frame_calculo = ctk.CTkFrame(
            self.frame_grid,
            fg_color=COR_PAINEL,
            corner_radius=14,
        )
        self.frame_calculo.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))
        self.frame_calculo.grid_columnconfigure(0, weight=1)

        self.label_calculo_titulo = ctk.CTkLabel(
            self.frame_calculo,
            text="Cálculo automático de pontos",
            font=self.font_card_titulo,
            text_color=COR_TEXTO,
        )
        self.label_calculo_titulo.grid(row=0, column=0, sticky="w", padx=14, pady=(10, 6))

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
        self.combo_tipo_cliente.grid(row=1, column=0, sticky="ew", padx=14, pady=4)
        self.combo_tipo_cliente.set("Varejo")

        self.entry_valor_compra = ctk.CTkEntry(
            self.frame_calculo,
            placeholder_text="Valor da compra (ex.: 50,00)",
            height=self.entry_height,
            corner_radius=10,
        )
        self.entry_valor_compra.grid(row=2, column=0, sticky="ew", padx=14, pady=4)

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
        self.btn_calcular.grid(row=3, column=0, sticky="ew", padx=14, pady=(6, 4))

        self.var_pontos_calculados = ctk.StringVar(value="0")
        self.var_regra_aplicada = ctk.StringVar(value="Aguardando cálculo.")

        self.label_pontos_calculados = ctk.CTkLabel(
            self.frame_calculo,
            text="Pontos calculados",
            font=self.font_label,
            text_color=COR_TEXTO,
        )
        self.label_pontos_calculados.grid(row=4, column=0, sticky="w", padx=14, pady=(4, 0))

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
            wraplength=360,
            justify="left",
        )
        self.label_regra_aplicada.grid(row=6, column=0, sticky="w", padx=14, pady=(2, 8))

    # =========================================================
    # FRAME 3 - BUSCAR CLIENTE
    # =========================================================
    def _criar_frame_busca_cliente(self):
        self.frame_busca = ctk.CTkFrame(
            self.frame_grid,
            fg_color=COR_PAINEL,
            corner_radius=14,
        )
        self.frame_busca.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(8, 0))
        self.frame_busca.grid_columnconfigure(0, weight=1)

        self.label_busca_titulo = ctk.CTkLabel(
            self.frame_busca,
            text="Buscar cliente",
            font=self.font_card_titulo,
            text_color=COR_TEXTO,
        )
        self.label_busca_titulo.grid(row=0, column=0, sticky="w", padx=14, pady=(10, 6))

        self.entry_nome = ctk.CTkEntry(
            self.frame_busca,
            placeholder_text="Nome",
            height=self.entry_height,
            corner_radius=10,
        )
        self.entry_nome.grid(row=1, column=0, sticky="ew", padx=14, pady=4)

        self.entry_telefone = ctk.CTkEntry(
            self.frame_busca,
            placeholder_text="Telefone",
            height=self.entry_height,
            corner_radius=10,
        )
        self.entry_telefone.grid(row=2, column=0, sticky="ew", padx=14, pady=4)

        self.entry_codigo = ctk.CTkEntry(
            self.frame_busca,
            placeholder_text="Código / ID",
            height=self.entry_height,
            corner_radius=10,
        )
        self.entry_codigo.grid(row=3, column=0, sticky="ew", padx=14, pady=4)

        self.frame_botoes_busca = ctk.CTkFrame(self.frame_busca, fg_color="transparent")
        self.frame_botoes_busca.grid(row=4, column=0, sticky="ew", padx=14, pady=(6, 8))
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
        self.btn_buscar.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=(0, 4))

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
        self.btn_limpar.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=(0, 4))

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

        # Faz o textbox crescer primeiro, evitando cortar os botões
        self.frame_acoes.grid_rowconfigure(5, weight=1)

        self.label_acoes_titulo = ctk.CTkLabel(
            self.frame_acoes,
            text="Ações de fidelidade",
            font=self.font_card_titulo,
            text_color=COR_TEXTO,
        )
        self.label_acoes_titulo.grid(row=0, column=0, sticky="w", padx=14, pady=(10, 6))

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
        self.segmented_acao.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 6))
        self.segmented_acao.set("Adicionar")

        self.entry_quantidade_pontos = ctk.CTkEntry(
            self.frame_acoes,
            placeholder_text="Quantidade de pontos",
            height=self.entry_height,
            corner_radius=10,
        )
        self.entry_quantidade_pontos.grid(row=2, column=0, sticky="ew", padx=14, pady=4)

        self.entry_valor_compra_acao = ctk.CTkEntry(
            self.frame_acoes,
            placeholder_text="Valor da compra (apoio manual)",
            height=self.entry_height,
            corner_radius=10,
        )
        self.entry_valor_compra_acao.grid(row=3, column=0, sticky="ew", padx=14, pady=4)

        self.entry_motivo = ctk.CTkEntry(
            self.frame_acoes,
            placeholder_text="Motivo da movimentação",
            height=self.entry_height,
            corner_radius=10,
        )
        self.entry_motivo.grid(row=4, column=0, sticky="ew", padx=14, pady=4)

        self.text_observacao = ctk.CTkTextbox(
            self.frame_acoes,
            height=self.textbox_height,
            corner_radius=10,
            fg_color=COR_BOTAO,
            text_color=COR_TEXTO,
            border_width=0,
            font=self.font_valor,
        )
        self.text_observacao.grid(row=5, column=0, sticky="nsew", padx=14, pady=4)
        self.text_observacao.insert("1.0", "Observação...")

        self.frame_botoes_acao = ctk.CTkFrame(self.frame_acoes, fg_color="transparent")
        self.frame_botoes_acao.grid(row=6, column=0, sticky="ew", padx=14, pady=(6, 4))
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
        self.btn_confirmar.grid(row=0, column=0, sticky="ew", padx=(0, 4))

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
        self.btn_cancelar.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.var_feedback_acao = ctk.StringVar(value="Nenhuma ação executada.")
        self.label_feedback_acao = ctk.CTkLabel(
            self.frame_acoes,
            textvariable=self.var_feedback_acao,
            font=self.font_feedback,
            text_color=COR_TEXTO_SEC,
            wraplength=360,
            justify="left",
        )
        self.label_feedback_acao.grid(row=7, column=0, sticky="w", padx=14, pady=(2, 8))

    # =========================================================
    # RESPONSIVIDADE
    # =========================================================
    def _ao_redimensionar(self, event):
        largura = max(event.width, 760)
        altura = max(event.height, 520)

        escala_w = largura / self.LARGURA_BASE
        escala_h = altura / self.ALTURA_BASE
        escala = min(escala_w, escala_h)

        titulo_size = self._clamp(int(20 * escala), 17, 24)
        card_titulo_size = self._clamp(int(14 * escala), 12, 16)
        label_size = self._clamp(int(10 * escala), 9, 11)
        valor_size = self._clamp(int(10 * escala), 9, 11)
        botao_size = self._clamp(int(10 * escala), 9, 11)
        feedback_size = self._clamp(int(10 * escala), 9, 11)
        destaque_size = self._clamp(int(20 * escala), 18, 24)
        segmented_size = self._clamp(int(9 * escala), 8, 10)

        self.font_titulo.configure(size=titulo_size)
        self.font_card_titulo.configure(size=card_titulo_size)
        self.font_label.configure(size=label_size)
        self.font_valor.configure(size=valor_size)
        self.font_botao.configure(size=botao_size)
        self.font_feedback.configure(size=feedback_size)
        self.font_destaque.configure(size=destaque_size)
        self.font_segmented.configure(size=segmented_size)

        self.entry_height = self._clamp(int(34 * escala_h), 32, 40)
        self.button_height = self._clamp(int(34 * escala_h), 32, 38)
        self.segmented_height = self._clamp(int(30 * escala_h), 28, 34)
        self.textbox_height = self._clamp(int(68 * escala_h), 58, 84)

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

        largura_wrap = self._clamp(int((largura / 2) - 100), 240, 380)
        self.label_status_operacao.configure(wraplength=largura_wrap)
        self.label_regra_aplicada.configure(wraplength=largura_wrap)
        self.label_feedback_acao.configure(wraplength=largura_wrap)

    # =========================================================
    # CLIENTE / BUSCA REAL
    # =========================================================
    def buscar_cliente(self):
        nome = self.entry_nome.get().strip()
        telefone = self.entry_telefone.get().strip()
        codigo = self.entry_codigo.get().strip()

        termo = nome or telefone or codigo

        if not termo and self.cliente_selecionado:
            termo = str(self.cliente_selecionado.get("id", "")).strip()

        if not termo:
            self.label_status_operacao.configure(
                text="Informe nome, telefone ou código para buscar.",
                text_color=COR_ERRO,
            )
            return

        if not self.sistema or not hasattr(self.sistema, "listar_clientes"):
            self.label_status_operacao.configure(
                text="Sistema de clientes não disponível.",
                text_color=COR_ERRO,
            )
            return

        resultados = self.sistema.listar_clientes(termo=termo)

        if not resultados and codigo and hasattr(self.sistema, "obter_cliente"):
            try:
                cliente_id = int(codigo)
                cliente = self.sistema.obter_cliente(cliente_id)
                if cliente:
                    resultados = [cliente]
            except Exception:
                pass

        if not resultados and self.cliente_selecionado and hasattr(self.sistema, "obter_cliente"):
            try:
                cliente = self.sistema.obter_cliente(int(self.cliente_selecionado["id"]))
                if cliente:
                    resultados = [cliente]
            except Exception:
                pass

        if not resultados:
            self.label_status_operacao.configure(
                text="Cliente não encontrado.",
                text_color=COR_ERRO,
            )
            return

        c = resultados[0]
        self.cliente_selecionado = self._mapear_cliente_para_interface(c)

        try:
            tipo = self.cliente_selecionado.get("tipo_cliente", "Varejo")
            if tipo in ("Varejo", "Revendedor"):
                self.combo_tipo_cliente.set(tipo)
        except Exception:
            pass

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

        self.cliente_selecionado = None
        self._limpar_interface_cliente()

        self.label_status_operacao.configure(
            text="Cadastre o cliente na tela de Clientes para usar a fidelidade.",
            text_color=COR_TEXTO_SEC,
        )

    def _mapear_cliente_para_interface(self, cliente):
        cadastro = self._formatar_data_cliente(cliente.get("cadastro"))
        ultima_compra = self._formatar_data_cliente(cliente.get("ultima_compra"))

        return {
            "id": cliente.get("id"),
            "nome": cliente.get("nome", "-"),
            "telefone": cliente.get("telefone", "-"),
            "cadastro": cadastro,
            "tipo_cliente": cliente.get("tipo_cliente", "Varejo"),
            "pontos_atuais": int(cliente.get("pontos_atuais", 0)),
            "total_acumulado": int(cliente.get("total_acumulado", 0)),
            "ultima_compra": ultima_compra,
            "status": cliente.get("status", "Inativo"),
        }

    def _formatar_data_cliente(self, valor):
        if not valor:
            return "-"

        if hasattr(valor, "strftime"):
            try:
                return valor.strftime("%d/%m/%Y")
            except Exception:
                pass

        return str(valor)

    # =========================================================
    # RN05 / CÁLCULO DE PONTOS
    # =========================================================
    def calcular_pontos_por_compra(self, tipo_cliente: str, valor_compra: float) -> int:
        if valor_compra <= 0:
            return 0

        if self.sistema and hasattr(self.sistema, "calcular_pontos_rn05"):
            try:
                return int(self.sistema.calcular_pontos_rn05(tipo_cliente, valor_compra))
            except Exception:
                pass

        tipo = str(tipo_cliente).strip().lower()

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
    # AÇÕES DE FIDELIDADE (USANDO O SERVIÇO)
    # =========================================================
    def executar_acao_fidelidade(self):
        if not self.cliente_selecionado:
            self.var_feedback_acao.set("Selecione um cliente antes de executar uma ação.")
            self.label_feedback_acao.configure(text_color=COR_ERRO)
            return

        if not self.sistema or not hasattr(self.sistema, "movimentar_fidelidade"):
            self.var_feedback_acao.set("Sistema de fidelidade não disponível.")
            self.label_feedback_acao.configure(text_color=COR_ERRO)
            return

        acao = self.segmented_acao.get().upper()
        quantidade = self._obter_int(self.entry_quantidade_pontos.get())
        motivo = self.entry_motivo.get().strip() or "Sem motivo"

        mapa = {
            "ADICIONAR": "ADICIONAR",
            "REMOVER": "REMOVER",
            "RESGATAR": "RESGATAR",
            "BÔNUS": "BONUS",
            "BONUS": "BONUS",
            "ZERAR": "ZERAR",
        }

        acao_real = mapa.get(acao, None)
        if not acao_real:
            self.var_feedback_acao.set("Ação inválida.")
            self.label_feedback_acao.configure(text_color=COR_ERRO)
            return

        if acao_real != "ZERAR" and quantidade <= 0:
            self.var_feedback_acao.set("Informe uma quantidade válida.")
            self.label_feedback_acao.configure(text_color=COR_ERRO)
            return

        try:
            self.sistema.movimentar_fidelidade(
                cliente_id=self.cliente_selecionado["id"],
                acao=acao_real,
                pontos=quantidade,
                motivo=motivo,
            )
        except Exception as e:
            self.var_feedback_acao.set(f"Erro ao aplicar movimentação: {e}")
            self.label_feedback_acao.configure(text_color=COR_ERRO)
            return

        self.buscar_cliente()

        self.var_feedback_acao.set("Movimentação aplicada com sucesso.")
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
    def _limpar_interface_cliente(self):
        self.var_nome.set("-")
        self.var_telefone.set("-")
        self.var_cadastro.set("-")
        self.var_tipo_cliente.set("-")
        self.var_pontos_atuais.set("0")
        self.var_total_acumulado.set("0")
        self.var_ultima_compra.set("-")
        self.var_status.set("Inativo")
        self.var_nivel.set("-")
        self._aplicar_destaques_resumo()

    def _atualizar_interface_cliente(self):
        if not self.cliente_selecionado:
            self._limpar_interface_cliente()
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

        tipo = self.cliente_selecionado.get("tipo_cliente", "Varejo")
        if tipo in ("Varejo", "Revendedor"):
            try:
                self.combo_tipo_cliente.set(tipo)
            except Exception:
                pass

        self._aplicar_destaques_resumo()

    def _aplicar_destaques_resumo(self):
        pontos = int(self.var_pontos_atuais.get())
        status = self.var_status.get()
        nivel = self.var_nivel.get()

        for lbl in self._resumo_valores:
            lbl.configure(text_color=COR_TEXTO_SEC)

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
            texto = str(valor_texto).strip().replace("R$", "").replace(" ", "")
            if not texto:
                return 0.0

            if "," in texto and "." in texto:
                texto = texto.replace(".", "").replace(",", ".")
            else:
                texto = texto.replace(",", ".")

            return float(texto)
        except ValueError:
            return 0.0

    def _obter_int(self, valor_texto: str) -> int:
        try:
            texto = str(valor_texto).strip()
            if not texto:
                return 0
            return int(texto)
        except ValueError:
            return 0

    @staticmethod
    def _clamp(valor: int, minimo: int, maximo: int) -> int:
        return max(minimo, min(valor, maximo))