from flask import Blueprint, render_template
from flask_login import login_required, current_user
from backend.app import db
from backend.models.contrato import Contrato, Pagamento
from backend.models.cliente import Cliente
from backend.routers.contratos import _link_lembrete_retirada
from datetime import date, datetime, timedelta

bp = Blueprint("dashboard", __name__)

@bp.route("/dashboard")
@login_required
def index():
    hoje = date.today()

    contratos_ativos    = Contrato.query.filter_by(status="ativo").count()
    contratos_atrasados = Contrato.query.filter_by(status="atrasado").count()
    saidas_hoje         = Contrato.query.filter(
        Contrato.data_retirada == hoje,
        Contrato.status.in_(["ativo","atrasado"])
    ).count()

    receita_mes = db.session.query(
        db.func.coalesce(db.func.sum(Pagamento.valor), 0)
    ).filter(
        Pagamento.data >= datetime(hoje.year, hoje.month, 1)
    ).scalar() or 0

    contratos_aberto = Contrato.query.filter(
        Contrato.status.in_(["ativo","atrasado"]),
        Contrato.valor_pago < Contrato.valor_total
    ).all()
    saldo_aberto = sum(c.saldo_restante for c in contratos_aberto)

    from sqlalchemy import func, text
    formas = db.session.query(
        Pagamento.forma,
        func.sum(Pagamento.valor).label('total')
    ).filter(
        Pagamento.data >= datetime(hoje.year, hoje.month, 1)
    ).group_by(Pagamento.forma).order_by(text('total DESC')).all()

    # Alertas: devoluções próximas (3 dias)
    limite = hoje + timedelta(days=3)
    contratos_vencendo = Contrato.query.join(Cliente).filter(
        Contrato.status.in_(["ativo","atrasado"]),
        Contrato.data_devolucao <= limite
    ).order_by(Contrato.data_devolucao).all()
    alertas = []
    for c in contratos_vencendo:
        dias = (c.data_devolucao - hoje).days
        alertas.append({"contrato": c, "dias": dias})

    # Lembretes: retiradas próximas (5 dias)
    limite_retirada = hoje + timedelta(days=5)
    contratos_retirando = Contrato.query.join(Cliente).filter(
        Contrato.status.in_(["ativo","atrasado"]),
        Contrato.data_retirada >= hoje,
        Contrato.data_retirada <= limite_retirada
    ).order_by(Contrato.data_retirada).all()
    lembretes = []
    for c in contratos_retirando:
        dias = (c.data_retirada - hoje).days
        link, horario = _link_lembrete_retirada(c)
        lembretes.append({"contrato": c, "dias": dias, "horario": horario, "link": link})

    contratos_recentes = Contrato.query.order_by(
        Contrato.criado_em.desc()
    ).limit(6).all()

    nomes_mes = ["","Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                 "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

    return render_template("dashboard.html",
        hoje=hoje,
        contratos_ativos=contratos_ativos,
        contratos_atrasados=contratos_atrasados,
        saidas_hoje=saidas_hoje,
        receita_mes=receita_mes,
        saldo_aberto=saldo_aberto,
        formas_pagamento=formas,
        alertas=alertas,
        lembretes=lembretes,
        contratos_recentes=contratos_recentes,
        mes_atual=nomes_mes[hoje.month]
    )
