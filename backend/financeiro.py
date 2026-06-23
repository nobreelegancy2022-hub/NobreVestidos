from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from backend.app import db
from backend.models.despesa import Despesa, MetaMensal
from backend.models.contrato import Pagamento
from datetime import date, datetime

bp = Blueprint("financeiro", __name__, url_prefix="/financeiro")

CATEGORIAS = [
    ("manutencao",  "Manutenção de Peças"),
    ("compra_peca", "Compra de Peças"),
    ("aluguel",     "Aluguel do Espaço"),
    ("salario",     "Salários"),
    ("marketing",   "Marketing"),
    ("outros",      "Outros"),
]

@bp.route("/")
@login_required
def index():
    hoje = date.today()
    mes  = int(request.args.get("mes", hoje.month))
    ano  = int(request.args.get("ano", hoje.year))

    mes_inicio = datetime(ano, mes, 1)
    mes_fim    = datetime(ano+1, 1, 1) if mes == 12 else datetime(ano, mes+1, 1)

    despesas = Despesa.query.filter(
        Despesa.data >= date(ano, mes, 1),
        Despesa.data <  date(mes_fim.year, mes_fim.month, 1)
    ).order_by(Despesa.data.desc()).all()

    total_despesas = sum(d.valor for d in despesas)

    # Receita do mês
    receita_mes = db.session.query(
        db.func.coalesce(db.func.sum(Pagamento.valor), 0)
    ).filter(
        Pagamento.data >= mes_inicio,
        Pagamento.data <  mes_fim
    ).scalar() or 0

    lucro = receita_mes - total_despesas

    # Meta do mês
    meta = MetaMensal.query.filter_by(mes=mes, ano=ano).first()
    meta_valor = meta.valor if meta else 0.0
    progresso = min(100, int((receita_mes / meta_valor * 100))) if meta_valor > 0 else 0

    # Por categoria
    por_cat = {}
    for d in despesas:
        por_cat[d.categoria] = por_cat.get(d.categoria, 0) + d.valor

    nomes_mes = ["","Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                 "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

    if mes == 1: mes_ant, ano_ant = 12, ano-1
    else:        mes_ant, ano_ant = mes-1, ano
    if mes == 12: mes_prox, ano_prox = 1, ano+1
    else:         mes_prox, ano_prox = mes+1, ano

    return render_template("financeiro.html",
        despesas=despesas, total_despesas=total_despesas,
        receita_mes=receita_mes, lucro=lucro,
        meta_valor=meta_valor, progresso=progresso,
        por_cat=por_cat, categorias=CATEGORIAS,
        mes=mes, ano=ano, nome_mes=nomes_mes[mes],
        mes_ant=mes_ant, ano_ant=ano_ant,
        mes_prox=mes_prox, ano_prox=ano_prox
    )


@bp.route("/despesa/nova", methods=["POST"])
@login_required
def nova_despesa():
    mes = int(request.form.get("mes", date.today().month))
    ano = int(request.form.get("ano", date.today().year))
    data_str = request.form.get("data", "")
    try:
        data_d = datetime.strptime(data_str, "%Y-%m-%d").date()
    except:
        data_d = date.today()

    d = Despesa(
        descricao  = request.form.get("descricao","").strip(),
        valor      = float(request.form.get("valor", 0) or 0),
        categoria  = request.form.get("categoria","outros"),
        data       = data_d,
        observacao = request.form.get("observacao","").strip()
    )
    db.session.add(d)
    db.session.commit()
    flash("Despesa registrada!", "success")
    return redirect(url_for("financeiro.index", mes=mes, ano=ano))


@bp.route("/despesa/<int:id>/excluir", methods=["POST"])
@login_required
def excluir_despesa(id):
    mes = int(request.form.get("mes", date.today().month))
    ano = int(request.form.get("ano", date.today().year))
    d = Despesa.query.get_or_404(id)
    db.session.delete(d)
    db.session.commit()
    flash("Despesa removida.", "warning")
    return redirect(url_for("financeiro.index", mes=mes, ano=ano))


@bp.route("/meta/salvar", methods=["POST"])
@login_required
def salvar_meta():
    mes   = int(request.form.get("mes", date.today().month))
    ano   = int(request.form.get("ano", date.today().year))
    valor = float(request.form.get("meta_valor", 0) or 0)
    meta  = MetaMensal.query.filter_by(mes=mes, ano=ano).first()
    if meta:
        meta.valor = valor
    else:
        meta = MetaMensal(mes=mes, ano=ano, valor=valor)
        db.session.add(meta)
    db.session.commit()
    flash(f"Meta de R$ {valor:,.2f} salva!".replace(",","X").replace(".",",").replace("X","."), "success")
    return redirect(url_for("financeiro.index", mes=mes, ano=ano))
