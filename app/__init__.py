import os
import cloudinary
from flask import Flask, jsonify
from flasgger import Swagger

from app.extensions import db, migrate, jwt, bcrypt, cors
from app.errors import register_error_handlers


def create_app(config=None):
    app = Flask(__name__)

    if config is None:
        from config import get_config
        config = get_config()
    app.config.from_object(config)

    # ── Extensions ────────────────────────────────────────────────────────────
    cors.init_app(app, origins=[app.config.get("FRONTEND_URL", "*")])
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)

    # ── Swagger / OpenAPI ─────────────────────────────────────────────────────
    _spec_path = os.path.join(os.path.dirname(__file__), "..", "docs", "swagger", "phase1.yaml")
    Swagger(app, template_file=os.path.abspath(_spec_path), config={
        "headers": [],
        "specs": [{"endpoint": "apispec", "route": "/api/docs/spec.json", "rule_filter": lambda rule: True, "model_filter": lambda tag: True}],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs/",
    })

    # ── Cloudinary ────────────────────────────────────────────────────────────
    cloudinary.config(
        cloud_name=app.config.get("CLOUDINARY_CLOUD_NAME"),
        api_key=app.config.get("CLOUDINARY_API_KEY"),
        api_secret=app.config.get("CLOUDINARY_API_SECRET"),
    )

    # ── JWT callbacks ─────────────────────────────────────────────────────────
    from app.routes.auth import is_token_revoked

    @jwt.token_in_blocklist_loader
    def check_revoked(h, p):
        return is_token_revoked(h, p)

    @jwt.expired_token_loader
    def expired(h, p):
        return jsonify({"success": False, "message": "Token expiré."}), 401

    @jwt.invalid_token_loader
    def invalid(e):
        return jsonify({"success": False, "message": "Token invalide."}), 401

    @jwt.unauthorized_loader
    def missing(e):
        return jsonify({"success": False, "message": "Authentification requise."}), 401

    # ── Blueprints ────────────────────────────────────────────────────────────
    from app.routes import all_blueprints
    for bp in all_blueprints:
        app.register_blueprint(bp)

    # ── Error handlers ────────────────────────────────────────────────────────
    register_error_handlers(app)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "NAMM GLOBAL API v2"})

    # ── Création des tables (dev uniquement — utiliser alembic en prod) ────────
    with app.app_context():
        from app.models import (  # noqa: F401
            User, Wave, Request, RequestItemImage,
            Quotation, QuotationCost,
            Order, OrderTrackingEvent, Payment,
            Supplier, SupplierOrder, SupplierOrderItem, SupplierOrderTracking,
            GalleryItem, Notification,
            ServiceFeeRule, ShippingMethod, ProductCategoryRule, Stat,
        )

    return app
