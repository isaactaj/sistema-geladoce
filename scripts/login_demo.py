import customtkinter as ctk
from PIL import Image

# =========================
# Tema Geladoce (login)
# =========================
COR_FUNDO = "#FFFFFF"
COR_FORM = "#FFFFFF"
COR_TEXTO = "#3A3A3A"
COR_TEXTO_SEC = "#6A6A6A"

COR_DESTAQUE = "#00BCD4"
COR_HOVER = "#C1ECFD"

FONTE = "Segoe UI"


class TelaLogin(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("light")
        self.title("Geladoce - Login")
        self.geometry("980x560")
        self.minsize(920, 520)
        self.configure(fg_color=COR_FUNDO)
        self.iconbitmap("sorvete.ico")
        # =====================================================
        # LAYOUT: 2 COLUNAS
        # - esquerda: imagem (flexível)
        # - direita: formulário (largura fixa)
        # =====================================================
        self.grid_rowconfigure(0, weight=1)

        # Coluna 0 (imagem) cresce
        self.grid_columnconfigure(0, weight=1)

        # Coluna 1 (form) NÃO cresce demais e tem largura mínima fixa
        self.grid_columnconfigure(1, weight=0, minsize=440)

        # =====================================================
        # ESQUERDA (imagem)
        # =====================================================
        self.frame_esquerda = ctk.CTkFrame(self, fg_color=COR_FUNDO, corner_radius=0)
        self.frame_esquerda.grid(row=0, column=0, sticky="nsew")
        self.frame_esquerda.grid_rowconfigure(0, weight=1)
        self.frame_esquerda.grid_columnconfigure(0, weight=1)

        # Carrega imagem original (sem redimensionar aqui)
        self.bg_original = Image.open("login_bg.png").convert("RGB")

        # Label que mostra a imagem (vamos atualizar sem distorcer)
        # Inicializa com placeholder pequeno, será atualizado no _atualizar_imagem_cover
        self.bg_img = ctk.CTkImage(light_image=self.bg_original, size=(1, 1))
        self.lbl_bg = ctk.CTkLabel(
            self.frame_esquerda, 
            image=self.bg_img, 
            text="",
            fg_color="transparent",
            bg_color="transparent"
        )
        self.lbl_bg.grid(row=0, column=0, sticky="nsew")

        # =====================================================
        # DIREITA (form)
        # =====================================================
        self.frame_direita = ctk.CTkFrame(self, fg_color=COR_FORM, corner_radius=0, width=440)
        self.frame_direita.grid(row=0, column=1, sticky="nsew")
        self.frame_direita.grid_propagate(False)  # <- NÃO deixa encolher por causa do conteúdo

        # Centraliza verticalmente o formulário dentro do frame direito
        self.frame_direita.grid_rowconfigure(0, weight=1)
        self.frame_direita.grid_rowconfigure(2, weight=1)
        self.frame_direita.grid_columnconfigure(0, weight=1)

        self.form = ctk.CTkFrame(self.frame_direita, fg_color="transparent")
        self.form.grid(row=1, column=0, sticky="n")
        self.form.grid_columnconfigure(0, weight=1)

        # Título
        ctk.CTkLabel(
            self.form,
            text="Acesso a Geladoce",
            font=ctk.CTkFont(family=FONTE, size=26, weight="bold"),
            text_color=COR_TEXTO
        ).grid(row=0, column=0, padx=40, pady=(0, 6), sticky="w")

        # Subtítulo
        ctk.CTkLabel(
            self.form,
            text="Entre com seu usuário e senha",
            font=ctk.CTkFont(family=FONTE, size=13),
            text_color=COR_TEXTO_SEC
        ).grid(row=1, column=0, padx=40, pady=(0, 22), sticky="w")

        # Usuário
        ctk.CTkLabel(
            self.form,
            text="Usuário",
            font=ctk.CTkFont(family=FONTE, size=12, weight="bold"),
            text_color=COR_TEXTO
        ).grid(row=2, column=0, padx=40, pady=(0, 6), sticky="w")

        self.entrada_usuario = ctk.CTkEntry(
            self.form,
            width=360, height=42,
            fg_color="#FFFFFF",
            text_color=COR_TEXTO,
            border_color="#DDDDDD"
        )
        self.entrada_usuario.grid(row=3, column=0, padx=40, pady=(0, 14), sticky="w")

        # Senha
        ctk.CTkLabel(
            self.form,
            text="Senha",
            font=ctk.CTkFont(family=FONTE, size=12, weight="bold"),
            text_color=COR_TEXTO
        ).grid(row=4, column=0, padx=40, pady=(0, 6), sticky="w")

        self.entrada_senha = ctk.CTkEntry(
            self.form,
            width=360, height=42,
            fg_color="#FFFFFF",
            text_color=COR_TEXTO,
            border_color="#DDDDDD",
            show="•"
        )
        self.entrada_senha.grid(row=5, column=0, padx=40, pady=(0, 10), sticky="w")

        # Feedback
        self.lbl_feedback = ctk.CTkLabel(
            self.form,
            text="",
            font=ctk.CTkFont(family=FONTE, size=12),
            text_color="#D32F2F"
        )
        self.lbl_feedback.grid(row=6, column=0, padx=40, pady=(0, 12), sticky="w")

        # Botões
        self.btn_entrar = ctk.CTkButton(
            self.form,
            text="Entrar",
            width=360, height=44,
            fg_color=COR_DESTAQUE,
            hover_color=COR_HOVER,
            text_color="#FFFFFF",
            font=ctk.CTkFont(family=FONTE, size=13, weight="bold"),
            command=self.entrar
        )
        self.btn_entrar.grid(row=7, column=0, padx=40, pady=(0, 12), sticky="w")

        self.btn_sair = ctk.CTkButton(
            self.form,
            text="Sair",
            width=360, height=42,
            fg_color="#FFFFFF",
            hover_color="#EEEEEE",
            text_color=COR_TEXTO,
            border_width=1,
            border_color="#DDDDDD",
            font=ctk.CTkFont(family=FONTE, size=13, weight="bold"),
            command=self.destroy
        )
        self.btn_sair.grid(row=8, column=0, padx=40, pady=(0, 6), sticky="w")

        # Enter para logar
        self.bind("<Return>", lambda e: self.entrar())
        self.entrada_usuario.focus()

        # Atualiza imagem "cover" ao redimensionar
        self.after(50, self._atualizar_imagem_cover)
        self.bind("<Configure>", lambda e: self.after_idle(self._atualizar_imagem_cover))

    # =====================================================
    # Imagem tipo "cover" (sem distorcer, preenche tudo)
    # - Redimensiona para cobrir o frame mantendo proporção
    # =====================================================
    def _atualizar_imagem_cover(self):
        try:
            w = max(200, self.frame_esquerda.winfo_width())
            h = max(200, self.frame_esquerda.winfo_height())

            # Calcula escala para cobrir o frame (cover mode)
            img_w, img_h = self.bg_original.size
            scale_w = w / img_w
            scale_h = h / img_h
            scale = max(scale_w, scale_h)  # Usa a maior escala para cobrir tudo

            # Redimensiona com melhor qualidade
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            img_resized = self.bg_original.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Corta o centro (cover mode)
            x = (new_w - w) // 2
            y = (new_h - h) // 2
            img_cropped = img_resized.crop((x, y, x + w, y + h))

            # Atualiza a imagem
            self.bg_img.configure(light_image=img_cropped, size=(w, h))

        except Exception:
            pass

    def entrar(self):
        usuario = self.entrada_usuario.get().strip()
        senha = self.entrada_senha.get().strip()

        if not usuario or not senha:
            self.lbl_feedback.configure(text="Preencha usuário e senha.", text_color="#D32F2F")
            return

        if usuario == "admin" and senha == "admin":
            self.lbl_feedback.configure(text="Login OK (placeholder)!", text_color="#2E7D32")
        else:
            self.lbl_feedback.configure(text="Usuário ou senha inválidos.", text_color="#D32F2F")


if __name__ == "__main__":
    TelaLogin().mainloop()
