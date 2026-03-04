# app/pages/login/page.py
from pathlib import Path

import customtkinter as ctk
from PIL import Image
from CTkMessagebox import CTkMessagebox

from app.config import theme


COR_DESTAQUE = "#00BCD4"  # mantém identidade do login
COR_FORM = "#FFFFFF"


class TelaLogin(ctk.CTkFrame):
    """
    Tela de login como FRAME.
    O main.py decide quando mostrar essa tela e quando abrir o sistema.
    """

    def __init__(
        self,
        master,
        autenticar_callback,
        on_login_success,
        on_exit=None,
        criar_usuario_callback=None,
        alterar_senha_callback=None,
    ):
        super().__init__(master, fg_color=theme.COR_FUNDO)

        self.autenticar_callback = autenticar_callback
        self.on_login_success = on_login_success
        self.on_exit = on_exit

        self.criar_usuario_callback = criar_usuario_callback
        self.alterar_senha_callback = alterar_senha_callback

        self.bg_original = None
        self.bg_img = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0, minsize=420)

        # =====================================================
        # ESQUERDA (imagem)
        # =====================================================
        self.frame_esquerda = ctk.CTkFrame(self, fg_color=theme.COR_FUNDO, corner_radius=0)
        self.frame_esquerda.grid(row=0, column=0, sticky="nsew")
        self.frame_esquerda.grid_rowconfigure(0, weight=1)
        self.frame_esquerda.grid_columnconfigure(0, weight=1)

        self.lbl_bg = ctk.CTkLabel(self.frame_esquerda, text="", fg_color="transparent")
        self.lbl_bg.grid(row=0, column=0, sticky="nsew")

        # tenta carregar imagem
        try:
            raiz_projeto = Path(__file__).resolve().parents[3]
            img_path = raiz_projeto / "assets" / "login_bg.png"
            if img_path.exists():
                self.bg_original = Image.open(img_path).convert("RGB")
        except Exception:
            self.bg_original = None

        # =====================================================
        # DIREITA (form)
        # =====================================================
        self.frame_direita = ctk.CTkFrame(self, fg_color=COR_FORM, corner_radius=0, width=420)
        self.frame_direita.grid(row=0, column=1, sticky="nsew")
        self.frame_direita.grid_propagate(False)

        self.frame_direita.grid_rowconfigure(0, weight=1)
        self.frame_direita.grid_rowconfigure(2, weight=1)
        self.frame_direita.grid_columnconfigure(0, weight=1)

        self.form = ctk.CTkFrame(self.frame_direita, fg_color="transparent")
        self.form.grid(row=1, column=0, sticky="n")
        self.form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.form,
            text="Acesso à Geladoce",
            font=ctk.CTkFont(family=theme.FONTE, size=24, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, padx=34, pady=(0, 6), sticky="w")

        ctk.CTkLabel(
            self.form,
            text="Entre com seu usuário (login ou CPF) e senha",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_TEXTO_SEC,
        ).grid(row=1, column=0, padx=34, pady=(0, 20), sticky="w")

        ctk.CTkLabel(
            self.form,
            text="Usuário / CPF",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=2, column=0, padx=34, pady=(0, 6), sticky="w")

        self.entrada_usuario = ctk.CTkEntry(
            self.form,
            width=340,
            height=42,
            fg_color="#FFFFFF",
            text_color=theme.COR_TEXTO,
            border_color="#DDDDDD",
        )
        self.entrada_usuario.grid(row=3, column=0, padx=34, pady=(0, 14), sticky="w")

        ctk.CTkLabel(
            self.form,
            text="Senha",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=4, column=0, padx=34, pady=(0, 6), sticky="w")

        self.entrada_senha = ctk.CTkEntry(
            self.form,
            width=340,
            height=42,
            fg_color="#FFFFFF",
            text_color=theme.COR_TEXTO,
            border_color="#DDDDDD",
            show="•",
        )
        self.entrada_senha.grid(row=5, column=0, padx=34, pady=(0, 10), sticky="w")

        self.lbl_feedback = ctk.CTkLabel(
            self.form,
            text="",
            font=ctk.CTkFont(family=theme.FONTE, size=12),
            text_color=theme.COR_ERRO,
        )
        self.lbl_feedback.grid(row=6, column=0, padx=34, pady=(0, 12), sticky="w")

        # Entrar
        self.btn_entrar = ctk.CTkButton(
            self.form,
            text="Entrar",
            width=340,
            height=44,
            fg_color=COR_DESTAQUE,
            hover_color=theme.COR_HOVER,
            text_color="#FFFFFF",
            font=ctk.CTkFont(family=theme.FONTE, size=13, weight="bold"),
            command=self.entrar,
        )
        self.btn_entrar.grid(row=7, column=0, padx=34, pady=(0, 10), sticky="w")

        # NOVOS BOTÕES (Sign in / Mudar senha)
        self.frame_extra = ctk.CTkFrame(self.form, fg_color="transparent")
        self.frame_extra.grid(row=8, column=0, padx=34, pady=(0, 10), sticky="ew")
        self.frame_extra.grid_columnconfigure((0, 1), weight=1)

        self.btn_criar_usuario = ctk.CTkButton(
            self.frame_extra,
            text="Criar usuário",
            height=40,
            fg_color="#FFFFFF",
            hover_color="#EEEEEE",
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color="#DDDDDD",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            command=self._abrir_cadastro_usuario,
        )
        self.btn_criar_usuario.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.btn_mudar_senha = ctk.CTkButton(
            self.frame_extra,
            text="Mudar senha",
            height=40,
            fg_color="#FFFFFF",
            hover_color="#EEEEEE",
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color="#DDDDDD",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            command=self._abrir_fluxo_mudar_senha,
        )
        self.btn_mudar_senha.grid(row=0, column=1, padx=(6, 0), sticky="ew")

        # Sair
        self.btn_sair = ctk.CTkButton(
            self.form,
            text="Sair",
            width=340,
            height=42,
            fg_color="#FFFFFF",
            hover_color="#EEEEEE",
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color="#DDDDDD",
            font=ctk.CTkFont(family=theme.FONTE, size=13, weight="bold"),
            command=self._sair,
        )
        self.btn_sair.grid(row=9, column=0, padx=34, pady=(0, 6), sticky="w")

        self.entrada_usuario.bind("<Return>", lambda e: self.entrar())
        self.entrada_senha.bind("<Return>", lambda e: self.entrar())

        self.after(50, self._atualizar_imagem_cover)
        self.bind("<Configure>", lambda e: self.after_idle(self._atualizar_imagem_cover))

        self.entrada_usuario.focus()

    # =====================================================
    # IMAGEM "COVER"
    # =====================================================
    def _atualizar_imagem_cover(self):
        if self.bg_original is None:
            return

        try:
            w = max(200, self.frame_esquerda.winfo_width())
            h = max(200, self.frame_esquerda.winfo_height())

            img_w, img_h = self.bg_original.size
            scale = max(w / img_w, h / img_h)

            new_w = int(img_w * scale)
            new_h = int(img_h * scale)

            img_resized = self.bg_original.resize((new_w, new_h), Image.Resampling.LANCZOS)

            x = (new_w - w) // 2
            y = (new_h - h) // 2
            img_cropped = img_resized.crop((x, y, x + w, y + h))

            self.bg_img = ctk.CTkImage(light_image=img_cropped, size=(w, h))
            self.lbl_bg.configure(image=self.bg_img)

        except Exception:
            pass

    # =====================================================
    # LOGIN
    # =====================================================
    def entrar(self):
        usuario = self.entrada_usuario.get().strip()
        senha = self.entrada_senha.get().strip()

        if not usuario or not senha:
            self.lbl_feedback.configure(text="Preencha usuário e senha.", text_color=theme.COR_ERRO)
            return

        try:
            dados_usuario = self.autenticar_callback(usuario, senha)
        except Exception as e:
            self.lbl_feedback.configure(text=f"Erro ao autenticar: {e}", text_color=theme.COR_ERRO)
            return

        if not dados_usuario:
            self.lbl_feedback.configure(text="Usuário ou senha inválidos.", text_color=theme.COR_ERRO)
            return

        self.lbl_feedback.configure(text="Login realizado com sucesso.", text_color=theme.COR_SUCESSO)
        self.after(120, lambda: self.on_login_success(dados_usuario))

    def _sair(self):
        if callable(self.on_exit):
            self.on_exit()

    # =====================================================
    # SIGN IN (CRIAR USUÁRIO)
    # =====================================================
    def _abrir_cadastro_usuario(self):
        if not callable(self.criar_usuario_callback):
            CTkMessagebox(title="Indisponível", message="Cadastro de usuário não configurado.", icon="warning")
            return

        win = ctk.CTkToplevel(self)
        win.title("Criar novo usuário")
        win.geometry("460x460")
        win.transient(self.winfo_toplevel())
        win.grab_set()

        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(99, weight=1)

        titulo = ctk.CTkLabel(
            win,
            text="Cadastro de Usuário",
            font=ctk.CTkFont(family=theme.FONTE, size=18, weight="bold"),
            text_color=theme.COR_TEXTO,
        )
        titulo.grid(row=0, column=0, padx=18, pady=(16, 8), sticky="w")

        # Nome
        ctk.CTkLabel(
            win, text="Nome *", font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO_SEC
        ).grid(row=1, column=0, padx=18, pady=(6, 4), sticky="w")

        ent_nome = ctk.CTkEntry(win, height=38)
        ent_nome.grid(row=2, column=0, padx=18, sticky="ew")

        # CPF
        ctk.CTkLabel(
            win, text="CPF *", font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO_SEC
        ).grid(row=3, column=0, padx=18, pady=(10, 4), sticky="w")

        ent_cpf = ctk.CTkEntry(win, height=38, placeholder_text="Somente números (11 dígitos)")
        ent_cpf.grid(row=4, column=0, padx=18, sticky="ew")

        # Tipo acesso
        ctk.CTkLabel(
            win, text="Tipo de acesso *", font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO_SEC
        ).grid(row=5, column=0, padx=18, pady=(10, 4), sticky="w")

        opt_tipo = ctk.CTkOptionMenu(
            win,
            values=["Colaborador", "Administrador"],
            fg_color="#FFFFFF",
            button_color=theme.COR_HOVER,
            button_hover_color=theme.COR_HOVER,
            text_color=theme.COR_TEXTO,
        )
        opt_tipo.grid(row=6, column=0, padx=18, sticky="ew")
        opt_tipo.set("Colaborador")

        # Senha
        ctk.CTkLabel(
            win, text="Senha *", font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO_SEC
        ).grid(row=7, column=0, padx=18, pady=(10, 4), sticky="w")

        ent_senha = ctk.CTkEntry(win, height=38, show="•")
        ent_senha.grid(row=8, column=0, padx=18, sticky="ew")

        # Confirmar
        ctk.CTkLabel(
            win, text="Confirmar senha *", font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            text_color=theme.COR_TEXTO_SEC
        ).grid(row=9, column=0, padx=18, pady=(10, 4), sticky="w")

        ent_conf = ctk.CTkEntry(win, height=38, show="•")
        ent_conf.grid(row=10, column=0, padx=18, sticky="ew")

        lbl = ctk.CTkLabel(win, text="", text_color=theme.COR_ERRO, font=ctk.CTkFont(family=theme.FONTE, size=11))
        lbl.grid(row=11, column=0, padx=18, pady=(8, 0), sticky="w")

        botoes = ctk.CTkFrame(win, fg_color="transparent")
        botoes.grid(row=12, column=0, padx=18, pady=(14, 18), sticky="ew")
        botoes.grid_columnconfigure((0, 1), weight=1)

        def somente_digitos(v): return "".join(ch for ch in str(v) if ch.isdigit())

        def criar():
            nome = ent_nome.get().strip()
            cpf = somente_digitos(ent_cpf.get())
            tipo = opt_tipo.get()
            senha = ent_senha.get()
            conf = ent_conf.get()

            if not nome or not cpf or not senha:
                lbl.configure(text="Preencha Nome, CPF e Senha.")
                return
            if len(cpf) != 11:
                lbl.configure(text="CPF inválido (11 dígitos).")
                return
            if senha != conf:
                lbl.configure(text="As senhas não conferem.")
                return

            try:
                user = self.criar_usuario_callback(nome=nome, cpf=cpf, senha=senha, tipo_acesso=tipo)
            except Exception as e:
                lbl.configure(text=str(e))
                return

            CTkMessagebox(
                title="Usuário criado",
                message=f"Usuário criado com sucesso!\n\nLogin para entrar: {user.get('login', cpf)}",
                icon="check",
            )
            win.destroy()

            # já preenche no login para facilitar
            self.entrada_usuario.delete(0, "end")
            self.entrada_usuario.insert(0, user.get("login", cpf))
            self.entrada_senha.delete(0, "end")
            self.entrada_senha.focus()

        ctk.CTkButton(
            botoes,
            text="Criar",
            height=40,
            fg_color=COR_DESTAQUE,
            hover_color=theme.COR_HOVER,
            text_color="#FFFFFF",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            command=criar,
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            botoes,
            text="Cancelar",
            height=40,
            fg_color="#FFFFFF",
            hover_color="#EEEEEE",
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color="#DDDDDD",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            command=win.destroy,
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        ent_nome.focus()

    # =====================================================
    # MUDAR SENHA (ADMIN -> TROCA)
    # =====================================================
    def _abrir_fluxo_mudar_senha(self):
        if not callable(self.alterar_senha_callback):
            CTkMessagebox(title="Indisponível", message="Alteração de senha não configurada.", icon="warning")
            return

        # 1) autenticar admin
        self._janela_autenticar_admin(self._abrir_janela_alterar_senha)

    def _janela_autenticar_admin(self, on_ok):
        win = ctk.CTkToplevel(self)
        win.title("Autorização de Administrador")
        win.geometry("420x300")
        win.transient(self.winfo_toplevel())
        win.grab_set()

        win.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            win,
            text="Confirme um Administrador",
            font=ctk.CTkFont(family=theme.FONTE, size=16, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, padx=18, pady=(16, 10), sticky="w")

        ent_user = ctk.CTkEntry(win, height=38, placeholder_text="Login ou CPF do admin")
        ent_user.grid(row=1, column=0, padx=18, pady=(0, 10), sticky="ew")

        ent_pass = ctk.CTkEntry(win, height=38, show="•", placeholder_text="Senha do admin")
        ent_pass.grid(row=2, column=0, padx=18, pady=(0, 10), sticky="ew")

        lbl = ctk.CTkLabel(win, text="", text_color=theme.COR_ERRO, font=ctk.CTkFont(family=theme.FONTE, size=11))
        lbl.grid(row=3, column=0, padx=18, pady=(0, 10), sticky="w")

        botoes = ctk.CTkFrame(win, fg_color="transparent")
        botoes.grid(row=4, column=0, padx=18, pady=(10, 16), sticky="ew")
        botoes.grid_columnconfigure((0, 1), weight=1)

        def confirmar():
            u = ent_user.get().strip()
            p = ent_pass.get().strip()
            if not u or not p:
                lbl.configure(text="Informe login e senha do admin.")
                return

            try:
                dados = self.autenticar_callback(u, p)
            except Exception as e:
                lbl.configure(text=str(e))
                return

            if not dados:
                lbl.configure(text="Credenciais inválidas.")
                return

            if dados.get("tipo_acesso") != "Administrador":
                lbl.configure(text="A conta informada não é Administrador.")
                return

            win.destroy()
            on_ok()

        ctk.CTkButton(
            botoes,
            text="Confirmar",
            height=40,
            fg_color=COR_DESTAQUE,
            hover_color=theme.COR_HOVER,
            text_color="#FFFFFF",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            command=confirmar,
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            botoes,
            text="Cancelar",
            height=40,
            fg_color="#FFFFFF",
            hover_color="#EEEEEE",
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color="#DDDDDD",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            command=win.destroy,
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        ent_user.focus()

    def _abrir_janela_alterar_senha(self):
        win = ctk.CTkToplevel(self)
        win.title("Alterar senha de usuário")
        win.geometry("460x320")
        win.transient(self.winfo_toplevel())
        win.grab_set()

        win.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            win,
            text="Alterar Senha",
            font=ctk.CTkFont(family=theme.FONTE, size=16, weight="bold"),
            text_color=theme.COR_TEXTO,
        ).grid(row=0, column=0, padx=18, pady=(16, 10), sticky="w")

        ent_login = ctk.CTkEntry(win, height=38, placeholder_text="Usuário (login) ou CPF")
        ent_login.grid(row=1, column=0, padx=18, pady=(0, 10), sticky="ew")

        ent_senha = ctk.CTkEntry(win, height=38, show="•", placeholder_text="Nova senha")
        ent_senha.grid(row=2, column=0, padx=18, pady=(0, 10), sticky="ew")

        ent_conf = ctk.CTkEntry(win, height=38, show="•", placeholder_text="Confirmar nova senha")
        ent_conf.grid(row=3, column=0, padx=18, pady=(0, 10), sticky="ew")

        lbl = ctk.CTkLabel(win, text="", text_color=theme.COR_ERRO, font=ctk.CTkFont(family=theme.FONTE, size=11))
        lbl.grid(row=4, column=0, padx=18, pady=(0, 10), sticky="w")

        botoes = ctk.CTkFrame(win, fg_color="transparent")
        botoes.grid(row=5, column=0, padx=18, pady=(10, 16), sticky="ew")
        botoes.grid_columnconfigure((0, 1), weight=1)

        def salvar():
            login = ent_login.get().strip()
            s1 = ent_senha.get()
            s2 = ent_conf.get()

            if not login or not s1:
                lbl.configure(text="Informe usuário/CPF e a nova senha.")
                return
            if s1 != s2:
                lbl.configure(text="As senhas não conferem.")
                return

            try:
                self.alterar_senha_callback(login, s1)
            except Exception as e:
                lbl.configure(text=str(e))
                return

            CTkMessagebox(title="Sucesso", message="Senha alterada com sucesso.", icon="check")
            win.destroy()

        ctk.CTkButton(
            botoes,
            text="Salvar",
            height=40,
            fg_color=COR_DESTAQUE,
            hover_color=theme.COR_HOVER,
            text_color="#FFFFFF",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            command=salvar,
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            botoes,
            text="Cancelar",
            height=40,
            fg_color="#FFFFFF",
            hover_color="#EEEEEE",
            text_color=theme.COR_TEXTO,
            border_width=1,
            border_color="#DDDDDD",
            font=ctk.CTkFont(family=theme.FONTE, size=12, weight="bold"),
            command=win.destroy,
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        ent_login.focus()