from functools import wraps
from flask import g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from app.models import User
from app.utils.helpers import forbidden, not_found


def login_required(fn):
    """Route accessible aux utilisateurs connectés (client OU admin)."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:
            return forbidden("Authentification requise.")

        user = User.query.get_or_404(int(get_jwt_identity()))
        if not user or not user.is_active:
            return not_found("Utilisateur introuvable ou désactivé.")

        g.current_user = user
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    """Route accessible aux admins uniquement."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:
            return forbidden("Authentification admin requise.")

        claims = get_jwt()
        if claims.get("role") != "admin":
            return forbidden("Accès réservé à l'administrateur.")

        user = User.query.get(int(get_jwt_identity()))
        if not user or not user.is_active or not user.is_admin:
            return not_found("Administrateur introuvable.")

        g.current_user = user
        return fn(*args, **kwargs)
    return wrapper


def current_user() -> User | None:
    return getattr(g, "current_user", None)
