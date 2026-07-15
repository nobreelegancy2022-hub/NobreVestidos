from backend.app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id        = db.Column(db.Integer, primary_key=True)
    nome      = db.Column(db.String(120), nullable=False)
    email     = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash= db.Column(db.String(256), nullable=False)
    nivel     = db.Column(db.String(20), default="admin")  # admin | ajuste
    ativo     = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_ajuste(self):
        return self.nivel == "ajuste"

    @property
    def is_admin(self):
        return self.nivel == "admin"

    def __repr__(self):
        return f"<Usuario {self.email}>"
