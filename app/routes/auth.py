from datetime import datetime
from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token, decode_token,
    jwt_required, get_jwt_identity, get_jwt,
)
from app import db
from app.models import User
from app.utils import (
    success, created, error, validate_password,
    login_required, current_user,
)
from app.constants import Messages as m

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def is_token_revoked(jwt_header, jwt_payload) -> bool:  #NOSONAR
    from app.services.auth_service import AuthService
    return AuthService.is_token_blacklisted(jwt_payload.get("jti", ""))

# ── POST /api/auth/register ───────────────────────────────────

@auth_bp.route("/register", methods=["POST"])
def register(): #NOSONAR
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
        whatsapp=whatsapp, country_code=country, city=city,
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
    import hashlib
    from app.services.auth_service import AuthService

    # Blacklister l'access token en DB
    jwt_data = get_jwt()
    expires_at = datetime.utcfromtimestamp(jwt_data["exp"])
    AuthService.blacklist_token(jwt_data.get("jti", ""), expires_at)

    # Révoquer le refresh token si fourni dans le body
    data = request.get_json(silent=True) or {}
    raw_refresh = data.get("refreshToken")
    if raw_refresh:
        try:
            decoded = decode_token(raw_refresh)
            refresh_expires = datetime.utcfromtimestamp(decoded["exp"])
            AuthService.blacklist_token(decoded.get("jti", ""), refresh_expires)
            token_hash = hashlib.sha256(raw_refresh.encode()).hexdigest()
            AuthService.revoke_refresh_token(token_hash)
        except Exception:
            pass

    return success(message="Déconnecté avec succès.")

# ── GET /api/auth/me ──────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    token = get_jwt_identity()
    user = User.query.get(int(token))
    if not user or not user.is_active:
        return error(m.INVALID_TOKEN, 401) 
    print("User info:", user.to_dict())  # Debug

    return success(user.to_dict())

# ── PATCH /api/auth/profile ───────────────────────────────────
@auth_bp.route("/profile", methods=["PATCH"])
@login_required
def update_profile(): #NOSONAR
    data = request.get_json(silent=True) or {}
    u    = current_user()

    first = (data.get("firstName") or "").strip()
    last  = (data.get("lastName")  or "").strip()
    u.full_name = " ".join(p for p in [first, last] if p) or u.full_name
    u.email    = (data.get("email")    or u.email    or "").strip() or None
    u.whatsapp     = (data.get("whatsapp")    or u.whatsapp     or "").strip() or None
    u.country_code = (data.get("countryCode") or u.country_code or "").strip() or None
    u.city         = (data.get("city")        or u.city         or "").strip() or None

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
    if User.query.filter_by(role="super_admin", is_active=True).first():
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

    admin = User(full_name=name, phone=phone, role="super_admin")
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

    admin = User.query.filter_by(phone=phone, role="super_admin", is_active=True).first()

    if not admin or not admin.check_password(password):
        return error("Identifiants incorrects.", 401)

    return success({**admin.to_dict(), **_tokens(admin)}, "Connexion réussie.")

# ── GET /api/auth/admin/exists ────────────────────────────────
@auth_bp.route("/admin/exists", methods=["GET"])
def admin_exists():
    exists = User.query.filter_by(role="super_admin", is_active=True).first() is not None
    return success({"exists": exists})


# ── GET /api/auth/verify ──────────────────────────────────────
@auth_bp.route("/verify", methods=["GET"])
@jwt_required()
def verify_token():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return error(m.INVALID_TOKEN, 401)

    user = db.session.get(User, user_id)
    if not user or not user.is_active:
        return error(m.INVALID_TOKEN, 401)

    return success({"valid": True, "user": user.to_dict()})

# ── POST /api/auth/password/reset/request ─────────────────────
@auth_bp.route("/password/reset/request", methods=["POST"])
def password_reset_request():
    """Envoie un OTP par SMS pour réinitialiser le mot de passe."""
    from app.services.otp_service import OTPService
    from app.services.sms_service import SmsService

    data     = request.get_json(silent=True) or {}
    phone    = (data.get("phone") or "").strip()
    channel  = data.get("channel", "sms")

    if not phone:
        return error("Numéro de téléphone requis.")

    user = User.query.filter_by(phone=phone, deleted_at=None).first()
    if not user:
        return success(message="Si ce numéro existe, un OTP a été envoyé.")

    otp, token = OTPService.create_reset_request(
        user_id=user.id,
        channel=channel,
        ip=request.remote_addr,
        user_agent=request.headers.get("User-Agent", ""),
    )

    import os
    if os.environ.get("DEBUG_OTP", "").lower() == "true":   
        return success({"tokenId": token.id, "otp": otp}, "OTP généré (mode debug).")

    sent = SmsService.send_otp(user.phone, otp)
    if not sent:
        return error("Échec d'envoi de l'OTP. Réessayez.", 503)

    return success({"tokenId": token.id}, "OTP envoyé.")


# ── POST /api/auth/password/reset/verify-otp ──────────────────
@auth_bp.route("/password/reset/verify-otp", methods=["POST"])
def password_reset_verify_otp():
    """Vérifie l'OTP et retourne un reset_token à usage unique."""
    from app.services.otp_service import OTPService
    from app.models.auth_token import PasswordResetToken

    data     = request.get_json(silent=True) or {}
    token_id = data.get("tokenId")
    otp_code = str(data.get("otp") or "").strip()

    token = PasswordResetToken.query.get(token_id) if token_id else None
    if not token:
        return error("Demande introuvable.", 404)

    if not OTPService.verify_otp(token, otp_code):
        return error("OTP invalide ou expiré.", 400)

    return success({"resetToken": token.reset_token}, "OTP validé.")


# ── POST /api/auth/password/reset/confirm ─────────────────────
@auth_bp.route("/password/reset/confirm", methods=["POST"])
def password_reset_confirm():
    """Applique le nouveau mot de passe via le reset_token."""
    from app.services.otp_service import OTPService

    data         = request.get_json(silent=True) or {}
    reset_token  = (data.get("resetToken") or "").strip()
    new_password = data.get("newPassword") or ""

    if not reset_token or not new_password:
        return error("resetToken et newPassword sont requis.")

    ok_pw, msg = validate_password(new_password)
    if not ok_pw:
        return error(msg)

    token = OTPService.consume_reset_token(reset_token)
    if not token:
        return error("Lien de réinitialisation invalide ou expiré.", 400)

    user = User.query.get(token.user_id)
    if not user:
        return error("Utilisateur introuvable.", 404)

    user.set_password(new_password)
    db.session.commit()

    return success(message="Mot de passe réinitialisé avec succès.")


# ── Helper privé ──────────────────────────────────────────────
def _tokens(user: User, long_lived: bool = False) -> dict:
    from datetime import timedelta
    from app.services.auth_service import AuthService

    extra = timedelta(days=30) if long_lived else timedelta(days=1)

    access = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role},
    )
    refresh = create_refresh_token(
        identity=str(user.id),
        additional_claims={"role": user.role},
        expires_delta=extra,
    )

    decoded = decode_token(refresh)
    AuthService.save_refresh_token(
        user_id=user.id,
        raw_token=refresh,
        device_label=(request.headers.get("User-Agent") or "")[:255],
        ip=request.remote_addr,
        expires_at=datetime.utcfromtimestamp(decoded["exp"]),
    )

    return {"accessToken": access, "refreshToken": refresh}


