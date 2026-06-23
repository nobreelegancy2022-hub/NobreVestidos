import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, template_folder="../frontend/pages",
                static_folder="../frontend/assets", static_url_path="/assets")

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "nobre_vestidos_2025_secret")

    database_url = os.environ.get("DATABASE_URL", "sqlite:///loja.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faça login para acessar o sistema."

    from backend.routers import (auth, estoque, clientes, contratos,
                                  agenda, contabilidade, consultas, pwa,
                                  dashboard, relatorio, financeiro)
    app.register_blueprint(auth.bp)
    app.register_blueprint(estoque.bp)
    app.register_blueprint(clientes.bp)
    app.register_blueprint(contratos.bp)
    app.register_blueprint(agenda.bp)
    app.register_blueprint(contabilidade.bp)
    app.register_blueprint(consultas.bp)
    app.register_blueprint(pwa.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(relatorio.bp)
    app.register_blueprint(financeiro.bp)

    with app.app_context():
        db.create_all()
        _garantir_usuario_isaac()

    return app

def _garantir_usuario_isaac():
    from backend.models.usuario import Usuario
    isaac = Usuario.query.filter_by(email="Isaac").first()
    if isaac:
        isaac.set_senha("753951")
        isaac.nome = "Isaac"
        isaac.ativo = True
        db.session.commit()
    else:
        for u in Usuario.query.all():
            if u.email != "Isaac":
                db.session.delete(u)
        novo = Usuario(nome="Isaac", email="Isaac")
        novo.set_senha("753951")
        db.session.add(novo)
        db.session.commit()
