from flask import Blueprint, render_template, request
from flask_login import login_required
from backend.app import db
from backend.models.contrato import Contrato, Pagamento
from backend.models.cliente import Cliente
from datetime import date, datetime

bp = Blueprint("contabilidade", __name__, url_prefix="/contabilidade")

@bp.route("/")
@login_required
def index():
    hoje = date.today()
    mes = int(request.args.get("mes", hoje.month))
    ano = int(request.args.get("ano", hoje.year))

    inicio = date(ano, mes, 1)
    if mes == 12:
        fim = date(ano + 1, 1, 1)
    else:
        fim = date(ano, mes + 1, 1)

    # Pagamentos do período
    pagamentos = db.session.query(Pagamento, Contrato, Cliente)\
        .join(Contrato, Pagamento.contrato_id == Contrato.id)\
        .join(Cliente, Contrato.cliente_id == Cliente.id)\
        .filter(
            Pagamento.data >= datetime(ano, mes, 1),
            Pagamento.data < datetime(fim.year, fim.month, fim.day)
        ).order_by(Pagamento.data.desc()).all()

    total_recebido = sum(p.Pagamento.valor for p in pagamentos)
    total_sinais = sum(p.Pagamento.valor for p in pagamentos if p.Pagamento.tipo == "sinal")
    total_complementos = sum(p.Pagamento.valor for p in pagamentos if p.Pagamento.tipo != "sinal")

    # Contratos com saldo em aberto
    em_aberto = Contrato.query.join(Cliente).filter(
        Contrato.status.in_(["ativo", "atrasado"]),
        Contrato.valor_pago < Contrato.valor_total
    ).all()
    total_em_aberto = sum(c.saldo_restante for c in em_aberto)

    # Navegação de meses
    if mes == 1:
        mes_ant, ano_ant = 12, ano - 1
    else:
        mes_ant, ano_ant = mes - 1, ano
    if mes == 12:
        mes_prox, ano_prox = 1, ano + 1
    else:
        mes_prox, ano_prox = mes + 1, ano

    nome_mes = [
        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ][mes]

    return render_template("contabilidade.html",
                           pagamentos=pagamentos,
                           total_recebido=total_recebido,
                           total_sinais=total_sinais,
                           total_complementos=total_complementos,
                           em_aberto=em_aberto,
                           total_em_aberto=total_em_aberto,
                           mes=mes, ano=ano, nome_mes=nome_mes,
                           mes_ant=mes_ant, ano_ant=ano_ant,
                           mes_prox=mes_prox, ano_prox=ano_prox)
