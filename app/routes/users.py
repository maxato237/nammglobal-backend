from flask import Blueprint, request as req
from app import db
from app.models import User
from app.services.audit_service import AuditService
from app.utils import success, not_found, error, admin_required, current_user

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.route("", methods=["GET"])
@admin_required
def list_users():
    role = req.args.get("role", "client")   # "client" | "admin"
    users = (
        User.query
        .filter_by(role=role, is_active=True)
        .order_by(User.created_at.desc())
        .all()
    )
    return success([u.to_dict() for u in users])


@users_bp.route("/<int:user_id>", methods=["GET"])
@admin_required
def get_user(user_id):
    u = User.query.get(user_id)
    if not u:
        return not_found("Utilisateur introuvable.")
    return success(u.to_dict())


@users_bp.route("/<int:user_id>/deactivate", methods=["PATCH"])
@admin_required
def deactivate_user(user_id):
    u = User.query.get(user_id)
    if not u:
        return not_found("Utilisateur introuvable.")
    if u.is_admin:
        return error("Impossible de désactiver un administrateur.", 403)
    u.is_active = False
    db.session.commit()
    AuditService.log("User", "deactivate", entity_id=u.id, actor=current_user())
    return success(message="Compte désactivé.")


@users_bp.route("/<int:user_id>/reactivate", methods=["PATCH"])
@admin_required
def reactivate_user(user_id):
    u = User.query.get(user_id)
    if not u:
        return not_found("Utilisateur introuvable.")
    u.is_active = True
    db.session.commit()
    AuditService.log("User", "reactivate", entity_id=u.id, actor=current_user())
    return success(message="Compte réactivé.")
