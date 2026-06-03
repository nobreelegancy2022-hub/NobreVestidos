from backend.app import db
from datetime import datetime

class Peca(db.Model):
    __tablename__ = "pecas"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)   # Vestido, Acessorio
    cor = db.Column(db.String(50))
    modelo = db.Column(db.String(100))
    descricao = db.Column(db.Text)          # usado para acessórios (nome/descrição)
    foto_path = db.Column(db.String(300))   # caminho da foto (vestidos)
    preco_aluguel = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), default="disponivel")
    # disponivel | alugada | manutencao | inativa
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    itens = db.relationship("ContratoItem", backref="peca", lazy=True)

    def disponivel_no_periodo(self, data_inicio, data_fim):
        """Verifica se a peça está livre no período solicitado."""
        from backend.models.contrato import Contrato, ContratoItem
        conflito = db.session.query(ContratoItem).join(Contrato).filter(
            ContratoItem.peca_id == self.id,
            Contrato.status.in_(["ativo", "atrasado"]),
            Contrato.data_retirada < data_fim,
            Contrato.data_devolucao > data_inicio
        ).first()
        return conflito is None

    def __repr__(self):
        return f"<Peca {self.codigo} - {self.tipo}>"
