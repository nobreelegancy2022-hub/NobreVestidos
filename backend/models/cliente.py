from backend.app import db
from datetime import datetime

class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(20), unique=True, nullable=True)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    endereco = db.Column(db.String(250))
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    contratos = db.relationship("Contrato", backref="cliente", lazy=True)

    def total_contratos(self):
        return len(self.contratos)

    def __repr__(self):
        return f"<Cliente {self.nome}>"
