import io
import random
import pandas as pd
from tkinter import filedialog

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader


# ------------------------------------------------------------
# Helpers locais
# ------------------------------------------------------------
def _fmt_filename_periodo(periodo: str) -> str:
    # "Fev/2026" -> "Fev_2026"
    return periodo.replace("/", "_").replace(" ", "_")


def _produtos_por_categoria(categoria: str):
    if categoria == "Sorvete":
        return ["Chocolate", "Baunilha", "Morango", "Flocos"]
    if categoria == "Picolé":
        return ["Limão", "Uva", "Abacaxi", "Coco"]
    if categoria == "Açaí":
        return ["Açaí Puro", "Açaí c/ Morango", "Açaí c/ Banana", "Açaí c/ Granola"]
    if categoria == "Outros":
        return ["Caldinho", "Milkshake", "Café Gelado", "Churros"]
    return ["Chocolate", "Açaí", "Café Gelado", "Flocos"]


def _gerar_dados_export(pagina):
    """
    Gera dados consistentes com o dashboard, usando:
    ano, mes, tipo, categoria (mesma ideia de seed).
    """
    st = pagina.get_state()
    ano = st["ano"]
    mes = st["mes"]
    tipo = st["tipo"]
    categoria = st["categoria"]

    seed = hash((ano, mes, tipo, categoria))
    rng = random.Random(seed)

    dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    serie = [rng.randint(600, 2500) for _ in dias]

    produtos = _produtos_por_categoria(categoria)
    qtd = [rng.randint(80, 420) for _ in produtos]

    return {
        "dias": dias,
        "serie": serie,
        "produtos": produtos,
        "qtd": qtd,
    }


def _fig_to_imagereader(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    buf.seek(0)
    return ImageReader(buf)


# ------------------------------------------------------------
# Exportação Excel
# ------------------------------------------------------------
def exportar_excel(pagina):
    st = pagina.get_state()
    periodo = st["periodo"]
    tipo = st["tipo"]
    categoria = st["categoria"]

    dados = _gerar_dados_export(pagina)

    # KPIs que já estão na tela (texto pronto)
    fat = pagina.kpis["faturamento"][0].cget("text")
    fat_delta = pagina.kpis["faturamento"][1].cget("text")
    vendas = pagina.kpis["vendas"][0].cget("text")
    vendas_delta = pagina.kpis["vendas"][1].cget("text")
    ticket = pagina.kpis["ticket"][0].cget("text")
    ticket_delta = pagina.kpis["ticket"][1].cget("text")

    df_kpi = pd.DataFrame([
        {"KPI": "Faturamento", "Valor": fat, "Delta": fat_delta},
        {"KPI": "Vendas", "Valor": vendas, "Delta": vendas_delta},
        {"KPI": "Ticket Médio", "Valor": ticket, "Delta": ticket_delta},
        {"Filtro Tipo": tipo, "Filtro Categoria": categoria, "Período": periodo},
    ])

    df_g1 = pd.DataFrame({"Dia": dados["dias"], "Faturamento": dados["serie"]})
    df_g2 = pd.DataFrame({"Produto": dados["produtos"], "Quantidade": dados["qtd"]})

    sugestao = f"relatorio_{_fmt_filename_periodo(periodo)}.xlsx"
    caminho = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel (*.xlsx)", "*.xlsx")],
        initialfile=sugestao
    )
    if not caminho:
        return

    # engine openpyxl é o mais comum
    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        df_kpi.to_excel(writer, sheet_name="KPIs", index=False)
        df_g1.to_excel(writer, sheet_name="FaturamentoDiario", index=False)
        df_g2.to_excel(writer, sheet_name="ProdutosVendidos", index=False)


# ------------------------------------------------------------
# Exportação PDF
# ------------------------------------------------------------
def exportar_pdf(pagina):
    st = pagina.get_state()
    periodo = st["periodo"]
    tipo = st["tipo"]
    categoria = st["categoria"]

    sugestao = f"relatorio_{_fmt_filename_periodo(periodo)}.pdf"
    caminho = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF (*.pdf)", "*.pdf")],
        initialfile=sugestao
    )
    if not caminho:
        return

    c = pdf_canvas.Canvas(caminho, pagesize=A4)
    w, h = A4

    # Cabeçalho
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, h - 2 * cm, f"Relatório Geladoce - {periodo}")

    c.setFont("Helvetica", 11)
    c.drawString(2 * cm, h - 3 * cm, f"Tipo: {tipo}    Categoria: {categoria}")

    # KPIs
    y = h - 4 * cm  # ✅ agora y existe e começa num lugar ok

    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "KPIs")
    y -= 0.7 * cm

    c.setFont("Helvetica", 11)
    linhas = [
        ("Faturamento", pagina.kpis["faturamento"][0].cget("text"), pagina.kpis["faturamento"][1].cget("text")),
        ("Vendas", pagina.kpis["vendas"][0].cget("text"), pagina.kpis["vendas"][1].cget("text")),
        ("Ticket Médio", pagina.kpis["ticket"][0].cget("text"), pagina.kpis["ticket"][1].cget("text")),
    ]

    for nome, valor, delta in linhas:
        delta_txt = delta if delta else "—"
        c.drawString(2 * cm, y, f"{nome}: {valor} ({delta_txt})")
        y -= 0.55 * cm

    # Gráficos como imagem
    y -= 0.6 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Gráficos")
    y -= 0.4 * cm

    # Converte as figs da tela em imagem
    img1 = _fig_to_imagereader(pagina.graf1.fig)
    img2 = _fig_to_imagereader(pagina.graf2.fig)

    img_w = (w - 4 * cm) / 2
    img_h = 6.5 * cm

    # Se não tiver espaço, pula pra próxima página
    if y - img_h < 2 * cm:
        c.showPage()
        y = h - 2 * cm

    c.drawImage(img1, 2 * cm, y - img_h, width=img_w, height=img_h, preserveAspectRatio=True, anchor="sw")
    c.drawImage(img2, 2 * cm + img_w, y - img_h, width=img_w, height=img_h, preserveAspectRatio=True, anchor="sw")

    c.showPage()
    c.save()
