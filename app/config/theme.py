# app/config/theme.py

# ============================================================
# Tema (cores, fontes e helpers visuais) - Geladoce
# ============================================================

# ---- Cores principais ----
COR_FUNDO = "#FFFFFF"        # fundo geral
COR_PAINEL = "#F7F7F7"       # fundo do menu lateral / cards
COR_BOTAO = "#FFFFFF"        # botão normal
COR_HOVER = "#C1ECFD"        # hover
COR_SELECIONADO = "#C1ECFD"  # botão ativo/selecionado

COR_TEXTO = "#3A3A3A"        # texto principal
COR_TEXTO_SEC = "#6A6A6A"    # texto secundário

# ---- Fonte padrão ----
FONTE = "Segoe UI"

# ---- Cores semânticas (indicadores) ----
COR_SUCESSO = "#2E7D32"      # verde (estoque cheio, lucro)
COR_ERRO = "#C62828"         # vermelho (estoque critico, prejuizo)
COR_AVISO = "#FFA000"        # laranja (estoque baixo)

# ============================================================
# Helpers
# ============================================================

def cor_delta(delta: float | None) -> str:
    if delta is None: return COR_TEXTO_SEC
    if delta > 0: return COR_SUCESSO
    if delta < 0: return COR_ERRO
    return COR_TEXTO_SEC

def fmt_dinheiro(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_percentual(delta: float) -> str:
    return f"{delta * 100:.0f}%"