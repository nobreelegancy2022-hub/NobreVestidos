from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, make_response
from flask_login import login_required, current_user
from backend.app import db
from backend.models.contrato import Contrato, ContratoItem, Pagamento
from backend.models.cliente import Cliente
from backend.models.peca import Peca
from backend.services.pdf_service import gerar_contrato_pdf, nome_arquivo_contrato
from datetime import datetime, date
import io



def _link_lembrete_retirada(contrato):
    """Retorna (link_whatsapp, horario) para lembrete de retirada."""
    import urllib.parse
    if not contrato.cliente.telefone:
        return None, None
    tel = contrato.cliente.telefone
    for ch in ["(",")"," ","-"]: tel = tel.replace(ch, "")
    horario = getattr(contrato, 'horario_saida', None)
    saida = contrato.data_retirada.strftime("%d/%m/%Y")
    if horario:
        saida += f" às {horario}"
    nome = contrato.cliente.nome
    pecas = " / ".join(
        " ".join(filter(None, [i.peca.cor, i.peca.modelo]))
        for i in contrato.itens
    )
    msg = (f"Olá, {nome}! 😊\n\n"
           f"Passando para lembrar que o seu vestido está agendado para retirada em:\n"
           f"📅 *{saida}*\n\n"
           f"👗 *Peças:* {pecas}\n\n"
           f"Qualquer dúvida estamos à disposição! 💕\n"
           f"_Equipe Nobre Vestidos_ 🌸")
    link = f"https://wa.me/55{tel}?text={urllib.parse.quote(msg)}"
    return link, horario

bp = Blueprint("contratos", __name__, url_prefix="/contratos")

@bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    if request.method == "POST":
        pecas_ids = request.form.getlist("pecas_ids")
        dt_retirada = datetime.strptime(request.form["data_retirada"], "%Y-%m-%d").date()
        dt_devolucao = datetime.strptime(request.form["data_devolucao"], "%Y-%m-%d").date()

        if dt_retirada < date.today():
            flash("A data de saída não pode ser anterior à data de hoje.", "danger")
            return redirect(url_for("contratos.novo"))

        if dt_devolucao <= dt_retirada:
            flash("A data de devolução deve ser após a retirada.", "danger")
            return redirect(url_for("contratos.novo"))

        # Cliente: usa existente ou cria novo
        cliente_id = request.form.get("cliente_id", "").strip()
        if cliente_id:
            cliente = Cliente.query.get(int(cliente_id))
            # Atualiza dados se vieram preenchidos
            nome = request.form.get("cliente_nome", "").strip()
            if nome:
                cliente.nome = nome
            tel = request.form.get("cliente_telefone", "").strip()
            if tel:
                cliente.telefone = tel
        else:
            # Cria novo cliente
            nome = request.form.get("cliente_nome", "").strip()
            if not nome:
                flash("Informe o nome do cliente.", "danger")
                return redirect(url_for("contratos.novo"))
            cliente = Cliente(
                nome=nome,
                cpf=request.form.get("cliente_cpf", "").strip(),
                telefone=request.form.get("cliente_telefone", "").strip(),
                endereco=request.form.get("cliente_endereco", "").strip(),
            )
            db.session.add(cliente)
            db.session.flush()

        # Medidas e observações no campo observacoes
        medidas = []
        if request.form.get("medida_cor"):
            medidas.append(f"Cor: {request.form['medida_cor']}")
        if request.form.get("medida_modelo"):
            medidas.append(f"Modelo: {request.form['medida_modelo']}")
        if request.form.get("medida_busto"):
            medidas.append(f"Busto: {request.form['medida_busto']}cm")
        if request.form.get("medida_cintura"):
            medidas.append(f"Cintura: {request.form['medida_cintura']}cm")
        if request.form.get("medida_barra"):
            medidas.append(f"Barra: {request.form['medida_barra']}cm")
        if request.form.get("medida_alca"):
            medidas.append(f"Alça: {request.form['medida_alca']}cm")
        if request.form.get("medida_obs"):
            medidas.append(f"Obs: {request.form['medida_obs']}")

        obs_geral = request.form.get("observacoes", "").strip()
        obs_completa = "\n".join(medidas)
        if obs_geral:
            obs_completa = obs_completa + ("\n" if obs_completa else "") + obs_geral

        valor_sinal = float(request.form.get("valor_sinal") or 0)
        valor_total_manual = request.form.get("valor_total_manual", "").strip()

        contrato = Contrato(
            cliente_id=cliente.id,
            usuario_id=current_user.id,
            data_retirada=dt_retirada,
            data_devolucao=dt_devolucao,
            valor_sinal=valor_sinal,
            observacoes=obs_completa
        )
        db.session.add(contrato)
        db.session.flush()

        # Adiciona peças
        valor_total = 0
        for pid in pecas_ids:
            peca = Peca.query.get(int(pid))
            if peca:
                item = ContratoItem(
                    contrato_id=contrato.id,
                    peca_id=peca.id,
                    preco_cobrado=peca.preco_aluguel
                )
                db.session.add(item)
                peca.status = "alugada"
                valor_total += peca.preco_aluguel

        # Valor total: manual tem prioridade
        if valor_total_manual:
            contrato.valor_total = float(valor_total_manual)
        else:
            contrato.valor_total = valor_total

        contrato.valor_pago = valor_sinal

        # Registra sinal como pagamento
        if valor_sinal > 0:
            pg = Pagamento(
                contrato_id=contrato.id,
                valor=valor_sinal,
                tipo="sinal",
                forma=request.form.get("forma_pagamento", "dinheiro"),
                observacao="Sinal no fechamento do contrato"
            )
            db.session.add(pg)

        db.session.commit()

        acao = request.form.get("acao", "salvar")

        # Salvar e gerar PDF direto
        if acao == "salvar_pdf":
            buffer = gerar_contrato_pdf(contrato)
            flash(f"Contrato #{contrato.id:04d} criado!", "success")
            response = make_response(send_file(
                buffer, mimetype="application/pdf",
                download_name=nome_arquivo_contrato(contrato),
                as_attachment=False
            ))
            return response

        flash(f"Contrato #{contrato.id:04d} criado! Preencha um novo contrato abaixo.", "success")
        return redirect(url_for("contratos.novo"))

    clientes = Cliente.query.order_by(Cliente.nome).all()
    return render_template("contrato_novo.html", clientes=clientes, hoje=date.today().isoformat())


@bp.route("/")
@login_required
def lista():
    status = request.args.get("status", "")
    busca = request.args.get("busca", "")

    ativos = Contrato.query.filter_by(status="ativo").all()
    for c in ativos:
        c.atualizar_status()
    db.session.commit()

    q = Contrato.query.join(Cliente)
    if status:
        q = q.filter(Contrato.status == status)
    if busca:
        q = q.filter(Cliente.nome.ilike(f"%{busca}%"))
    contratos = q.order_by(Contrato.criado_em.desc()).all()

    return render_template("contratos_lista.html", contratos=contratos,
                           filtro_status=status, busca=busca)


@bp.route("/<int:id>")
@login_required
def detalhe(id):
    contrato = Contrato.query.get_or_404(id)
    contrato.atualizar_status()
    db.session.commit()
    return render_template("contrato_detalhe.html", contrato=contrato)


@bp.route("/<int:id>/pagar", methods=["POST"])
@login_required
def pagar(id):
    contrato = Contrato.query.get_or_404(id)
    valor = float(request.form.get("valor", 0))
    if valor > 0:
        pg = Pagamento(
            contrato_id=contrato.id,
            valor=valor,
            tipo=request.form.get("tipo", "complemento"),
            forma=request.form.get("forma", "dinheiro"),
            observacao=request.form.get("observacao", "")
        )
        db.session.add(pg)
        contrato.valor_pago = round(contrato.valor_pago + valor, 2)
        db.session.commit()
        flash("Pagamento registrado!", "success")
    return redirect(url_for("contratos.detalhe", id=id))


@bp.route("/<int:id>/devolver", methods=["POST"])
@login_required
def devolver(id):
    contrato = Contrato.query.get_or_404(id)
    contrato.status = "devolvido"
    contrato.data_devolucao_real = date.today()
    for item in contrato.itens:
        item.peca.status = "disponivel"
    db.session.commit()
    flash("Devolução registrada! Peças liberadas no estoque.", "success")
    return redirect(url_for("contratos.detalhe", id=id))


@bp.route("/<int:id>/cancelar", methods=["POST"])
@login_required
def cancelar(id):
    contrato = Contrato.query.get_or_404(id)
    contrato.status = "cancelado"
    for item in contrato.itens:
        item.peca.status = "disponivel"
    db.session.commit()
    flash("Contrato cancelado.", "warning")
    return redirect(url_for("contratos.lista"))


@bp.route("/<int:id>/excluir", methods=["POST"])
@login_required
def excluir(id):
    contrato = Contrato.query.get_or_404(id)
    for item in contrato.itens:
        if contrato.status in ["ativo", "atrasado"]:
            item.peca.status = "disponivel"
    db.session.delete(contrato)
    db.session.commit()
    flash(f"Contrato #{id:04d} excluído.", "warning")
    return redirect(url_for("contratos.lista"))


@bp.route("/<int:id>/status", methods=["POST"])
@login_required
def alterar_status(id):
    contrato = Contrato.query.get_or_404(id)
    novo_status = request.form.get("status", "")
    status_validos = ["ativo", "atrasado", "devolvido", "cancelado"]
    if novo_status in status_validos:
        # Se mudando para devolvido, libera peças
        if novo_status == "devolvido" and contrato.status != "devolvido":
            from datetime import date
            contrato.data_devolucao_real = date.today()
            for item in contrato.itens:
                item.peca.status = "disponivel"
        # Se saindo de devolvido, volta peças para alugada
        elif novo_status != "devolvido" and contrato.status == "devolvido":
            for item in contrato.itens:
                item.peca.status = "alugada"
        contrato.status = novo_status
        db.session.commit()
        flash(f"Status atualizado para {novo_status.capitalize()}!", "success")
        # Se devolvido e tem telefone, monta link WhatsApp
        if novo_status == "devolvido" and contrato.cliente.telefone:
            tel = contrato.cliente.telefone
            for ch in ["(",")"," ","-"]: tel = tel.replace(ch, "")
            nome = contrato.cliente.nome
            msg = (f"Olá, {nome}! 😊\n\n"
                   f"Obrigada por escolher a *Nobre Vestidos*! 💕\n"
                   f"Foi um prazer atendê-la. Esperamos que tenha arrasado no visual! 👗✨\n\n"
                   f"Qualquer dúvida ou para um próximo aluguel, estamos sempre à disposição!\n\n"
                   f"_Equipe Nobre Vestidos_ 🌸")
            import urllib.parse
            wa_link = f"https://wa.me/55{tel}?text={urllib.parse.quote(msg)}"
            return redirect(url_for("contratos.lista", wa_link=urllib.parse.quote(wa_link, safe="")))
    return redirect(url_for("contratos.lista"))





@bp.route("/<int:id>/ajuste", methods=["POST"])
@login_required
def toggle_ajuste(id):
    from flask import jsonify
    contrato = Contrato.query.get_or_404(id)
    contrato.ajuste_pronto = not contrato.ajuste_pronto
    db.session.commit()
    return jsonify({"ajuste_pronto": contrato.ajuste_pronto})

@bp.route("/<int:id>/whatsapp")
@login_required
def whatsapp(id):
    from flask import jsonify
    import urllib.parse
    contrato = Contrato.query.get_or_404(id)
    if not contrato.cliente.telefone:
        return jsonify({"link": None})
    tel = contrato.cliente.telefone
    for ch in ["(",")"," ","-"]: tel = tel.replace(ch, "")
    pecas = " / ".join(
        " ".join(filter(None, [i.peca.cor, i.peca.modelo]))
        for i in contrato.itens
    )
    nome = contrato.cliente.nome
    saida = contrato.data_retirada.strftime("%d/%m/%Y")
    devolucao = contrato.data_devolucao.strftime("%d/%m/%Y") if contrato.data_devolucao else "-"
    total = f"R$ {contrato.valor_total:.2f}"
    sinal = f"R$ {contrato.valor_pago:.2f}"
    saldo = f"R$ {contrato.saldo_restante:.2f}"
    msg = (f"Olá, {nome}! 😊\n"
           f"Confirmando seu aluguel na *Nobre Vestidos*:\n\n"
           f"📅 *Saída:* {saida}\n"
           f"📅 *Devolução:* {devolucao}\n"
           f"👗 *Peças:* {pecas}\n\n"
           f"💰 *Total:* {total} | *Sinal:* {sinal} | *Saldo:* {saldo}\n\n"
           f"Qualquer dúvida estamos à disposição! 💕")
    link = f"https://wa.me/55{tel}?text={urllib.parse.quote(msg)}"
    return jsonify({"link": link})

@bp.route("/<int:id>/pdf")
@login_required
def pdf(id):
    contrato = Contrato.query.get_or_404(id)
    buffer = gerar_contrato_pdf(contrato)
    return send_file(buffer, mimetype="application/pdf",
                     download_name=nome_arquivo_contrato(contrato),
                     as_attachment=False)
