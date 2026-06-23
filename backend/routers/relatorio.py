from flask import Blueprint, send_file, request
from flask_login import login_required
from backend.app import db
from backend.models.contrato import Contrato, Pagamento
from backend.models.cliente import Cliente
from datetime import datetime, date
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm

bp = Blueprint("relatorio", __name__, url_prefix="/relatorio")

DOURADO = colors.HexColor("#B8962E")
ESCURO  = colors.HexColor("#8b1a4a")
CINZA   = colors.HexColor("#666666")
PRETO   = colors.black

def fmt_moeda(v):
    if not v: return "R$ 0,00"
    return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")

@bp.route("/mensal")
@login_required
def mensal():
    hoje = date.today()
    mes  = int(request.args.get("mes", hoje.month))
    ano  = int(request.args.get("ano", hoje.year))

    mes_inicio = datetime(ano, mes, 1)
    if mes == 12:
        mes_fim = datetime(ano+1, 1, 1)
    else:
        mes_fim = datetime(ano, mes+1, 1)

    nomes_mes = ["","Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                 "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
    nome_mes = nomes_mes[mes]

    # Pagamentos do mês
    pagamentos = db.session.query(Pagamento, Contrato, Cliente)\
        .join(Contrato, Pagamento.contrato_id == Contrato.id)\
        .join(Cliente,  Contrato.cliente_id   == Cliente.id)\
        .filter(Pagamento.data >= mes_inicio, Pagamento.data < mes_fim)\
        .order_by(Pagamento.data).all()

    total_recebido   = sum(r.Pagamento.valor for r in pagamentos)
    total_sinais     = sum(r.Pagamento.valor for r in pagamentos if r.Pagamento.tipo == "sinal")
    total_complement = sum(r.Pagamento.valor for r in pagamentos if r.Pagamento.tipo != "sinal")

    # Contratos do mês
    contratos_mes = Contrato.query.join(Cliente).filter(
        Contrato.criado_em >= mes_inicio,
        Contrato.criado_em < mes_fim
    ).all()
    total_contratos = len(contratos_mes)
    valor_total_contratos = sum(c.valor_total for c in contratos_mes)

    # Saldo em aberto
    em_aberto = Contrato.query.filter(
        Contrato.status.in_(["ativo","atrasado"]),
        Contrato.valor_pago < Contrato.valor_total
    ).all()
    total_aberto = sum(c.saldo_restante for c in em_aberto)

    # Por forma de pagamento
    formas = {}
    for r in pagamentos:
        f = r.Pagamento.forma or "outro"
        formas[f] = formas.get(f, 0) + r.Pagamento.valor

    # ── Gera PDF ─────────────────────────────────────────────
    buffer = io.BytesIO()
    W, H = A4
    ML = MR = 2*cm
    c = canvas.Canvas(buffer, pagesize=A4)
    hoje_fmt = datetime.now()

    # Faixa topo
    c.setFillColor(ESCURO)
    c.rect(0, H-3*cm, W, 3*cm, fill=1, stroke=0)

    # Título
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.white)
    c.drawCentredString(W/2, H-1.5*cm, "NOBRE VESTIDOS")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#AAAAAA"))
    c.drawCentredString(W/2, H-2.1*cm, "Relatório Financeiro Mensal")

    y = H - 3.5*cm

    # Período
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(PRETO)
    c.drawString(ML, y, f"Período: {nome_mes} / {ano}")
    c.setFont("Helvetica", 8)
    c.setFillColor(CINZA)
    c.drawRightString(W-MR, y, f"Gerado em {hoje_fmt.strftime('%d/%m/%Y %H:%M')}")
    y -= 0.2*cm
    c.setStrokeColor(DOURADO)
    c.setLineWidth(1.5)
    c.line(ML, y, W-MR, y)
    y -= 0.6*cm

    # Resumo em caixas
    def caixa(cx, cy, larg, alt, label, valor, cor_val):
        c.setFillColor(colors.HexColor("#F8F7F4"))
        c.roundRect(cx, cy-alt, larg, alt, 4, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#B8962E"))
        c.rect(cx, cy-alt, 0.2*cm, alt, fill=1, stroke=0)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(CINZA)
        c.drawString(cx+0.4*cm, cy-0.45*cm, label.upper())
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(cor_val)
        c.drawString(cx+0.4*cm, cy-0.95*cm, valor)

    bw = (W - ML - MR - 0.3*cm) / 2
    bh = 1.3*cm

    caixa(ML,       y, bw, bh, "Total Recebido no Mês",    fmt_moeda(total_recebido),   colors.HexColor("#1a5c33"))
    caixa(ML+bw+0.3*cm, y, bw, bh, "Saldo Total em Aberto", fmt_moeda(total_aberto),  colors.HexColor("#8B4513"))
    y -= bh + 0.3*cm
    caixa(ML,       y, bw, bh, "Contratos Fechados no Mês", str(total_contratos),        colors.HexColor("#1a3a5c"))
    caixa(ML+bw+0.3*cm, y, bw, bh, "Valor Total dos Contratos", fmt_moeda(valor_total_contratos), PRETO)
    y -= bh + 0.5*cm

    # Por forma de pagamento
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(PRETO)
    c.drawString(ML, y, "RECEITA POR FORMA DE PAGAMENTO")
    y -= 0.15*cm
    c.setStrokeColor(colors.HexColor("#DDDDCC"))
    c.setLineWidth(0.3)
    c.line(ML, y, W-MR, y)
    y -= 0.4*cm

    forma_map = {"pix":"PIX","cartao_credito":"Cartão de Crédito",
                 "cartao_debito":"Cartão de Débito","dinheiro":"Dinheiro"}
    for forma, val in sorted(formas.items(), key=lambda x: -x[1]):
        label = forma_map.get(forma, forma.capitalize())
        c.setFont("Helvetica", 9)
        c.setFillColor(PRETO)
        c.drawString(ML+0.3*cm, y, label)
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor("#1a5c33"))
        c.drawRightString(W-MR, y, fmt_moeda(val))
        y -= 0.5*cm

    y -= 0.3*cm

    # Detalhamento dos pagamentos
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(PRETO)
    c.drawString(ML, y, "DETALHAMENTO DOS PAGAMENTOS")
    y -= 0.15*cm
    c.line(ML, y, W-MR, y)
    y -= 0.35*cm

    # Header tabela
    c.setFillColor(ESCURO)
    c.rect(ML, y-0.4*cm, W-ML-MR, 0.5*cm, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(colors.white)
    for x, label in [(ML+0.2*cm,"Data"),(ML+2*cm,"Cliente"),(ML+8*cm,"Forma"),(ML+10.5*cm,"Tipo"),(W-MR-1.8*cm,"Valor")]:
        c.drawString(x, y-0.28*cm, label)
    y -= 0.6*cm

    alt_linha = 0.45*cm
    for i, r in enumerate(pagamentos):
        if y < 3*cm:
            c.showPage()
            y = H - 2*cm
        bg = colors.HexColor("#F8F7F4") if i % 2 == 0 else colors.white
        c.setFillColor(bg)
        c.rect(ML, y-alt_linha+0.1*cm, W-ML-MR, alt_linha, fill=1, stroke=0)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(PRETO)
        c.drawString(ML+0.2*cm,   y-0.22*cm, r.Pagamento.data.strftime("%d/%m/%Y"))
        nome = r.Cliente.nome[:28] if len(r.Cliente.nome) > 28 else r.Cliente.nome
        c.drawString(ML+2*cm,     y-0.22*cm, nome)
        forma_label = forma_map.get(r.Pagamento.forma or "", r.Pagamento.forma or "—")
        c.drawString(ML+8*cm,     y-0.22*cm, forma_label)
        c.drawString(ML+10.5*cm,  y-0.22*cm, (r.Pagamento.tipo or "").capitalize())
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(colors.HexColor("#1a5c33"))
        c.drawRightString(W-MR-0.2*cm, y-0.22*cm, fmt_moeda(r.Pagamento.valor))
        y -= alt_linha

    # Total
    y -= 0.1*cm
    c.setStrokeColor(DOURADO)
    c.setLineWidth(1)
    c.line(ML, y, W-MR, y)
    y -= 0.4*cm
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(PRETO)
    c.drawString(ML, y, "TOTAL RECEBIDO NO MÊS:")
    c.setFillColor(colors.HexColor("#1a5c33"))
    c.drawRightString(W-MR, y, fmt_moeda(total_recebido))

    # Rodapé
    c.setFont("Helvetica", 7)
    c.setFillColor(CINZA)
    c.drawCentredString(W/2, 1.2*cm, "Nobre Vestidos — Aluguel de Vestidos · Fortaleza/CE")

    c.save()
    buffer.seek(0)

    nome_arquivo = f"Relatorio_{nome_mes}_{ano}.pdf"
    return send_file(buffer, mimetype="application/pdf",
                     download_name=nome_arquivo, as_attachment=False)


@bp.route("/pecas")
@login_required
def pecas_mais_alugadas():
    from backend.models.peca import Peca
    from backend.models.contrato import ContratoItem, Contrato
    from sqlalchemy import func

    periodo = request.args.get("periodo", "total")
    hoje = date.today()

    q = db.session.query(
        Peca,
        func.count(ContratoItem.id).label("total_alugueis"),
    ).join(ContratoItem, Peca.id == ContratoItem.peca_id)\
     .join(Contrato, Contrato.id == ContratoItem.contrato_id)\
     .filter(Contrato.status.in_(["ativo","atrasado","devolvido"]))

    if periodo == "mes":
        q = q.filter(Contrato.data_retirada >= date(hoje.year, hoje.month, 1))
    elif periodo == "ano":
        q = q.filter(Contrato.data_retirada >= date(hoje.year, 1, 1))

    pecas = q.group_by(Peca.id)\
             .order_by(func.count(ContratoItem.id).desc())\
             .limit(30).all()

    por_tipo = {}
    for peca, total in pecas:
        if peca.tipo not in por_tipo:
            por_tipo[peca.tipo] = 0
        por_tipo[peca.tipo] += total

    return render_template("relatorio_pecas.html",
        pecas=pecas, por_tipo=por_tipo, periodo=periodo, hoje=hoje)
