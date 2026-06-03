from flask import Blueprint, render_template, redirect, url_for, Response
from flask_login import login_required, current_user
from datetime import date

bp = Blueprint("pwa", __name__)

@bp.route("/app")
def app_view():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login_app"))
    return render_template("pwa/app.html", hoje=date.today().isoformat())

@bp.route("/manifest.json")
def manifest():
    from flask import jsonify
    return jsonify({
        "name": "Espaço D Luxo",
        "short_name": "D Luxo",
        "description": "Sistema de aluguel de trajes — Novo Contrato",
        "start_url": "/app",
        "display": "standalone",
        "background_color": "#0a0f1a",
        "theme_color": "#1a3a5c",
        "orientation": "portrait",
        "icons": [
            {"src": "/assets/icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "/assets/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}
        ]
    })

@bp.route("/sw.js")
def service_worker():
    sw = "self.addEventListener('fetch', e => e.respondWith(fetch(e.request)));"
    return Response(sw, mimetype="application/javascript")
