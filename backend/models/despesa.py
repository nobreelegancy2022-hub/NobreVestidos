from backend.app import db
from datetime import datetime

class Despesa(db.Model):
    __tablename__ = "despesas"

    id          = db.Column(db.Integer, primary_key=True)
    descricao   = db.Column(db.String(200), nullable=False)
    valor       = db.Column(db.Float, nullable=False)
    categoria   = db.Column(db.String(50), default="outros")
    # manutencao | compra_peca | aluguel | salario | marketing | outros
    data        = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    observacao  = db.Column(db.String(300))
    criado_em   = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Despesa {self.descricao} R${self.valor}>"


class MetaMensal(db.Model):
    __tablename__ = "metas_mensais"

    id    = db.Column(db.Integer, primary_key=True)
    mes   = db.Column(db.Integer, nullable=False)   # 1-12
    ano   = db.Column(db.Integer, nullable=False)
    valor = db.Column(db.Float, nullable=False, default=0.0)

    __table_args__ = (db.UniqueConstraint('mes', 'ano', name='uq_meta_mes_ano'),)
