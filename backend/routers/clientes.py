from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from backend.app import db
from backend.models.cliente import Cliente

bp = Blueprint("clientes", __name__, url_prefix="/clientes")

@bp.route("/")
@login_required
def index():
    busca = request.args.get("busca", "")
    q = Cliente.query
    if busca:
        q = q.filter(
            db.or_(
                Cliente.nome.ilike(f"%{busca}%"),
                Cliente.cpf.ilike(f"%{busca}%"),
                Cliente.telefone.ilike(f"%{busca}%")
            )
        )
    clientes = q.order_by(Cliente.nome).all()
    return render_template("clientes.html", clientes=clientes, busca=busca)

@bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    if request.method == "POST":
        cliente = Cliente(
            nome=request.form["nome"],
            cpf=request.form.get("cpf", ""),
            telefone=request.form.get("telefone", ""),
            email=request.form.get("email", ""),
            endereco=request.form.get("endereco", ""),
            observacoes=request.form.get("observacoes", "")
        )
        db.session.add(cliente)
        db.session.commit()
        flash(f"Cliente {cliente.nome} cadastrado!", "success")
        return redirect(url_for("clientes.index"))
    return render_template("clientes_form.html", cliente=None)

@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
def editar(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == "POST":
        cliente.nome = request.form["nome"]
        cliente.cpf = request.form.get("cpf", "")
        cliente.telefone = request.form.get("telefone", "")
        cliente.email = request.form.get("email", "")
        cliente.endereco = request.form.get("endereco", "")
        cliente.observacoes = request.form.get("observacoes", "")
        db.session.commit()
        flash("Cliente atualizado!", "success")
        return redirect(url_for("clientes.index"))
    return render_template("clientes_form.html", cliente=cliente)

@bp.route("/<int:id>")
@login_required
def detalhe(id):
    cliente = Cliente.query.get_or_404(id)
    return render_template("clientes_detalhe.html", cliente=cliente)

@bp.route("/<int:id>/excluir", methods=["POST"])
@login_required
def excluir(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    flash("Cliente removido.", "warning")
    return redirect(url_for("clientes.index"))
