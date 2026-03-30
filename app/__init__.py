import cloudinary
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS

db      = SQLAlchemy()
migrate = Migrate()
jwt     = JWTManager()
bcrypt  = Bcrypt()

def create_app(config=None):
    app = Flask(__name__)
    if config is None:
        from config import get_config
        config = get_config()
    app.config.from_object(config)

    CORS(app)
    db.init_app(app); migrate.init_app(app, db); jwt.init_app(app); bcrypt.init_app(app)

    from app.routes.auth import is_token_revoked

    @jwt.token_in_blocklist_loader
    def check_revoked(h, p): return is_token_revoked(h, p)

    @jwt.expired_token_loader
    def expired(h, p): return jsonify({"success":False,"message":"Token expiré."}), 401

    @jwt.invalid_token_loader
    def invalid(e): return jsonify({"success":False,"message":"Token invalide."}), 401

    @jwt.unauthorized_loader
    def missing(e): return jsonify({"success":False,"message":"Authentification requise."}), 401

    from app.routes import all_blueprints
    for bp in all_blueprints: app.register_blueprint(bp)

    @app.route("/api/health")
    def health(): return jsonify({"status":"ok","service":"NAMM GLOBAL API v2"})

    @app.errorhandler(404)
    def h404(e): return jsonify({"success":False,"message":"Route introuvable."}), 404
    @app.errorhandler(405)
    def h405(e): return jsonify({"success":False,"message":"Méthode non autorisée."}), 405
    @app.errorhandler(500)
    def h500(e): return jsonify({"success":False,"message":"Erreur serveur interne."}), 500

    with app.app_context():
        from app.models import (  # noqa
            User, Wave, Request, RequestItemImage,
            Quotation,QuotationCost,
            Order, OrderTrackingEvent, Payment,
            Supplier, SupplierOrder, SupplierOrderItem, SupplierOrderTracking,
            GalleryItem, Notification,
            ServiceFeeRule, ShippingMethod, ProductCategoryRule, Stat,
        )

        db.create_all()
    return app
