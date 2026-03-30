from flask import Blueprint, request as req
from app import db
from app.models import Notification
from app.utils import success, not_found, login_required, current_user

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")

@notifications_bp.route("", methods=["GET"])
@login_required
def list_notifications():
    user        = current_user()
    unread_only = req.args.get("unread") == "1"
    q = Notification.query.filter_by(user_id=user.id)
    if unread_only: q = q.filter_by(is_read=False)
    notifs = q.order_by(Notification.created_at.desc()).limit(50).all()
    unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return success({"items": [n.to_dict() for n in notifs], "unreadCount": unread_count})

@notifications_bp.route("/<int:notif_id>/read", methods=["PATCH"])
@login_required
def mark_read(notif_id):
    n = Notification.query.filter_by(id=notif_id, user_id=current_user().id).first()
    if not n: return not_found("Notification introuvable.")
    n.is_read = True; db.session.commit()
    return success(n.to_dict())

@notifications_bp.route("/read-all", methods=["PATCH"])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user().id, is_read=False).update({"is_read": True})
    db.session.commit(); return success(message="Toutes les notifications marquées comme lues.")

@notifications_bp.route("/<int:notif_id>", methods=["DELETE"])
@login_required
def delete_notification(notif_id):
    n = Notification.query.filter_by(id=notif_id, user_id=current_user().id).first()
    if not n: return not_found("Notification introuvable.")
    db.session.delete(n); db.session.commit()
    return success(message="Notification supprimée.")
