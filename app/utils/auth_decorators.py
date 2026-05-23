from functools import wraps
from flask import g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from app.models import User
from app.utils.helpers import forbidden, not_found


def login_required(fn):
    """Route accessible aux utilisateurs connectés (client OU admin)."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from app.utils.helpers import error as err
        try:
            verify_jwt_in_request()
        except Exception:
            return err("Authentification requise.", 401)

        user = User.query.get(int(get_jwt_identity()))
        if not user or not user.is_active:
            return err("Utilisateur introuvable ou désactivé.", 401)

        g.current_user = user
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    """Route accessible aux opérateurs et super_admins uniquement."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from app.utils.helpers import error as err
        try:
            verify_jwt_in_request()
        except Exception:
            return err("Authentification requise.", 401)

        user = User.query.get(int(get_jwt_identity()))
        if not user or not user.is_active:
            return err("Utilisateur introuvable.", 401)
        if not user.is_admin:
            return forbidden("Accès réservé aux administrateurs.")

        g.current_user = user
        return fn(*args, **kwargs)
    return wrapper


def current_user() -> User | None:
    return getattr(g, "current_user", None)
