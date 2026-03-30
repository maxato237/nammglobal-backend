from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt,
)
from app import db
from app.models import User
from app.utils import (
    success, created, error, validate_password,
    login_required, current_user,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Blacklist en mémoire (remplacer par Redis en production)
_blacklist: set = set()


def is_token_revoked(jwt_header, jwt_payload) -> bool:
    return jwt_payload.get("jti", "") in _blacklist

# ── POST /api/auth/register ───────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data     = request.get_json(silent=True) or {}
    name     = (data.get("name") or "").strip()
    phone    = (data.get("phone") or "").strip()
    password = data.get("password") or ""
    email    = (data.get("email") or "").strip() or None
    whatsapp = (data.get("whatsapp") or "").strip() or None
    country  = (data.get("country") or "").strip() or None
    city     = (data.get("city") or "").strip() or None

    if not name or not phone or not password:
        return error("Nom complet, téléphone et mot de passe sont obligatoires.")
    ok, msg = validate_password(password)
    if not ok:
        return error(msg)
    if User.query.filter_by(phone=phone).first():
        return error("Ce numéro est déjà associé à un compte.", 409)
    if email and User.query.filter_by(email=email).first():
        return error("Cet email est déjà utilisé.", 409)

    user = User(
        full_name=name, phone=phone, email=email,
        whatsapp=whatsapp, country=country, city=city,
        role="client",
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return created({**user.to_dict(), **_tokens(user)}, "Compte créé avec succès.")

# ── POST /api/auth/login ──────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data     = request.get_json(silent=True) or {}
    phone    =(data.get("phone") or "").strip()
    password = data.get("password") or ""
    remember = bool(data.get("remember", False))

    if not phone or not password:
        return error("Téléphone et mot de passe requis.")

    user = User.query.filter_by(phone=phone).first()
    if not user or not user.check_password(password):
        return error("Numéro ou mot de passe incorrect.", 401)
    if not user.is_active:
        return error("Compte désactivé. Contactez le support.", 403)

    return success(
        {**user.to_dict(), **_tokens(user, long_lived=remember)},
        "Connexion réussie.",
    )

# ── POST /api/auth/refresh ────────────────────────────────────
@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user = User.query.get(int(get_jwt_identity()))
    if not user or not user.is_active:
        return error("Session invalide.", 401)
    access = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role},
    )
    return success({"accessToken": access})

# ── POST /api/auth/logout ─────────────────────────────────────
@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    _blacklist.add(get_jwt().get("jti", ""))
    return success(message="Déconnecté avec succès.")

# ── GET /api/auth/me ──────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    return success(current_user().to_dict())

# ── PATCH /api/auth/profile ───────────────────────────────────
@auth_bp.route("/profile", methods=["PATCH"])
@login_required
def update_profile():
    data = request.get_json(silent=True) or {}
    u    = current_user()

    first = (data.get("firstName") or "").strip()
    last  = (data.get("lastName")  or "").strip()
    u.full_name = " ".join(p for p in [first, last] if p) or u.full_name
    u.email    = (data.get("email")    or u.email    or "").strip() or None
    u.whatsapp = (data.get("whatsapp") or u.whatsapp or "").strip() or None
    u.country  = (data.get("country")  or u.country  or "").strip() or None
    u.city     = (data.get("city")     or u.city     or "").strip() or None

    new_pass = (data.get("newPassword") or "").strip()
    if new_pass:
        ok, msg = validate_password(new_pass)
        if not ok:
            return error(msg)
        u.set_password(new_pass)

    db.session.commit()
    return success(u.to_dict(), "Profil mis à jour.")

# ── POST /api/auth/admin/setup ────────────────────────────────
@auth_bp.route("/admin/setup", methods=["POST"])
def admin_setup():
    """Crée le premier compte admin. Bloqué si un admin existe déjà."""
    if User.query.filter_by(role="admin", is_active=True).first():
        return error("Un compte administrateur existe déjà.", 409)

    data     = request.get_json(silent=True) or {}
    name     = (data.get("name") or data.get("fullName") or "").strip()
    phone    = (data.get("phone") or "").strip()
    password = data.get("password") or ""

    if not name or not phone or not password:
        return error("Nom, téléphone et mot de passe sont obligatoires.")
    ok, msg = validate_password(password)
    if not ok:
        return error(msg)

    if User.query.filter_by(phone=phone).first():
        return error("Ce numéro est déjà utilisé.", 409)

    admin = User(full_name=name, phone=phone, role="admin")
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()

    return created({**admin.to_dict(), **_tokens(admin)}, "Compte admin créé.")

# ── POST /api/auth/admin/login ────────────────────────────────
@auth_bp.route("/admin/login", methods=["POST"])
def admin_login():
    """Connexion administrateur par téléphone et mot de passe."""
    data     = request.get_json(silent=True) or {}
    phone    = (data.get("phone") or "").strip()
    password = data.get("password") or ""

    if not phone or not password:
        return error("Téléphone et mot de passe sont obligatoires.")

    admin = User.query.filter_by(phone=phone, role="admin", is_active=True).first()

    if not admin or not admin.check_password(password):
        return error("Identifiants incorrects.", 401)

    return success({**admin.to_dict(), **_tokens(admin)}, "Connexion réussie.")

# ── GET /api/auth/admin/exists ────────────────────────────────
@auth_bp.route("/admin/exists", methods=["GET"])
def admin_exists():
    exists = User.query.filter_by(role="admin", is_active=True).first() is not None
    return success({"exists": exists})

# ── Helper privé ──────────────────────────────────────────────
def _tokens(user: User, long_lived: bool = False) -> dict:
    from datetime import timedelta
    extra = timedelta(days=30) if long_lived else None
    return {
        "accessToken": create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.role},
        ),
        "refreshToken": create_refresh_token(
            identity=str(user.id),
            additional_claims={"role": user.role},
            expires_delta=extra,
        ),
    }
