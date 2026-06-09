import io
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm

W, H = A4  # 595 x 842 pts
ML = 2.2 * cm
MR = 2.2 * cm
TW = W - ML - MR

# Paleta elegante
DOURADO    = colors.HexColor("#B8962E")
DOURADO_CLR= colors.HexColor("#D4AF5A")
ESCURO     = colors.HexColor("#8b1a4a")
CINZA_ESC  = colors.HexColor("#333344")
CINZA_MED  = colors.HexColor("#666677")
CINZA_CLR  = colors.HexColor("#9999AA")
PRETO      = colors.HexColor("#111111")
BRANCO     = colors.white
FUNDO_SEC  = colors.HexColor("#F8F7F4")

def fmt_data(d):
    if not d: return "—"
    return d.strftime("%d/%m/%Y") if hasattr(d, "strftime") else str(d)

def fmt_moeda(v):
    if not v: return "R$ 0,00"
    return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")

def nome_arquivo_contrato(contrato):
    nome = (contrato.cliente.nome or "Cliente").replace(" ", "_")
    return f"Contrato_{contrato.id:04d}_{nome}.pdf"

def set_color(c, cor):
    c.setFillColor(cor)

def linha_h(c, x, y, largura, espessura=0.5, cor=None):
    c.saveState()
    if cor: c.setStrokeColor(cor)
    c.setLineWidth(espessura)
    c.line(x, y, x + largura, y)
    c.restoreState()

def texto(c, x, y, txt, fonte="Helvetica", tam=10, cor=PRETO, alinha="L"):
    c.saveState()
    c.setFont(fonte, tam)
    c.setFillColor(cor)
    if alinha == "C":
        c.drawCentredString(x, y, str(txt))
    elif alinha == "R":
        c.drawRightString(x, y, str(txt))
    else:
        c.drawString(x, y, str(txt))
    c.restoreState()

def bloco_info(c, x, y, label, valor, larg_label=3.5*cm):
    """Linha: LABEL  valor"""
    c.saveState()
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(CINZA_MED)
    c.drawString(x, y, label)
    c.setFont("Helvetica", 9.5)
    c.setFillColor(PRETO)
    c.drawString(x + larg_label, y, str(valor))
    c.restoreState()

def wrap_text(c, x, y, txt, fonte, tam, cor, max_w, line_h):
    """Quebra texto em múltiplas linhas. Retorna novo Y."""
    c.setFont(fonte, tam)
    c.setFillColor(cor)
    words = txt.split()
    linha = ""
    for w in words:
        teste = linha + (" " if linha else "") + w
        if c.stringWidth(teste, fonte, tam) <= max_w:
            linha = teste
        else:
            c.drawString(x, y, linha)
            y -= line_h
            linha = w
    if linha:
        c.drawString(x, y, linha)
        y -= line_h
    return y

def gerar_contrato_pdf(contrato):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    hoje = datetime.now()
    cli  = contrato.cliente

    # ══════════════════════════════════════════════════════════
    # PÁGINA 1
    # ══════════════════════════════════════════════════════════
    y = H

    # ── Faixa superior escura ─────────────────────────────────
    c.setFillColor(ESCURO)
    c.rect(0, H - 3.4*cm, W, 3.4*cm, fill=1, stroke=0)

    # Data e número do contrato na faixa
    c.setFont("Helvetica", 7.5)
    c.setFillColor(CINZA_CLR)
    c.drawString(ML, H - 0.7*cm,
        hoje.strftime("%d/%m/%Y   %H:%M"))
    c.drawRightString(W - MR, H - 0.7*cm,
        f"Contrato Nº {contrato.id:04d}")

    # Linha separadora fina dourada
    c.setStrokeColor(DOURADO)
    c.setLineWidth(0.3)
    c.line(ML, H - 0.95*cm, W - MR, H - 0.95*cm)

  # Nome da empresa — NOBRE VESTIDOS
    cx = W / 2
    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(BRANCO)
    tw_nobre  = c.stringWidth("NOBRE ", "Helvetica-Bold", 26)
    tw_vest   = c.stringWidth("VESTIDOS", "Helvetica-Bold", 26)
    total_w   = tw_nobre + tw_vest
    x_start   = cx - total_w / 2

    c.drawString(x_start, H - 1.95*cm, "NOBRE ")
    c.setFillColor(DOURADO_CLR)
    c.drawString(x_start + tw_nobre, H - 1.95*cm, "VESTIDOS")
    # Subtítulo da empresa
    c.setFont("Helvetica", 7.5)
    c.setFillColor(CINZA_CLR)
    c.drawCentredString(cx, H - 2.65*cm,
        "Aluguel de Vestidos  ·  Rua Afrodísio Gondim, 119  ·  Fortaleza/CE  ·  (85) 3085-2056")

    # ── Título do contrato ────────────────────────────────────
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(ESCURO)
    c.drawCentredString(cx, H - 4.3*cm, ""CONTRATO DE LOCAÇÃO DE VESTIDO"")

    # Linha dourada sob o título
    c.setStrokeColor(DOURADO)
    c.setLineWidth(1.5)
    c.line(cx - 5.5*cm, H - 4.6*cm, cx + 5.5*cm, H - 4.6*cm)

    y = H - 5.2*cm

    # ── Função para seção com fundo ───────────────────────────
    def secao(titulo, y_pos, altura):
        # Fundo levemente cinza
        c.setFillColor(FUNDO_SEC)
        c.roundRect(ML - 0.2*cm, y_pos - altura, TW + 0.4*cm, altura, 4, fill=1, stroke=0)
        # Barra lateral dourada
        c.setFillColor(DOURADO)
        c.rect(ML - 0.2*cm, y_pos - altura, 0.22*cm, altura, fill=1, stroke=0)
        # Título da seção
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(DOURADO)
        c.drawString(ML + 0.25*cm, y_pos - 0.45*cm, titulo.upper())
        return y_pos - 0.75*cm  # Y de início do conteúdo

    LH = 0.5*cm  # espaçamento entre linhas

    # ── PARTES ────────────────────────────────────────────────
    cpf_str = f"  CPF: {cli.cpf}" if cli.cpf else ""
    n_linhas_partes = 2 + (1 if cli.endereco else 0) + (1 if cli.telefone else 0)
    alt_partes = (n_linhas_partes * LH) + 1.1*cm

    yi = secao("Partes", y, alt_partes)

    c.setFont("Helvetica-Bold", 9); c.setFillColor(CINZA_MED)
    c.drawString(ML + 0.5*cm, yi, "LOCADOR(A):")
    c.setFont("Helvetica", 9); c.setFillColor(PRETO)
    c.drawString(ML + 0.5*cm + 2.8*cm, yi, "Nobre Vestidos – Aluguel de Vestidos")
    yi -= LH

    c.setFont("Helvetica-Bold", 9); c.setFillColor(CINZA_MED)
    c.drawString(ML + 0.5*cm, yi, "LOCATÁRIO(A):")
    c.setFont("Helvetica", 9); c.setFillColor(PRETO)
    c.drawString(ML + 0.5*cm + 2.8*cm, yi, f"{cli.nome or '—'}{cpf_str}")
    yi -= LH

    if cli.endereco:
        c.setFont("Helvetica-Bold", 9); c.setFillColor(CINZA_MED)
        c.drawString(ML + 0.5*cm, yi, "Endereço:")
        c.setFont("Helvetica", 9); c.setFillColor(PRETO)
        c.drawString(ML + 0.5*cm + 2.8*cm, yi, cli.endereco)
        yi -= LH

    if cli.telefone:
        c.setFont("Helvetica-Bold", 9); c.setFillColor(CINZA_MED)
        c.drawString(ML + 0.5*cm, yi, "Telefone:")
        c.setFont("Helvetica", 9); c.setFillColor(PRETO)
        c.drawString(ML + 0.5*cm + 2.8*cm, yi, cli.telefone)

    y = y - alt_partes - 0.35*cm

    # ── DADOS DO EVENTO ───────────────────────────────────────
    obs_raw = contrato.observacoes or ""
    linhas  = [l.strip() for l in obs_raw.split("\n") if l.strip()]
    MK = ("Cor","Modelo","Busto","Cintura","Barra","Alça","Obs")
    med = {}
    obs_ev = []
    for l in linhas:
        if ":" in l and any(l.startswith(k) for k in MK):
            k,v = l.split(":",1); med[k.strip()] = v.strip()
        else:
            obs_ev.append(l)

    tipo_ev = obs_ev[0] if obs_ev else ""
    pecas_txt = " / ".join(
        " - ".join(filter(None,[i.peca.cor, i.peca.modelo]))
        for i in contrato.itens if i.peca.tipo == "Vestido")
    acess = ", ".join(filter(None,[i.peca.descricao for i in contrato.itens if i.peca.tipo == "Acessorio"]))

    n_ev = 2 + (1 if tipo_ev else 0) + (1 if pecas_txt else 0) + (1 if acess else 0)
    alt_ev = n_ev * LH + 1.1*cm
    yi = secao("Dados do Evento", y, alt_ev)

    if tipo_ev:
        c.setFont("Helvetica-Bold",9); c.setFillColor(CINZA_MED)
        c.drawString(ML+0.5*cm, yi, "Tipo de Evento:")
        c.setFont("Helvetica",9); c.setFillColor(PRETO)
        c.drawString(ML+0.5*cm+3.2*cm, yi, tipo_ev); yi -= LH

    c.setFont("Helvetica-Bold",9); c.setFillColor(CINZA_MED)
    c.drawString(ML+0.5*cm, yi, "Saída:")
    c.setFont("Helvetica",9); c.setFillColor(PRETO)
    c.drawString(ML+0.5*cm+3.2*cm, yi, fmt_data(contrato.data_retirada))
    c.setFont("Helvetica-Bold",9); c.setFillColor(CINZA_MED)
    c.drawString(ML+0.5*cm+7*cm, yi, "Devolução:")
    c.setFont("Helvetica",9); c.setFillColor(PRETO)
    c.drawString(ML+0.5*cm+9.8*cm, yi, fmt_data(contrato.data_devolucao)); yi -= LH

    if pecas_txt:
        c.setFont("Helvetica-Bold",9); c.setFillColor(CINZA_MED)
        c.drawString(ML+0.5*cm, yi, "Peças Locadas:")
        c.setFont("Helvetica",9); c.setFillColor(PRETO)
        # Quebra se necessário
        max_w = TW - 3.5*cm
        pw = c.stringWidth(pecas_txt, "Helvetica", 9)
        if pw <= max_w:
            c.drawString(ML+0.5*cm+3.2*cm, yi, pecas_txt)
        else:
            c.drawString(ML+0.5*cm+3.2*cm, yi, pecas_txt[:int(len(pecas_txt)*max_w/pw)] + "...")
        yi -= LH

    if acess:
        c.setFont("Helvetica-Bold",9); c.setFillColor(CINZA_MED)
        c.drawString(ML+0.5*cm, yi, "Itens Adicionais:")
        c.setFont("Helvetica",9); c.setFillColor(PRETO)
        c.drawString(ML+0.5*cm+3.2*cm, yi, acess)

    y = y - alt_ev - 0.35*cm

    # ── VALORES ───────────────────────────────────────────────
    forma_map = {"pix":"PIX","cartao_credito":"Cartão de Crédito",
                 "cartao_debito":"Cartão de Débito","dinheiro":"Dinheiro"}
    forma = forma_map.get(
        contrato.pagamentos[0].forma if contrato.pagamentos else "", "—")

    alt_val = 4*LH + 1.1*cm
    yi = secao("Valores", y, alt_val)

    # Tabela de valores com visual limpo
    col1 = ML + 0.5*cm
    col2 = ML + 0.5*cm + 4.5*cm

    for label, valor, destaque in [
        ("Forma de Pagamento:", forma, False),
        ("Valor Total:", fmt_moeda(contrato.valor_total), True),
        ("Sinal Pago:", fmt_moeda(contrato.valor_sinal), False),
        ("Saldo na Devolução:", fmt_moeda(contrato.saldo_restante), True),
    ]:
        c.setFont("Helvetica-Bold", 9); c.setFillColor(CINZA_MED)
        c.drawString(col1, yi, label)
        c.setFont("Helvetica-Bold" if destaque else "Helvetica", 9.5)
        c.setFillColor(DOURADO if destaque else PRETO)
        c.drawString(col2, yi, valor)
        yi -= LH

    y = y - alt_val - 0.35*cm

    # ── MEDIDAS ───────────────────────────────────────────────
    alt_med = 3*LH + 1.1*cm
    obs_med = med.get("Obs","")
    if obs_med: alt_med += LH
    yi = secao("Medidas do Vestido", y, alt_med)

    cor_str    = med.get("Cor", "—")
    modelo_str = med.get("Modelo", "—")
    busto_str  = med.get("Busto", "—") + (" cm" if med.get("Busto") else "")
    cin_str    = med.get("Cintura", "—") + (" cm" if med.get("Cintura") else "")
    barra_str  = med.get("Barra", "—") + (" cm" if med.get("Barra") else "")
    alca_str   = med.get("Alça", "—") + (" cm" if med.get("Alça") else "")

    # Linha 1: Cor e Modelo
    for label, val, xoff in [
        ("Cor:", cor_str, 0),
        ("Modelo:", modelo_str, 5*cm),
    ]:
        c.setFont("Helvetica-Bold",9); c.setFillColor(CINZA_MED)
        c.drawString(col1 + xoff, yi, label)
        c.setFont("Helvetica",9.5); c.setFillColor(PRETO)
        c.drawString(col1 + xoff + 1.8*cm, yi, val)
    yi -= LH

    # Linha 2: Busto, Cintura, Barra
    for label, val, xoff in [
        ("Busto:", busto_str, 0),
        ("Cintura:", cin_str, 4.5*cm),
        ("Barra:", barra_str, 9*cm),
    ]:
        c.setFont("Helvetica-Bold",9); c.setFillColor(CINZA_MED)
        c.drawString(col1 + xoff, yi, label)
        c.setFont("Helvetica",9.5); c.setFillColor(PRETO)
        c.drawString(col1 + xoff + 2.2*cm, yi, val)
    yi -= LH

    # Linha 3: Alça
    c.setFont("Helvetica-Bold",9); c.setFillColor(CINZA_MED)
    c.drawString(col1, yi, "Alça:")
    c.setFont("Helvetica",9.5); c.setFillColor(PRETO)
    c.drawString(col1 + 2.2*cm, yi, alca_str)

    if obs_med:
        yi -= LH
        c.setFont("Helvetica-Bold",9); c.setFillColor(CINZA_MED)
        c.drawString(col1, yi, "Obs:")
        c.setFont("Helvetica",9); c.setFillColor(PRETO)
        c.drawString(col1 + 3.2*cm, yi, obs_med)

    y = y - alt_med - 0.35*cm

    # ── CLÁUSULAS ─────────────────────────────────────────────
    clausulas = [
        ("1a", "O presente contrato tem por objeto a locação das peças de vestuário descritas acima, para uso exclusivo do(a) LOCATÁRIO(A) no evento informado, não sendo permitida a cessão ou sublocação a terceiros."),
        ("2a", "O(a) LOCATÁRIO(A) declara ter conferido as peças no momento da retirada, recebendo-as limpas, em perfeito estado de conservação e em condições de uso, comprometendo-se a devolvê-las nas mesmas condições, salvo o desgaste natural de uso."),
        ("3a", "O atraso na devolução acarretará multa diária de 10% do valor total da locação por dia de atraso, sem prejuízo da cobrança integral do valor das peças em caso de não devolução."),
        ("4a", "Em caso de dano, perda, extravio ou manchas permanentes, o(a) LOCATÁRIO(A) autoriza a cobrança do valor de reposição da peça, conforme tabela interna da loja."),
        ("5a", "Não é permitido qualquer ajuste definitivo nas peças sem autorização expressa da loja."),
        ("6a", "O sinal pago no ato da reserva não é devolvido em caso de cancelamento em prazo inferior a 7 dias do evento."),
        ("7a", "O(a) LOCATÁRIO(A) é responsável pela guarda das peças durante todo o período de locação."),
        ("8a", "Fica eleito o foro da Comarca de Fortaleza/CE para dirimir quaisquer conflitos."),
        ("9a", "As peças estarão disponíveis para retirada a partir das 14h. Retiradas anteriores dependem de autorização da loja."),
        ("10a","A devolução deverá ser realizada entre 9h e 18h do dia combinado."),
    ]

    # Calcula altura das cláusulas
    c.setFont("Helvetica", 8.5)
    alt_cl = 1.1*cm
    for num, txt in clausulas:
        words = txt.split()
        linha = f"{num} – "
        linhas_n = 1
        for w in words:
            teste = linha + w + " "
            if c.stringWidth(teste, "Helvetica", 8.5) > TW - 0.1*cm:
                linhas_n += 1
                linha = w + " "
            else:
                linha = teste
        alt_cl += linhas_n * 0.43*cm + 0.08*cm

    # Se não couber na página, nova página
    if y - alt_cl < 4*cm:
        # Rodapé p1
        _rodape(c, hoje, contrato.id, 1)
        c.showPage()
        y = H - 2*cm

    yi = secao("Cláusulas Contratuais", y, alt_cl)

    for num, txt in clausulas:
        full = f"{num} – {txt}"
        c.setFont("Helvetica-Bold", 8.5); c.setFillColor(DOURADO)
        numw = c.stringWidth(f"{num} – ", "Helvetica-Bold", 8.5)
        c.drawString(ML + 0.5*cm, yi, f"{num} – ")
        c.setFont("Helvetica", 8.5); c.setFillColor(CINZA_ESC)
        # Quebra texto do parágrafo
        x_txt = ML + 0.5*cm + numw
        max_w = TW - 0.5*cm - numw
        words = txt.split()
        linha = ""
        first = True
        for w in words:
            teste = linha + (" " if linha else "") + w
            if c.stringWidth(teste, "Helvetica", 8.5) <= (max_w if first else TW - 0.5*cm):
                linha = teste
            else:
                c.drawString(x_txt if first else ML + 0.5*cm, yi, linha)
                yi -= 0.43*cm
                first = False
                x_txt = ML + 0.5*cm
                linha = w
        if linha:
            c.drawString(x_txt if first else ML + 0.5*cm, yi, linha)
        yi -= 0.51*cm

    y = yi - 0.4*cm

    # ── Local, data e assinaturas ─────────────────────────────
    if y < 4.5*cm:
        _rodape(c, hoje, contrato.id, 1)
        c.showPage()
        y = H - 2.5*cm

    c.setFont("Helvetica", 9); c.setFillColor(CINZA_MED)
    c.drawString(ML, y, "Fortaleza/CE, ______ / ______ / __________")
    y -= 1.8*cm

    # Duas colunas de assinatura
    cx1 = ML + TW * 0.25
    cx2 = ML + TW * 0.75
    larg_ass = TW * 0.38

    for cx in [cx1, cx2]:
        c.setStrokeColor(DOURADO)
        c.setLineWidth(0.8)
        c.line(cx - larg_ass/2, y, cx + larg_ass/2, y)

    y -= 0.4*cm
    c.setFont("Helvetica", 8); c.setFillColor(CINZA_MED)
    c.drawCentredString(cx1, y, cli.nome or "Locatário(a)")
    c.drawCentredString(cx2, y, "Nobre Vestidos – Aluguel de Vestidos")
    y -= 0.28*cm
    c.setFont("Helvetica", 7.5); c.setFillColor(CINZA_CLR)
    c.drawCentredString(cx1, y, "LOCATÁRIO(A)")
    c.drawCentredString(cx2, y, "LOCADOR(A)")

    _rodape(c, hoje, contrato.id, 1)
    c.save()
    buffer.seek(0)
    return buffer


def _rodape(c, hoje, contrato_id, pagina):
    c.saveState()
    c.setStrokeColor(colors.HexColor("#DDDDCC"))
    c.setLineWidth(0.3)
    c.line(2.2*cm, 1.4*cm, W - 2.2*cm, 1.4*cm)
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor("#AAAAAA"))
    c.drawString(2.2*cm, 1.0*cm, hoje.strftime("%d/%m/%Y  %H:%M"))
    c.drawCentredString(W/2, 1.0*cm, "Nobre Vestidos – Aluguel de Vestidos")
    c.drawRightString(W - 2.2*cm, 1.0*cm, f"Contrato #{contrato_id:04d}")
    c.restoreState()
