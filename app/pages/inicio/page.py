import calendar
import json
import threading
from datetime import date, datetime, timedelta
from urllib.error import URLError
from urllib.request import urlopen
from zoneinfo import ZoneInfo

import customtkinter as ctk

from app.config import theme


class PaginaInicio(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        # =========================================================
        # Layout da página
        # - Coluna esquerda fixa (relógio + clima)
        # - Coluna direita responsiva (calendário)
        # =========================================================
        self.grid_columnconfigure(0, weight=0)   # fixa
        self.grid_columnconfigure(1, weight=1)   # responsiva
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # Estado geral
        self.tz_belem = ZoneInfo("America/Belem")
        hoje = date.today()

        self.cal_ano = hoje.year
        self.cal_mes = hoje.month
        self.data_selecionada = hoje
        self.servicos = self._mock_servicos()

        # Tooltip / hover
        self.tooltip = None
        self.tooltip_pinned = False
        self._hover_job = None
        self._hover_widget = None
        self._hover_data = None

        # Jobs agendados (after)
        self._job_relogio = None
        self._job_clima = None
        self._job_resize_inicio = None
        self._job_resize_calendario = None

        # Cache de dimensões
        self._prev_dimensions = {
            "inicio": (0, 0),
            "calendario": (0, 0),
        }

        # =========================================================
        # Fonts reutilizáveis
        # =========================================================
        # Boas-vindas
        self.font_titulo_inicio = ctk.CTkFont(family=theme.FONTE, size=34, weight="bold")
        self.font_subtitulo_inicio = ctk.CTkFont(family=theme.FONTE, size=14, weight="bold")

        # Relógio / Clima (fixos)
        self.font_titulo_relogio = ctk.CTkFont(family=theme.FONTE, size=16, weight="bold")
        self.font_hora = ctk.CTkFont(family=theme.FONTE, size=38, weight="bold")
        self.font_data = ctk.CTkFont(family=theme.FONTE, size=13)

        self.font_titulo_temp = ctk.CTkFont(family=theme.FONTE, size=16, weight="bold")
        self.font_temp = ctk.CTkFont(family=theme.FONTE, size=38, weight="bold")
        self.font_clima = ctk.CTkFont(family=theme.FONTE, size=13, weight="bold")
        self.font_temp_atualizada = ctk.CTkFont(family=theme.FONTE, size=11)

        # Calendário (responsivas)
        self.font_titulo_calendario = ctk.CTkFont(family=theme.FONTE, size=18, weight="bold")
        self.font_mes_ano = ctk.CTkFont(family=theme.FONTE, size=14, weight="bold")
        self.font_dia_semana = ctk.CTkFont(family=theme.FONTE, size=11, weight="bold")
        self.font_dia_numero = ctk.CTkFont(family=theme.FONTE, size=11)

        # UI
        self._criar_card_boas_vindas()
        self._criar_coluna_status()
        self._criar_card_calendario_servicos()

        # Inicializações
        self._render_calendario()
        self._atualizar_relogio()
        self._atualizar_temperatura()

        # Bind para fechar tooltip clicando fora
        self.after(200, self._registrar_bind_root_click)

    # =========================================================
    # UI
    # =========================================================
    def _criar_card_boas_vindas(self):
        self.card_boas_vindas = ctk.CTkFrame(
            self, fg_color=theme.COR_HOVER, corner_radius=16, height=220
        )
        self.card_boas_vindas.grid(
            row=0, column=0, columnspan=2, padx=30, pady=(20, 14), sticky="ew"
        )
        self.card_boas_vindas.grid_columnconfigure(0, weight=1)
        self.card_boas_vindas.grid_rowconfigure(0, weight=1)
        self.card_boas_vindas.grid_rowconfigure(3, weight=1)
        self.card_boas_vindas.grid_propagate(False)

        self.lbl_titulo_inicio = ctk.CTkLabel(
            self.card_boas_vindas,
            text="Bem vindo ao Sistema Geladoce",
            font=self.font_titulo_inicio,
            text_color=theme.COR_TEXTO_SEC,
            anchor="center"
        )
        self.lbl_titulo_inicio.grid(row=1, column=0, padx=22, sticky="")

        self.lbl_subtitulo_inicio = ctk.CTkLabel(
            self.card_boas_vindas,
            text="Tudo o que você precisa para gerenciar a Geladoce, em um só lugar.",
            font=self.font_subtitulo_inicio,
            text_color=theme.COR_TEXTO_SEC,
            anchor="center",
            justify="center",
            wraplength=860,
        )
        self.lbl_subtitulo_inicio.grid(row=2, column=0, padx=22, pady=(6, 0), sticky="")

        # Responsivo só aqui
        self.card_boas_vindas.bind("<Configure>", self._on_resize_boas_vindas)

    def _criar_coluna_status(self):
        # IMPORTANTE: NÃO usar grid_propagate(False) aqui sem controlar altura total.
        # Mantemos largura fixa, mas deixamos a altura ser definida pelo conteúdo.
        self.coluna_status = ctk.CTkFrame(self, fg_color="transparent", width=360)
        self.coluna_status.grid(row=1, column=0, padx=(30, 12), pady=(0, 24), sticky="nw")
        self.coluna_status.grid_columnconfigure(0, weight=1)

        # Cards fixos (sem responsividade)
        self._criar_card_relogio(self.coluna_status)
        self._criar_card_temperatura(self.coluna_status)

    def _criar_card_relogio(self, master):
        self.card_relogio = ctk.CTkFrame(
            master,
            fg_color=theme.COR_PAINEL,
            corner_radius=14,
            width=360,
            height=175,
        )
        self.card_relogio.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        self.card_relogio.grid_propagate(False)
        self.card_relogio.grid_columnconfigure(0, weight=1)
        self.card_relogio.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self.card_relogio,
            text="Relógio • Belém/PA",
            font=self.font_titulo_relogio,
            text_color=theme.COR_TEXTO,
            anchor="center",
        ).grid(row=0, column=0, padx=16, pady=(14, 6), sticky="")

        self.lbl_hora = ctk.CTkLabel(
            self.card_relogio,
            text="--:--:--",
            font=self.font_hora,
            text_color=theme.COR_TEXTO,
            anchor="center",
            justify="center",
        )
        self.lbl_hora.grid(row=1, column=0, padx=16, pady=(0, 4), sticky="")

        self.lbl_data = ctk.CTkLabel(
            self.card_relogio,
            text="",
            font=self.font_data,
            text_color=theme.COR_TEXTO_SEC,
            anchor="center",
            justify="center",
        )
        self.lbl_data.grid(row=2, column=0, padx=16, pady=(0, 14), sticky="")

    def _criar_card_temperatura(self, master):
        self.card_temperatura = ctk.CTkFrame(
            master,
            fg_color=theme.COR_HOVER,
            corner_radius=14,
            width=360,
            height=190,
        )
        self.card_temperatura.grid(row=1, column=0, pady=(10, 0), sticky="ew")
        self.card_temperatura.grid_propagate(False)
        self.card_temperatura.grid_columnconfigure(0, weight=1)
        self.card_temperatura.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self.card_temperatura,
            text="Temperatura local",
            font=self.font_titulo_temp,
            text_color="#FFFFFF",
            anchor="center",
        ).grid(row=0, column=0, padx=16, pady=(14, 6), sticky="")

        self.lbl_temperatura = ctk.CTkLabel(
            self.card_temperatura,
            text="-- °C",
            font=self.font_temp,
            text_color="#FFFFFF",
            anchor="center",
            justify="center",
        )
        self.lbl_temperatura.grid(row=1, column=0, padx=16, pady=(0, 2), sticky="")

        self.lbl_clima = ctk.CTkLabel(
            self.card_temperatura,
            text="Buscando clima...",
            font=self.font_clima,
            text_color=theme.COR_TEXTO_SEC,
            anchor="center",
            justify="center",
            wraplength=320,  # fixo
        )
        self.lbl_clima.grid(row=2, column=0, padx=16, pady=(0, 2), sticky="")

        self.lbl_temp_atualizada = ctk.CTkLabel(
            self.card_temperatura,
            text="",
            font=self.font_temp_atualizada,
            text_color=theme.COR_TEXTO_SEC,
            anchor="center",
        )
        self.lbl_temp_atualizada.grid(row=3, column=0, padx=16, pady=(0, 14), sticky="")

    def _criar_card_calendario_servicos(self):
        self.card_calendario = ctk.CTkFrame(self, fg_color=theme.COR_PAINEL, corner_radius=14)
        self.card_calendario.grid(row=1, column=1, padx=(12, 30), pady=(0, 24), sticky="nsew")
        self.card_calendario.grid_columnconfigure(0, weight=1)
        self.card_calendario.grid_rowconfigure(2, weight=1)

        self.lbl_titulo_calendario = ctk.CTkLabel(
            self.card_calendario,
            text="Calendário de serviços",
            font=self.font_titulo_calendario,
            text_color=theme.COR_TEXTO,
        )
        self.lbl_titulo_calendario.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")

        header = ctk.CTkFrame(self.card_calendario, fg_color="transparent")
        header.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            header,
            text="<",
            width=34,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._mes_anterior,
        ).grid(row=0, column=0, padx=(0, 8))

        self.lbl_mes_ano = ctk.CTkLabel(
            header,
            text="",
            font=self.font_mes_ano,
            text_color=theme.COR_TEXTO,
        )
        self.lbl_mes_ano.grid(row=0, column=1, sticky="w")

        ctk.CTkButton(
            header,
            text=">",
            width=34,
            fg_color=theme.COR_BOTAO,
            hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
            command=self._mes_proximo,
        ).grid(row=0, column=2)

        self.frame_dias = ctk.CTkFrame(self.card_calendario, fg_color=theme.COR_BOTAO, corner_radius=12)
        self.frame_dias.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="nsew")

        for c in range(7):
            self.frame_dias.grid_columnconfigure(c, weight=1, uniform="cal_cols")
        for r in range(7):
            self.frame_dias.grid_rowconfigure(r, weight=1, uniform="cal_rows")

        # Responsivo só no calendário
        self.card_calendario.bind("<Configure>", self._on_resize_calendario)

    # =========================================================
    # Responsividade (somente boas-vindas e calendário)
    # =========================================================
    def _on_resize_boas_vindas(self, event):
        if self._job_resize_inicio is not None:
            try:
                self.after_cancel(self._job_resize_inicio)
            except Exception:
                pass
        self._job_resize_inicio = self.after(50, self._aplicar_resize_boas_vindas)

    def _aplicar_resize_boas_vindas(self):
        self._job_resize_inicio = None
        if not self.winfo_exists():
            return

        try:
            largura = self.card_boas_vindas.winfo_width()
            altura = self.card_boas_vindas.winfo_height()
            if self._prev_dimensions["inicio"] == (largura, altura):
                return
            self._prev_dimensions["inicio"] = (largura, altura)
        except Exception:
            return

        largura = max(300, largura)
        altura = max(120, altura)

        titulo_size = int(min(max(largura * 0.04, 22), 42))
        subtitulo_size = int(min(max(largura * 0.018, 12), 18))

        if altura < 150:
            titulo_size = max(20, titulo_size - 6)
            subtitulo_size = max(10, subtitulo_size - 2)
        elif altura < 180:
            titulo_size = max(22, titulo_size - 3)
            subtitulo_size = max(11, subtitulo_size - 1)

        self.font_titulo_inicio.configure(size=titulo_size)
        self.font_subtitulo_inicio.configure(size=subtitulo_size)

        padding = max(15, int(largura * 0.02))
        self.lbl_titulo_inicio.grid_configure(padx=padding)
        self.lbl_subtitulo_inicio.grid_configure(padx=padding)

        wrap = max(280, largura - 80)
        self.lbl_subtitulo_inicio.configure(wraplength=wrap)

    def _on_resize_calendario(self, event):
        if self._job_resize_calendario is not None:
            try:
                self.after_cancel(self._job_resize_calendario)
            except Exception:
                pass
        self._job_resize_calendario = self.after(50, self._aplicar_resize_calendario)

    def _aplicar_resize_calendario(self):
        self._job_resize_calendario = None
        if not self.winfo_exists():
            return

        try:
            largura = self.card_calendario.winfo_width()
            altura = self.card_calendario.winfo_height()
            if self._prev_dimensions["calendario"] == (largura, altura):
                return
            self._prev_dimensions["calendario"] = (largura, altura)
        except Exception:
            return

        largura = max(280, largura)

        titulo_cal_size = int(min(max(largura * 0.040, 15), 22))
        mes_ano_size = int(min(max(largura * 0.028, 12), 16))
        dia_num_size = int(min(max(largura * 0.020, 10), 13))
        dia_semana_size = max(9, dia_num_size - 1)

        self.font_titulo_calendario.configure(size=titulo_cal_size)
        self.font_mes_ano.configure(size=mes_ano_size)
        self.font_dia_numero.configure(size=dia_num_size)
        self.font_dia_semana.configure(size=dia_semana_size)

        self._atualizar_calendario_estilo()

    def _atualizar_calendario_estilo(self):
        try:
            dia_btn_h = max(32, min(42, self.font_dia_numero.cget("size") * 3))
        except Exception:
            dia_btn_h = 34

        for widget in self.frame_dias.winfo_children():
            try:
                if isinstance(widget, ctk.CTkButton):
                    widget.configure(font=self.font_dia_numero, height=dia_btn_h)
                elif isinstance(widget, ctk.CTkLabel):
                    txt = widget.cget("text")
                    if txt in {"Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"}:
                        widget.configure(font=self.font_dia_semana)
                    else:
                        widget.configure(font=self.font_dia_numero)
            except Exception:
                pass

    # =========================================================
    # Relógio e clima
    # =========================================================
    def _atualizar_relogio(self):
        agora = datetime.now(self.tz_belem)
        dias = [
            "Segunda-feira",
            "Terça-feira",
            "Quarta-feira",
            "Quinta-feira",
            "Sexta-feira",
            "Sábado",
            "Domingo",
        ]
        self.lbl_hora.configure(text=agora.strftime("%H:%M:%S"))
        self.lbl_data.configure(text=f"{dias[agora.weekday()]}, {agora.strftime('%d/%m/%Y')}")
        self._job_relogio = self.after(1000, self._atualizar_relogio)

    def _atualizar_temperatura(self):
        threading.Thread(target=self._buscar_temperatura, daemon=True).start()
        self._job_clima = self.after(600000, self._atualizar_temperatura)

    def _buscar_temperatura(self):
        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=-1.4558&longitude=-48.5044"
            "&current=temperature_2m,apparent_temperature,weather_code"
            "&timezone=America%2FBelem"
        )

        temperatura_txt = "-- °C"
        clima_txt = "Sem conexão com serviço de clima"
        atualizado_txt = f"Atualizado às {datetime.now(self.tz_belem).strftime('%H:%M')}"

        try:
            with urlopen(url, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))

            current = payload.get("current", {})
            temperatura = current.get("temperature_2m")
            sensacao = current.get("apparent_temperature")
            weather_code = current.get("weather_code")

            if isinstance(temperatura, (int, float)):
                temperatura_txt = f"{temperatura:.1f} °C"

            descricao = self._descricao_clima(weather_code)
            if isinstance(sensacao, (int, float)):
                clima_txt = f"Sensação {sensacao:.1f} °C | {descricao}"
            else:
                clima_txt = descricao

        except (URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError):
            pass

        try:
            self.after(0, lambda: self._aplicar_clima_ui(temperatura_txt, clima_txt, atualizado_txt))
        except Exception:
            pass

    def _aplicar_clima_ui(self, temperatura_txt, clima_txt, atualizado_txt):
        if not self.winfo_exists():
            return
        self.lbl_temperatura.configure(text=temperatura_txt)
        self.lbl_clima.configure(text=clima_txt)
        self.lbl_temp_atualizada.configure(text=atualizado_txt)

    def _descricao_clima(self, code):
        mapa = {
            0: "Céu limpo",
            1: "Predominantemente limpo",
            2: "Parcialmente nublado",
            3: "Nublado",
            45: "Nevoeiro",
            48: "Nevoeiro com geada",
            51: "Garoa fraca",
            53: "Garoa moderada",
            55: "Garoa forte",
            61: "Chuva fraca",
            63: "Chuva moderada",
            65: "Chuva forte",
            80: "Pancadas de chuva fracas",
            81: "Pancadas de chuva moderadas",
            82: "Pancadas de chuva fortes",
            95: "Tempestade",
        }
        return mapa.get(code, "Clima indisponível")

    # =========================================================
    # Tooltip de serviços (hover/click)
    # =========================================================
    def _registrar_bind_root_click(self):
        try:
            top = self.winfo_toplevel()
            top.bind("<Button-1>", self._on_root_click, add="+")
        except Exception:
            pass

    def _on_root_click(self, event):
        if self.tooltip is None and not self.tooltip_pinned:
            return

        try:
            clicked_widget = event.widget
        except Exception:
            self._ocultar_tooltip_servicos(forcar=True)
            return

        if self._widget_pertence_ao_tooltip(clicked_widget):
            return

        if isinstance(clicked_widget, ctk.CTkButton) and getattr(clicked_widget, "_eh_dia_calendario", False):
            return

        self._ocultar_tooltip_servicos(forcar=True)

    def _widget_pertence_ao_tooltip(self, widget):
        if self.tooltip is None:
            return False
        atual = widget
        while atual is not None:
            if atual == self.tooltip:
                return True
            try:
                atual = atual.master
            except Exception:
                break
        return False

    def _agendar_hover_tooltip(self, widget, data_dia):
        self._cancelar_hover_agendado()
        if self.tooltip_pinned:
            return
        self._hover_widget = widget
        self._hover_data = data_dia
        self._hover_job = self.after(250, self._mostrar_hover_tooltip_agendado)

    def _mostrar_hover_tooltip_agendado(self):
        self._hover_job = None
        widget = self._hover_widget
        data_dia = self._hover_data

        if widget is None or data_dia is None:
            return

        try:
            if not widget.winfo_exists():
                return
        except Exception:
            return

        self._mostrar_tooltip_servicos(widget, data_dia, fixar=False)

    def _cancelar_hover_agendado(self):
        if self._hover_job is not None:
            try:
                self.after_cancel(self._hover_job)
            except Exception:
                pass
            self._hover_job = None

    def _mostrar_tooltip_servicos(self, widget, data_dia, fixar=False):
        agenda = self.servicos.get(data_dia.isoformat(), [])
        if not agenda:
            return

        try:
            if not widget.winfo_exists():
                return
        except Exception:
            return

        self._ocultar_tooltip_servicos(forcar=True)

        try:
            x = widget.winfo_rootx() + 10
            y = widget.winfo_rooty() + widget.winfo_height() + 6
        except Exception:
            return

        self.tooltip = ctk.CTkToplevel(self)
        self.tooltip.overrideredirect(True)
        self.tooltip.attributes("-topmost", True)
        self.tooltip.geometry(f"+{x}+{y}")

        box = ctk.CTkFrame(
            self.tooltip,
            fg_color="#FFFFFF",
            corner_radius=10,
            border_width=1,
            border_color="#D9D9D9",
        )
        box.pack(fill="both", expand=True)

        titulo = data_dia.strftime("%d/%m/%Y")
        ctk.CTkLabel(
            box,
            text=f"Serviços • {titulo}",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).pack(anchor="w", padx=10, pady=(8, 4))

        for item in agenda:
            ctk.CTkLabel(
                box,
                text=f"• {item}",
                font=ctk.CTkFont(family=theme.FONTE, size=11),
                text_color=theme.COR_TEXTO_SEC,
                justify="left",
                anchor="w",
                wraplength=280,
            ).pack(anchor="w", padx=10, pady=1)

        ctk.CTkLabel(box, text="", height=4).pack()
        self.tooltip_pinned = fixar

    def _ocultar_tooltip_servicos(self, forcar=False):
        if self.tooltip_pinned and not forcar:
            return

        if self.tooltip is not None:
            try:
                self.tooltip.destroy()
            except Exception:
                pass
            self.tooltip = None

        if forcar:
            self.tooltip_pinned = False

    def _toggle_tooltip_data(self, widget, data_dia):
        self._cancelar_hover_agendado()

        mesma_data = self.data_selecionada == data_dia
        tinha_fixado = self.tooltip_pinned and self.tooltip is not None

        self.data_selecionada = data_dia
        self._render_calendario()

        if data_dia.isoformat() not in self.servicos:
            self._ocultar_tooltip_servicos(forcar=True)
            return

        if mesma_data and tinha_fixado:
            self._ocultar_tooltip_servicos(forcar=True)
        else:
            self._mostrar_tooltip_servicos(widget, data_dia, fixar=True)

    # =========================================================
    # Calendário
    # =========================================================
    def _render_calendario(self):
        self._cancelar_hover_agendado()

        for widget in self.frame_dias.winfo_children():
            widget.destroy()

        self.lbl_mes_ano.configure(text=f"{self._nome_mes(self.cal_mes)} {self.cal_ano}")

        nomes_dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        for col, nome in enumerate(nomes_dias):
            lbl = ctk.CTkLabel(
                self.frame_dias,
                text=nome,
                font=self.font_dia_semana,
                text_color=theme.COR_TEXTO_SEC,
                fg_color="transparent",
            )
            lbl.grid(row=0, column=col, padx=3, pady=(6, 4), sticky="nsew")

        cal = calendar.Calendar(firstweekday=0)
        semanas = cal.monthdatescalendar(self.cal_ano, self.cal_mes)

        for row, semana in enumerate(semanas, start=1):
            for col, data_dia in enumerate(semana):
                if data_dia.month != self.cal_mes:
                    ctk.CTkLabel(
                        self.frame_dias,
                        text=str(data_dia.day),
                        font=self.font_dia_numero,
                        text_color="#B0B0B0",
                    ).grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
                    continue

                chave = data_dia.isoformat()
                tem_servico = chave in self.servicos

                texto = str(data_dia.day)
                if tem_servico:
                    texto += " •"

                fg = theme.COR_BOTAO
                text_color = theme.COR_TEXTO

                if data_dia == self.data_selecionada:
                    fg = theme.COR_SELECIONADO
                    text_color = theme.COR_TEXTO
                elif tem_servico:
                    fg = "#EAF8FE"

                btn = ctk.CTkButton(
                    self.frame_dias,
                    text=texto,
                    height=34,
                    corner_radius=8,
                    fg_color=fg,
                    hover_color=theme.COR_HOVER,
                    text_color=text_color,
                    font=self.font_dia_numero,
                    border_width=1 if tem_servico else 0,
                    border_color="#BEE9FB" if tem_servico else theme.COR_BOTAO,
                    command=lambda b=None, d=data_dia: None,
                )
                btn.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
                btn._eh_dia_calendario = True

                btn.configure(command=lambda b=btn, d=data_dia: self._toggle_tooltip_data(b, d))

                if tem_servico:
                    btn.bind("<Enter>", lambda e, b=btn, d=data_dia: self._agendar_hover_tooltip(b, d))
                    btn.bind("<Leave>", lambda e: self._cancelar_hover_agendado())
                else:
                    btn.bind("<Enter>", lambda e: self._cancelar_hover_agendado())
                    btn.bind("<Leave>", lambda e: None)

        self._atualizar_calendario_estilo()

    def _mes_anterior(self):
        self._cancelar_hover_agendado()
        self._ocultar_tooltip_servicos(forcar=True)

        self.cal_mes -= 1
        if self.cal_mes == 0:
            self.cal_mes = 12
            self.cal_ano -= 1

        self.data_selecionada = date(self.cal_ano, self.cal_mes, 1)
        self._render_calendario()

    def _mes_proximo(self):
        self._cancelar_hover_agendado()
        self._ocultar_tooltip_servicos(forcar=True)

        self.cal_mes += 1
        if self.cal_mes == 13:
            self.cal_mes = 1
            self.cal_ano += 1

        self.data_selecionada = date(self.cal_ano, self.cal_mes, 1)
        self._render_calendario()

    def _nome_mes(self, mes):
        nomes = {
            1: "Janeiro",
            2: "Fevereiro",
            3: "Março",
            4: "Abril",
            5: "Maio",
            6: "Junho",
            7: "Julho",
            8: "Agosto",
            9: "Setembro",
            10: "Outubro",
            11: "Novembro",
            12: "Dezembro",
        }
        return nomes[mes]

    # =========================================================
    # Mock de dados
    # =========================================================
    def _mock_servicos(self):
        hoje = date.today()
        return {
            hoje.isoformat(): [
                "09:00 - Revisar freezer da loja 1",
                "15:30 - Entrega especial de sorvetes",
            ],
            (hoje + timedelta(days=1)).isoformat(): [
                "08:30 - Limpeza técnica da máquina de açaí",
            ],
            (hoje + timedelta(days=2)).isoformat(): [
                "10:00 - Manutenção preventiva no balcão",
                "16:00 - Reabastecimento de estoque",
            ],
            (hoje + timedelta(days=4)).isoformat(): [
                "14:00 - Serviço externo em evento corporativo",
            ],
        }

    # =========================================================
    # Limpeza
    # =========================================================
    def destroy(self):
        try:
            self._cancelar_hover_agendado()
        except Exception:
            pass

        try:
            self._ocultar_tooltip_servicos(forcar=True)
        except Exception:
            pass

        for attr in (
            "_job_relogio",
            "_job_clima",
            "_job_resize_inicio",
            "_job_resize_calendario",
        ):
            try:
                job = getattr(self, attr, None)
                if job is not None:
                    self.after_cancel(job)
                    setattr(self, attr, None)
            except Exception:
                pass

        super().destroy()