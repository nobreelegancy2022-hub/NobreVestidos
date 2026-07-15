import os
from flask import Flask, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user

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
                                  dashboard, relatorio, financeiro, ajustes)
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
    app.register_blueprint(ajustes.bp)

    # Controle de acesso: usuário nível ajuste só acessa /ajustes/
    @app.before_request
    def restringir_ajuste():
        if not current_user.is_authenticated:
            return
        if not current_user.is_ajuste:
            return
        # Rotas permitidas para ajuste
        permitidas = ("ajustes.", "auth.logout", "static")
        endpoint = request.endpoint or ""
        if not any(endpoint.startswith(p) for p in permitidas):
            return redirect(url_for("ajustes.index"))

    with app.app_context():
        db.create_all()
        _garantir_usuario_isaac()
        _garantir_usuario_ajuste()

    return app


def _garantir_usuario_isaac():
    from backend.models.usuario import Usuario
    isaac = Usuario.query.filter_by(email="Isaac").first()
    if isaac:
        isaac.set_senha("753951")
        isaac.nome = "Isaac"
        isaac.nivel = "admin"
        isaac.ativo = True
        db.session.commit()
    else:
        novo = Usuario(nome="Isaac", email="Isaac", nivel="admin")
        novo.set_senha("753951")
        db.session.add(novo)
        db.session.commit()


def _garantir_usuario_ajuste():
    from backend.models.usuario import Usuario
    u = Usuario.query.filter_by(email="ajustes").first()
    if not u:
        novo = Usuario(nome="Ajustes", email="ajustes", nivel="ajuste")
        novo.set_senha("ajustes123")
        db.session.add(novo)
        db.session.commit()
