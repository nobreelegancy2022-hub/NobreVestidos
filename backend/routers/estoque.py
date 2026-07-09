import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required
from backend.app import db
from backend.models.peca import Peca
from datetime import datetime
from werkzeug.utils import secure_filename

bp = Blueprint("estoque", __name__, url_prefix="/estoque")

TIPOS  = ["Vestido", "Acessorio"]
STATUS = ["disponivel", "alugada", "manutencao", "inativa"]
EXTENSOES_PERMITIDAS = {"png", "jpg", "jpeg", "webp"}

def extensao_permitida(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in EXTENSOES_PERMITIDAS

def pasta_fotos():
    pasta = os.path.join(current_app.static_folder, "fotos_vestidos")
    os.makedirs(pasta, exist_ok=True)
    return pasta

@bp.route("/")
@login_required
def index():
    filtro_tipo = request.args.get("tipo", "Vestido")
    busca       = request.args.get("busca", "")

    q = Peca.query.filter_by(tipo=filtro_tipo)
    if busca:
        q = q.filter(db.or_(
            Peca.codigo.ilike(f"%{busca}%"),
            Peca.modelo.ilike(f"%{busca}%"),
            Peca.cor.ilike(f"%{busca}%"),
            Peca.descricao.ilike(f"%{busca}%"),
        ))
    pecas       = q.order_by(Peca.codigo).all()
    total       = Peca.query.filter_by(tipo=filtro_tipo).count()
    disponiveis = Peca.query.filter_by(tipo=filtro_tipo, status="disponivel").count()
    alugadas    = Peca.query.filter_by(tipo=filtro_tipo, status="alugada").count()

    return render_template("estoque.html", pecas=pecas, tipos=TIPOS,
                           filtro_tipo=filtro_tipo, busca=busca,
                           total=total, disponiveis=disponiveis, alugadas=alugadas)


@bp.route("/cadastrar", methods=["POST"])
@login_required
def cadastrar_rapido():
    tipo = request.form.get("tipo", "Vestido")

    # Gera código automático
    abrev = {"Vestido": "VST", "Acessorio": "ACS"}.get(tipo, tipo[:3].upper())
    total_tipo = Peca.query.filter_by(tipo=tipo).count()
    codigo = f"{abrev}{(total_tipo+1):04d}"
    while Peca.query.filter_by(codigo=codigo).first():
        total_tipo += 1
        codigo = f"{abrev}{total_tipo:04d}"

    foto_path = None
    if tipo == "Vestido":
        cor    = request.form.get("cor", "").strip()
        modelo = request.form.get("modelo", "").strip()

        # Upload de foto
        arquivo = request.files.get("foto")
        if arquivo and arquivo.filename and extensao_permitida(arquivo.filename):
            nome_arquivo = secure_filename(f"{codigo}_{arquivo.filename}")
            caminho = os.path.join(pasta_fotos(), nome_arquivo)
            arquivo.save(caminho)
            foto_path = f"fotos_vestidos/{nome_arquivo}"

        peca = Peca(
            codigo=codigo, tipo=tipo, cor=cor, modelo=modelo,
            foto_path=foto_path, preco_aluguel=0.0, status="disponivel"
        )
    else:
        # Acessório: só nome/descrição
        descricao = request.form.get("descricao", "").strip()
        peca = Peca(
            codigo=codigo, tipo=tipo,
            descricao=descricao,
            preco_aluguel=0.0, status="disponivel"
        )

    db.session.add(peca)
    db.session.commit()
    flash(f"{'Vestido' if tipo == 'Vestido' else 'Acessório'} {peca.codigo} cadastrado com sucesso!", "success")
    return redirect(url_for("estoque.index", tipo=tipo))


@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
def editar(id):
    peca = Peca.query.get_or_404(id)
    if request.method == "POST":
        if peca.tipo == "Vestido":
            peca.cor    = request.form.get("cor", "").strip()
            peca.modelo = request.form.get("modelo", "").strip()

            # Troca de foto
            arquivo = request.files.get("foto")
            if arquivo and arquivo.filename and extensao_permitida(arquivo.filename):
                # Remove foto antiga se existir
                if peca.foto_path:
                    antiga = os.path.join(current_app.static_folder, peca.foto_path)
                    if os.path.exists(antiga):
                        os.remove(antiga)
                nome_arquivo = secure_filename(f"{peca.codigo}_{arquivo.filename}")
                caminho = os.path.join(pasta_fotos(), nome_arquivo)
                arquivo.save(caminho)
                peca.foto_path = f"fotos_vestidos/{nome_arquivo}"
        else:
            peca.descricao = request.form.get("descricao", "").strip()

        peca.status = request.form.get("status", "disponivel")
        db.session.commit()
        flash("Peça atualizada!", "success")
        return redirect(url_for("estoque.index", tipo=peca.tipo))

    return render_template("estoque_form.html", peca=peca, tipos=TIPOS, status_opts=STATUS)


@bp.route("/<int:id>/excluir", methods=["POST"])
@login_required
def excluir(id):
    peca = Peca.query.get_or_404(id)
    tipo = peca.tipo
    # Remove foto se existir
    if peca.foto_path:
        caminho = os.path.join(current_app.static_folder, peca.foto_path)
        if os.path.exists(caminho):
            os.remove(caminho)
    db.session.delete(peca)
    db.session.commit()
    flash("Peça removida.", "warning")
    return redirect(url_for("estoque.index", tipo=tipo))


@bp.route("/disponibilidade")
@login_required
def disponibilidade():
    inicio = request.args.get("inicio")
    fim    = request.args.get("fim")
    if not inicio or not fim:
        return jsonify([])
    dt_inicio = datetime.strptime(inicio, "%Y-%m-%d").date()
    dt_fim    = datetime.strptime(fim,    "%Y-%m-%d").date()

    pecas = Peca.query.filter(Peca.status.in_(["disponivel", "alugada"])).all()
    resultado = []
    for p in pecas:
        livre = p.disponivel_no_periodo(dt_inicio, dt_fim)
        resultado.append({
            "id": p.id, "codigo": p.codigo, "tipo": p.tipo,
            "cor": p.cor or "", "modelo": p.modelo or "",
            "descricao": p.descricao or "",
            "foto_path": p.foto_path or "",
            "preco": p.preco_aluguel, "livre": livre
        })
    return jsonify(resultado)
