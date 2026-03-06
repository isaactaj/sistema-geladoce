from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as pdf_canvas


class GeradorComprovanteFechamento:
    def __init__(self, output_dir=None):
        base_project_dir = Path(__file__).resolve().parents[3]
        self.output_dir = Path(output_dir) if output_dir else (base_project_dir / "exports" / "fechamentos")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _to_decimal(self, valor):
        if isinstance(valor, Decimal):
            return valor
        txt = str(valor).strip().replace("R$", "").replace(" ", "")
        if not txt:
            return Decimal("0")
        if "," in txt and "." in txt:
            txt = txt.replace(".", "").replace(",", ".")
        else:
            txt = txt.replace(",", ".")
        try:
            return Decimal(txt)
        except Exception:
            return Decimal("0")

    def _fmt_moeda(self, valor):
        dec = self._to_decimal(valor)
        s = f"{float(dec):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {s}"

    def _fmt_data(self, valor):
        if isinstance(valor, datetime):
            return valor.strftime("%d/%m/%Y")
        if isinstance(valor, date):
            return valor.strftime("%d/%m/%Y")

        txt = str(valor).strip()
        if not txt:
            return datetime.now().strftime("%d/%m/%Y")

        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(txt, fmt).strftime("%d/%m/%Y")
            except ValueError:
                pass

        return txt

    def _fmt_data_arquivo(self, valor):
        if isinstance(valor, datetime):
            return valor.strftime("%Y-%m-%d")
        if isinstance(valor, date):
            return valor.strftime("%Y-%m-%d")

        txt = str(valor).strip()
        if not txt:
            return datetime.now().strftime("%Y-%m-%d")

        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(txt, fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass

        return datetime.now().strftime("%Y-%m-%d")

    def _quebrar_texto(self, texto, max_chars=88):
        texto = str(texto or "").strip()
        if not texto:
            return ["Sem observações."]

        palavras = texto.split()
        linhas = []
        linha_atual = ""

        for palavra in palavras:
            candidato = palavra if not linha_atual else f"{linha_atual} {palavra}"
            if len(candidato) <= max_chars:
                linha_atual = candidato
            else:
                if linha_atual:
                    linhas.append(linha_atual)
                linha_atual = palavra

        if linha_atual:
            linhas.append(linha_atual)

        return linhas or ["Sem observações."]

    def _montar_nome_arquivo(self, fechamento):
        data_ref = fechamento.get("data") or fechamento.get("data_fechamento") or date.today()
        fechamento_id = fechamento.get("id", "sem_id")
        data_txt = self._fmt_data_arquivo(data_ref)
        carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"comprovante_fechamento_{data_txt}_{fechamento_id}_{carimbo}.pdf"

    def _resolver_caminho_saida(self, fechamento, caminho_arquivo=None):
        if caminho_arquivo:
            caminho = Path(caminho_arquivo)
        else:
            nome_arquivo = self._montar_nome_arquivo(fechamento)
            caminho = self.output_dir / nome_arquivo
        caminho.parent.mkdir(parents=True, exist_ok=True)
        return caminho

    def gerar_pdf(self, fechamento, caminho_arquivo=None):
        if not isinstance(fechamento, dict):
            raise ValueError("Os dados do fechamento devem ser enviados em um dicionário.")

        caminho = self._resolver_caminho_saida(fechamento, caminho_arquivo)

        data_ref = fechamento.get("data") or fechamento.get("data_fechamento")
        fechamento_id = fechamento.get("id", "—")

        vendas_brutas = self._to_decimal(fechamento.get("vendas_brutas", 0))
        descontos = self._to_decimal(fechamento.get("descontos", 0))
        cancelamentos = self._to_decimal(fechamento.get("cancelamentos", 0))

        dinheiro = self._to_decimal(fechamento.get("dinheiro", 0))
        pix = self._to_decimal(fechamento.get("pix", 0))
        cartao = self._to_decimal(fechamento.get("cartao", 0))
        prazo = self._to_decimal(fechamento.get("prazo", 0))

        sangria = self._to_decimal(fechamento.get("sangria", 0))
        caixa_inicial = self._to_decimal(fechamento.get("caixa_inicial", 0))
        contado_caixa = self._to_decimal(fechamento.get("contado_caixa", 0))

        total_liquido = self._to_decimal(
            fechamento.get("total_liquido", max(Decimal("0"), vendas_brutas - descontos - cancelamentos))
        )
        total_recebido = self._to_decimal(
            fechamento.get("total_recebido", dinheiro + pix + cartao + prazo)
        )
        previsto_em_caixa = self._to_decimal(
            fechamento.get("previsto_em_caixa", caixa_inicial + dinheiro - sangria)
        )
        diferenca = self._to_decimal(
            fechamento.get("diferenca", contado_caixa - previsto_em_caixa)
        )

        observacao = str(fechamento.get("observacao", "")).strip()
        data_emissao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        if abs(float(diferenca)) < 0.005:
            situacao = "Conferido sem diferença"
        elif diferenca > 0:
            situacao = f"Sobra de caixa: {self._fmt_moeda(diferenca)}"
        else:
            situacao = f"Falta de caixa: {self._fmt_moeda(abs(diferenca))}"

        c = pdf_canvas.Canvas(str(caminho), pagesize=A4)
        largura, altura = A4
        y = altura - 2.0 * cm

        def nova_pagina():
            c.showPage()
            return altura - 2.0 * cm

        # Cabeçalho
        c.setFont("Helvetica-Bold", 18)
        c.drawString(2 * cm, y, "Geladoce")
        y -= 0.8 * cm

        c.setFont("Helvetica-Bold", 14)
        c.drawString(2 * cm, y, "Comprovante de Fechamento de Caixa")
        y -= 0.7 * cm

        c.setFont("Helvetica", 10)
        c.drawString(2 * cm, y, f"Data do fechamento: {self._fmt_data(data_ref)}")
        c.drawRightString(largura - 2 * cm, y, f"Emissão: {data_emissao}")
        y -= 0.5 * cm

        c.drawString(2 * cm, y, f"Registro: {fechamento_id}")
        y -= 0.5 * cm

        c.line(2 * cm, y, largura - 2 * cm, y)
        y -= 0.8 * cm

        # Resumo financeiro
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Resumo financeiro")
        y -= 0.6 * cm

        c.setFont("Helvetica", 10.5)
        linhas_resumo = [
            ("Vendas brutas", self._fmt_moeda(vendas_brutas)),
            ("Descontos", self._fmt_moeda(descontos)),
            ("Cancelamentos", self._fmt_moeda(cancelamentos)),
            ("Total líquido", self._fmt_moeda(total_liquido)),
            ("Total recebido", self._fmt_moeda(total_recebido)),
        ]
        for titulo, valor in linhas_resumo:
            if y < 3 * cm:
                y = nova_pagina()
                c.setFont("Helvetica", 10.5)
            c.drawString(2 * cm, y, titulo)
            c.drawRightString(largura - 2 * cm, y, valor)
            y -= 0.5 * cm

        y -= 0.2 * cm

        # Recebimentos
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Recebimentos")
        y -= 0.6 * cm

        c.setFont("Helvetica", 10.5)
        linhas_recebimentos = [
            ("Dinheiro", self._fmt_moeda(dinheiro)),
            ("Pix", self._fmt_moeda(pix)),
            ("Cartão", self._fmt_moeda(cartao)),
            ("Prazo", self._fmt_moeda(prazo)),
        ]
        for titulo, valor in linhas_recebimentos:
            if y < 3 * cm:
                y = nova_pagina()
                c.setFont("Helvetica", 10.5)
            c.drawString(2 * cm, y, titulo)
            c.drawRightString(largura - 2 * cm, y, valor)
            y -= 0.5 * cm

        y -= 0.2 * cm

        # Conferência do caixa
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Conferência do caixa")
        y -= 0.6 * cm

        c.setFont("Helvetica", 10.5)
        linhas_caixa = [
            ("Caixa inicial", self._fmt_moeda(caixa_inicial)),
            ("Sangria", self._fmt_moeda(sangria)),
            ("Previsto em caixa", self._fmt_moeda(previsto_em_caixa)),
            ("Contado em caixa", self._fmt_moeda(contado_caixa)),
            ("Diferença", self._fmt_moeda(diferenca)),
        ]
        for titulo, valor in linhas_caixa:
            if y < 3 * cm:
                y = nova_pagina()
                c.setFont("Helvetica", 10.5)
            c.drawString(2 * cm, y, titulo)
            c.drawRightString(largura - 2 * cm, y, valor)
            y -= 0.5 * cm

        y -= 0.2 * cm

        # Situação
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Situação")
        y -= 0.6 * cm

        c.setFont("Helvetica", 10.5)
        if y < 3 * cm:
            y = nova_pagina()
            c.setFont("Helvetica", 10.5)
        c.drawString(2 * cm, y, situacao)
        y -= 0.8 * cm

        # Observações
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Observações")
        y -= 0.6 * cm

        c.setFont("Helvetica", 10)
        for linha in self._quebrar_texto(observacao):
            if y < 3 * cm:
                y = nova_pagina()
                c.setFont("Helvetica", 10)
            c.drawString(2 * cm, y, linha)
            y -= 0.45 * cm

        # Rodapé
        if y < 3 * cm:
            y = nova_pagina()

        y -= 0.8 * cm
        c.line(2 * cm, y, largura - 2 * cm, y)
        y -= 0.7 * cm

        c.setFont("Helvetica", 9)
        c.drawString(2 * cm, y, "Documento gerado automaticamente pelo sistema Geladoce.")

        c.save()
        return str(caminho.resolve())