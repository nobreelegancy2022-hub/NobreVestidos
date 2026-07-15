from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from backend.app import db
from backend.models.contrato import Contrato
from datetime import date, timedelta

bp = Blueprint("ajustes", __name__, url_prefix="/ajustes")

@bp.route("/")
@login_required
def index():
    hoje = date.today()
    limite = hoje + timedelta(days=7)

    # Contratos ativos com saída nos próximos 7 dias
    contratos = Contrato.query.filter(
        Contrato.status.in_(["ativo", "atrasado"]),
        Contrato.data_retirada >= hoje,
        Contrato.data_retirada <= limite
    ).order_by(Contrato.data_retirada, Contrato.horario_saida).all()

    # Agrupar por data
    por_dia = {}
    for c in contratos:
        dia = c.data_retirada
        if dia not in por_dia:
            por_dia[dia] = []
        por_dia[dia].append(c)

    return render_template("pwa/ajustes.html",
                           por_dia=por_dia,
                           hoje=hoje)


@bp.route("/<int:id>/toggle")
@login_required
def toggle(id):
    contrato = Contrato.query.get_or_404(id)
    contrato.ajuste_pronto = not contrato.ajuste_pronto
    db.session.commit()
    return redirect(url_for("ajustes.index"))
