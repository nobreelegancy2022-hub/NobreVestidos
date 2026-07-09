from flask import Blueprint, render_template, request
from flask_login import login_required
from backend.models.contrato import Contrato
from backend.models.cliente import Cliente
from datetime import date, timedelta, datetime

bp = Blueprint("agenda", __name__, url_prefix="/agenda")

@bp.route("/")
@login_required
def index():
    hoje = date.today()
    inicio_str = request.args.get("inicio", "")
    fim_str    = request.args.get("fim", "")
    modo       = request.args.get("modo", "semana")
    aba        = request.args.get("aba", "saidas")  # saidas | provas

    if inicio_str and fim_str:
        try:
            dt_inicio = datetime.strptime(inicio_str, "%Y-%m-%d").date()
            dt_fim    = datetime.strptime(fim_str, "%Y-%m-%d").date()
        except:
            dt_inicio = hoje - timedelta(days=hoje.weekday())
            dt_fim    = dt_inicio + timedelta(days=6)
    elif modo == "hoje":
        dt_inicio = hoje
        dt_fim    = hoje
    elif modo == "amanha":
        dt_inicio = hoje + timedelta(days=1)
        dt_fim    = hoje + timedelta(days=1)
    else:  # semana
        dt_inicio = hoje - timedelta(days=hoje.weekday())
        dt_fim    = dt_inicio + timedelta(days=6)

    # Contratos com saída no período
    contratos_saida = Contrato.query.join(Cliente).filter(
        Contrato.data_retirada >= dt_inicio,
        Contrato.data_retirada <= dt_fim,
        Contrato.status.in_(["ativo", "atrasado", "devolvido"])
    ).order_by(Contrato.data_retirada, Cliente.nome).all()

    # Contratos com prova no período
    contratos_prova = Contrato.query.join(Cliente).filter(
        Contrato.data_prova != None,
        Contrato.data_prova >= dt_inicio,
        Contrato.data_prova <= dt_fim,
        Contrato.status.in_(["ativo", "atrasado", "devolvido"])
    ).order_by(Contrato.data_prova, Cliente.nome).all()

    return render_template("agenda.html",
                           contratos_saida=contratos_saida,
                           contratos_prova=contratos_prova,
                           dt_inicio=dt_inicio,
                           dt_fim=dt_fim,
                           hoje=hoje,
                           modo=modo,
                           aba=aba)
