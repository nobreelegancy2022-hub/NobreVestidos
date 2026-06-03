from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from backend.app import db
from backend.models.peca import Peca
from backend.models.contrato import Contrato
from backend.models.cliente import Cliente

bp = Blueprint("consultas", __name__, url_prefix="/consultas")

@bp.route("/")
@login_required
def index():
    return render_template("consultas.html")

@bp.route("/buscar")
@login_required
def buscar():
    termo = request.args.get("q", "").strip()
    tipo  = request.args.get("tipo", "tudo")  # tudo | pecas | contratos | clientes

    if not termo:
        return jsonify({"pecas": [], "contratos": [], "clientes": []})

    resultado = {"pecas": [], "contratos": [], "clientes": []}

    # ── Peças ─────────────────────────────────────────────────
    if tipo in ("tudo", "pecas"):
        pecas = Peca.query.filter(db.or_(
            Peca.codigo.ilike(f"%{termo}%"),
            Peca.cor.ilike(f"%{termo}%"),
            Peca.modelo.ilike(f"%{termo}%"),
            Peca.tamanho.ilike(f"%{termo}%"),
            Peca.tipo.ilike(f"%{termo}%"),
        )).order_by(Peca.tipo, Peca.tamanho).limit(30).all()

        resultado["pecas"] = [{
            "codigo":  p.codigo,
            "tipo":    p.tipo,
            "cor":     p.cor or "—",
            "modelo":  p.modelo or "—",
            "tamanho": p.tamanho or "—",
            "status":  p.status,
        } for p in pecas]

    # ── Contratos ─────────────────────────────────────────────
    if tipo in ("tudo", "contratos"):
        contratos = Contrato.query.join(Cliente).filter(db.or_(
            Cliente.nome.ilike(f"%{termo}%"),
            Cliente.cpf.ilike(f"%{termo}%"),
            Cliente.telefone.ilike(f"%{termo}%"),
        )).order_by(Contrato.criado_em.desc()).limit(20).all()

        resultado["contratos"] = [{
            "id":         f"{c.id:04d}",
            "cliente":    c.cliente.nome,
            "retirada":   c.data_retirada.strftime("%d/%m/%Y"),
            "devolucao":  c.data_devolucao.strftime("%d/%m/%Y"),
            "valor":      f"R$ {c.valor_total:,.2f}".replace(",","X").replace(".",",").replace("X","."),
            "status":     c.status,
            "pecas":      " / ".join(
                " - ".join(filter(None,[i.peca.cor, i.peca.modelo, i.peca.tamanho]))
                for i in c.itens
            ),
        } for c in contratos]

    # ── Clientes ──────────────────────────────────────────────
    if tipo in ("tudo", "clientes"):
        clientes = Cliente.query.filter(db.or_(
            Cliente.nome.ilike(f"%{termo}%"),
            Cliente.cpf.ilike(f"%{termo}%"),
            Cliente.telefone.ilike(f"%{termo}%"),
            Cliente.email.ilike(f"%{termo}%"),
        )).order_by(Cliente.nome).limit(20).all()

        resultado["clientes"] = [{
            "id":        c.id,
            "nome":      c.nome,
            "cpf":       c.cpf or "—",
            "telefone":  c.telefone or "—",
            "contratos": len(c.contratos),
        } for c in clientes]

    return jsonify(resultado)
