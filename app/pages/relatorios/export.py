import io
from pathlib import Path
from datetime import datetime

import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader


class GeradorExportRelatorios:
    """
    Exportador de relatórios (Excel e PDF) com base em dados reais da tela,
    sem usar random.

    Diretório padrão:
        geladocesistema/exports/relatorios
    """

    def __init__(self, output_dir=None):
        # export.py -> app/pages/relatorios/export.py
        # parents[3] = raiz do projeto (geladocesistema)
        base_project_dir = Path(__file__).resolve().parents[3]
        self.output_dir = Path(output_dir) if output_dir else (base_project_dir / "exports" / "relatorios")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------
    def _slug(self, texto):
        mapa = {
            "ã": "a", "á": "a", "à": "a", "â": "a",
            "é": "e", "ê": "e",
            "í": "i",
            "ó": "o", "ô": "o", "õ": "o",
            "ú": "u",
            "ç": "c",
            "/": "_", "\\": "_", " ": "_", "-": "_",
        }

        txt = str(texto or "").strip().lower()
        for origem, destino in mapa.items():
            txt = txt.replace(origem, destino)

        while "__" in txt:
            txt = txt.replace("__", "_")

        return txt.strip("_") or "geral"

    def _fmt_dinheiro(self, valor):
        try:
            numero = float(valor)
        except Exception:
            numero = 0.0
        return f"R$ {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _montar_nome_base(self, pagina):
        st = pagina.get_state()
        periodo = self._slug(st.get("periodo", "periodo"))
        tipo = self._slug(st.get("tipo", "todos"))
        categoria = self._slug(st.get("categoria", "todos"))
        carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"relatorio_{periodo}_{tipo}_{categoria}_{carimbo}"

    def _caminho_saida(self, pagina, extensao):
        nome_base = self._montar_nome_base(pagina)
        return self.output_dir / f"{nome_base}.{extensao}"

    def _fig_to_imagereader(self, fig):
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
        buf.seek(0)
        return ImageReader(buf)

    def _obter_dados(self, pagina):
        st = pagina.get_state()
        dados = st.get("dados_relatorio", {}) or {}

        return {
            "state": st,
            "faturamento": float(dados.get("faturamento", 0) or 0),
            "qtd_vendas": int(dados.get("qtd_vendas", 0) or 0),
            "ticket_medio": float(dados.get("ticket_medio", 0) or 0),
            "serie_por_dia": dados.get("serie_por_dia", {}) or {},
            "top_produtos": dados.get("top_produtos", []) or [],
            "vendas": dados.get("vendas", []) or [],
            "taxas_entrega": float(dados.get("taxas_entrega", 0) or 0),
        }

    def _linhas_vendas(self, vendas):
        linhas = []

        for venda in vendas:
            itens = venda.get("itens", []) or []
            itens_txt = " | ".join(
                f'{item.get("produto_nome", "")} x{item.get("qtd", 0)}'
                for item in itens
            )

            data_txt = ""
            data_obj = venda.get("data")
            if data_obj:
                try:
                    data_txt = data_obj.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    data_txt = str(data_obj)

            linhas.append({
                "ID": venda.get("id"),
                "Data": data_txt,
                "Tipo": venda.get("tipo", ""),
                "Forma de Pagamento": venda.get("forma_pagamento", ""),
                "Subtotal": float(venda.get("subtotal", 0) or 0),
                "Desconto": float(venda.get("desconto", 0) or 0),
                "Taxa de Entrega": float(venda.get("taxa_entrega", 0) or 0),
                "Total": float(venda.get("total", 0) or 0),
                "Itens": itens_txt,
                "Observação": venda.get("observacao", ""),
            })

        return linhas

    # ------------------------------------------------------------
    # Exportação Excel
    # ------------------------------------------------------------
    def exportar_excel(self, pagina):
        dados = self._obter_dados(pagina)
        st = dados["state"]
        caminho = self._caminho_saida(pagina, "xlsx")

        df_kpis = pd.DataFrame([
            {"Indicador": "Faturamento", "Valor": dados["faturamento"], "Descrição": "Valor real do período"},
            {"Indicador": "Quantidade de vendas", "Valor": dados["qtd_vendas"], "Descrição": "Total de vendas reais"},
            {"Indicador": "Ticket médio", "Valor": dados["ticket_medio"], "Descrição": "Faturamento ÷ Vendas"},
            {"Indicador": "Taxas de entrega", "Valor": dados["taxas_entrega"], "Descrição": "Somatório das taxas (quando houver)"},
        ])

        df_filtros = pd.DataFrame([
            {
                "Período": st.get("periodo", ""),
                "Tipo": st.get("tipo", ""),
                "Categoria": st.get("categoria", ""),
                "Gerado em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            }
        ])

        serie = dados["serie_por_dia"]
        dias = sorted(serie.keys())
        df_faturamento_diario = pd.DataFrame([
            {"Dia": dia, "Faturamento": float(serie[dia])}
            for dia in dias
        ])

        df_top_produtos = pd.DataFrame([
            {"Produto": nome, "Quantidade": qtd}
            for nome, qtd in dados["top_produtos"]
        ])

        df_vendas = pd.DataFrame(self._linhas_vendas(dados["vendas"]))

        with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
            df_filtros.to_excel(writer, sheet_name="Resumo", index=False, startrow=0)
            df_kpis.to_excel(writer, sheet_name="Resumo", index=False, startrow=3)
            df_faturamento_diario.to_excel(writer, sheet_name="Faturamento_Diario", index=False)
            df_top_produtos.to_excel(writer, sheet_name="Top_Produtos", index=False)
            df_vendas.to_excel(writer, sheet_name="Vendas", index=False)

        return str(caminho)

    # ------------------------------------------------------------
    # Exportação PDF
    # ------------------------------------------------------------
    def exportar_pdf(self, pagina):
        dados = self._obter_dados(pagina)
        st = dados["state"]
        caminho = self._caminho_saida(pagina, "pdf")

        c = pdf_canvas.Canvas(str(caminho), pagesize=A4)
        w, h = A4

        def nova_pagina():
            c.showPage()
            return h - 2 * cm

        y = h - 2 * cm

        # Cabeçalho
        c.setFont("Helvetica-Bold", 16)
        c.drawString(2 * cm, y, "Relatório Gerencial - Geladoce")
        y -= 0.8 * cm

        c.setFont("Helvetica", 11)
        c.drawString(2 * cm, y, f'Período: {st.get("periodo", "")}')
        y -= 0.55 * cm
        c.drawString(2 * cm, y, f'Tipo: {st.get("tipo", "")}    Categoria: {st.get("categoria", "")}')
        y -= 0.55 * cm
        c.drawString(2 * cm, y, f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
        y -= 1.0 * cm

        # KPIs
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Indicadores")
        y -= 0.7 * cm

        c.setFont("Helvetica", 11)
        linhas_kpi = [
            f'Faturamento: {self._fmt_dinheiro(dados["faturamento"])}',
            f'Quantidade de vendas: {dados["qtd_vendas"]}',
            f'Ticket médio: {self._fmt_dinheiro(dados["ticket_medio"])}',
            f'Taxas de entrega: {self._fmt_dinheiro(dados["taxas_entrega"])}',
        ]

        for linha in linhas_kpi:
            if y < 2 * cm:
                y = nova_pagina()
            c.drawString(2 * cm, y, linha)
            y -= 0.55 * cm

        y -= 0.35 * cm

        # Faturamento diário
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Faturamento por dia")
        y -= 0.7 * cm

        c.setFont("Helvetica", 10)
        serie = dados["serie_por_dia"]
        dias = sorted(serie.keys())

        if dias:
            for dia in dias:
                if y < 2 * cm:
                    y = nova_pagina()
                c.drawString(2 * cm, y, f"Dia {dia}: {self._fmt_dinheiro(float(serie[dia]))}")
                y -= 0.45 * cm
        else:
            c.drawString(2 * cm, y, "Sem vendas no período selecionado.")
            y -= 0.5 * cm

        y -= 0.35 * cm

        # Top produtos
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Produtos mais vendidos")
        y -= 0.7 * cm

        c.setFont("Helvetica", 10)
        if dados["top_produtos"]:
            for nome, qtd in dados["top_produtos"]:
                if y < 2 * cm:
                    y = nova_pagina()
                c.drawString(2 * cm, y, f"{nome}: {qtd}")
                y -= 0.45 * cm
        else:
            c.drawString(2 * cm, y, "Sem produtos vendidos no período.")
            y -= 0.5 * cm

        # Gráficos da tela
        try:
            img1 = self._fig_to_imagereader(pagina.graf1.fig)
            img2 = self._fig_to_imagereader(pagina.graf2.fig)

            img_w = (w - 5 * cm) / 2
            img_h = 6.0 * cm

            if y - img_h < 2 * cm:
                y = nova_pagina()

            y -= 0.3 * cm
            c.setFont("Helvetica-Bold", 12)
            c.drawString(2 * cm, y, "Gráficos")
            y -= 0.4 * cm

            if y - img_h < 2 * cm:
                y = nova_pagina()

            c.drawImage(
                img1,
                2 * cm,
                y - img_h,
                width=img_w,
                height=img_h,
                preserveAspectRatio=True,
                anchor="sw"
            )
            c.drawImage(
                img2,
                2.8 * cm + img_w,
                y - img_h,
                width=img_w,
                height=img_h,
                preserveAspectRatio=True,
                anchor="sw"
            )
        except Exception:
            pass

        c.save()
        return str(caminho)


# ------------------------------------------------------------
# Compatibilidade com código antigo
# ------------------------------------------------------------
def exportar_excel(pagina, output_dir=None):
    return GeradorExportRelatorios(output_dir=output_dir).exportar_excel(pagina)


def exportar_pdf(pagina, output_dir=None):
    return GeradorExportRelatorios(output_dir=output_dir).exportar_pdf(pagina)