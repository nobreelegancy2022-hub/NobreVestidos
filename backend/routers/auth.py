from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from backend.models.usuario import Usuario
from backend.app import login_manager

bp = Blueprint("auth", __name__)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@bp.route("/", methods=["GET", "POST"])
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_input = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        usuario = Usuario.query.filter_by(email=login_input, ativo=True).first()
        if usuario and usuario.verificar_senha(senha):
            login_user(usuario, remember=True)
            next_page = request.args.get("next", "")
            if "app" in next_page:
                return redirect(url_for("pwa.app_view"))
            return redirect(url_for("contratos.novo"))
        flash("Login ou senha incorretos.", "danger")
    return render_template("login.html")

@bp.route("/login-app", methods=["GET", "POST"])
def login_app():
    if request.method == "POST":
        login_input = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        usuario = Usuario.query.filter_by(email=login_input, ativo=True).first()
        if usuario and usuario.verificar_senha(senha):
            login_user(usuario, remember=True)
            return redirect(url_for("pwa.app_view"))
        flash("Login ou senha incorretos.", "danger")
    return render_template("pwa/login_app.html")

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
