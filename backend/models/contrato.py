from backend.app import db
from datetime import datetime, date

class Contrato(db.Model):
    __tablename__ = "contratos"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    data_retirada = db.Column(db.Date, nullable=False)
    data_devolucao = db.Column(db.Date, nullable=False)
    data_prova    = db.Column(db.Date)
    ajuste_pronto = db.Column(db.Boolean, nullable=False, default=False)
    horario_prova = db.Column(db.String(10))
    horario_saida = db.Column(db.String(10))
    data_devolucao_real = db.Column(db.Date)
    valor_total = db.Column(db.Float, default=0.0)
    valor_sinal = db.Column(db.Float, default=0.0)
    valor_pago = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default="ativo")
    # ativo | devolvido | atrasado | cancelado
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    itens = db.relationship("ContratoItem", backref="contrato", lazy=True, cascade="all, delete-orphan")
    pagamentos = db.relationship("Pagamento", backref="contrato", lazy=True, cascade="all, delete-orphan")

    @property
    def saldo_restante(self):
        return round(self.valor_total - self.valor_pago, 2)

    @property
    def esta_atrasado(self):
        return (self.status == "ativo" and
                self.data_devolucao < date.today())

    def atualizar_status(self):
        if self.status == "ativo" and self.data_devolucao < date.today():
            self.status = "atrasado"

    def __repr__(self):
        return f"<Contrato #{self.id}>"


class ContratoItem(db.Model):
    __tablename__ = "contrato_itens"

    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey("contratos.id"), nullable=False)
    peca_id = db.Column(db.Integer, db.ForeignKey("pecas.id"), nullable=False)
    preco_cobrado = db.Column(db.Float, nullable=False)


class Pagamento(db.Model):
    __tablename__ = "pagamentos"

    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey("contratos.id"), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(20))  # sinal | complemento | total
    forma = db.Column(db.String(20)) # dinheiro | pix | cartao | outro
    observacao = db.Column(db.String(200))
    data = db.Column(db.DateTime, default=datetime.utcnow)
