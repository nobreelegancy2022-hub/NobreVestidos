from flask import Blueprint, render_template, request
from flask_login import login_required
from backend.models.contrato import Contrato
from backend.models.cliente import Cliente
from datetime import date, timedelta
import calendar

bp = Blueprint("agenda", __name__, url_prefix="/agenda")

@bp.route("/")
@login_required
def index():
    hoje = date.today()
    visao = request.args.get("visao", "mes")  # mes | semana
    mes = int(request.args.get("mes", hoje.month))
    ano = int(request.args.get("ano", hoje.year))

    # --- VISÃO SEMANA ---
    if visao == "semana":
        # Início da semana (segunda-feira)
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        fim_semana = inicio_semana + timedelta(days=6)

        contratos_semana = Contrato.query.join(Cliente).filter(
            Contrato.data_retirada >= inicio_semana,
            Contrato.data_retirada <= fim_semana,
            Contrato.status.in_(["ativo", "atrasado"])
        ).order_by(Contrato.data_retirada).all()

        # Monta dias da semana com contratos
        dias_semana = []
        for i in range(7):
            dia = inicio_semana + timedelta(days=i)
            cts = [c for c in contratos_semana if c.data_retirada == dia]
            dias_semana.append({"data": dia, "contratos": cts})

        return render_template("agenda.html",
                               visao="semana",
                               dias_semana=dias_semana,
                               hoje=hoje,
                               inicio_semana=inicio_semana,
                               fim_semana=fim_semana,
                               mes=mes, ano=ano)

    # --- VISÃO MÊS ---
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])

    contratos = Contrato.query.join(Cliente).filter(
        Contrato.data_retirada >= primeiro_dia,
        Contrato.data_retirada <= ultimo_dia,
        Contrato.status.in_(["ativo", "atrasado"])
    ).order_by(Contrato.data_retirada).all()

    agenda = {}
    for c in contratos:
        dia = c.data_retirada.day
        if dia not in agenda:
            agenda[dia] = []
        agenda[dia].append(c)

    cal = calendar.monthcalendar(ano, mes)

    mes_ant = 12 if mes == 1 else mes - 1
    ano_ant = ano - 1 if mes == 1 else ano
    mes_prox = 1 if mes == 12 else mes + 1
    ano_prox = ano + 1 if mes == 12 else ano

    nomes_mes = ["","Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                 "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

    return render_template("agenda.html",
                           visao="mes",
                           cal=cal, agenda=agenda,
                           mes=mes, ano=ano, hoje=hoje,
                           nome_mes=nomes_mes[mes],
                           mes_ant=mes_ant, ano_ant=ano_ant,
                           mes_prox=mes_prox, ano_prox=ano_prox)
