from flask import Blueprint, request
from app.extensions import db
from app.models import ContactMessage, ContactReply
from app.utils import success, created, error, not_found
from app.utils.auth_decorators import login_required, admin_required, current_user

contact_bp = Blueprint("contact", __name__, url_prefix="/api/v1/contact")


@contact_bp.route("/messages", methods=["POST"])
def submit_message():
    data = request.get_json(silent=True) or {}
    if not data.get("first_name") or not data.get("message") or not data.get("subject"):
        return error("Prénom, sujet et message sont requis.")
    msg = ContactMessage(
        first_name=data["first_name"],
        last_name=data.get("last_name"),
        email=data.get("email"),
        whatsapp=data.get("whatsapp"),
        country_code=data.get("country_code"),
        subject=data["subject"],
        order_id=data.get("order_id"),
        company_name=data.get("company_name"),
        message=data["message"],
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent"),
    )
    db.session.add(msg)
    db.session.commit()
    return created(msg.to_dict(), "Message envoyé.")


@contact_bp.route("/messages", methods=["GET"])
@admin_required
def list_messages():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status = request.args.get("status")
    q = ContactMessage.query
    if status:
        q = q.filter_by(status=status)
    paginated = q.order_by(ContactMessage.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return success({
        "items": [m.to_dict() for m in paginated.items],
        "total": paginated.total,
        "page": paginated.page,
        "pages": paginated.pages,
    })


@contact_bp.route("/messages/<int:msg_id>", methods=["GET"])
@admin_required
def get_message(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    data = msg.to_dict()
    data["replies"] = [r.to_dict() for r in msg.replies.all()]
    return success(data)


@contact_bp.route("/messages/<int:msg_id>/status", methods=["PATCH"])
@admin_required
def update_status(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in ("new", "read", "in_progress", "resolved"):
        return error("Statut invalide.")
    msg.status = status
    if status == "resolved":
        from datetime import datetime
        msg.resolved_at = datetime.utcnow()
    db.session.commit()
    return success(msg.to_dict(), "Statut mis à jour.")


@contact_bp.route("/messages/<int:msg_id>/replies", methods=["POST"])
@admin_required
def reply_to_message(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    data = request.get_json(silent=True) or {}
    if not data.get("content"):
        return error("Le contenu de la réponse est requis.")
    u = current_user()
    reply = ContactReply(
        message_id=msg_id,
        admin_user_id=u.id,
        content=data["content"],
        sent_via=data.get("sent_via", "internal"),
    )
    db.session.add(reply)
    if msg.status == "new":
        msg.status = "in_progress"
    db.session.commit()
    return created(reply.to_dict(), "Réponse envoyée.")


@contact_bp.route("/messages/<int:msg_id>/assign", methods=["POST"])
@admin_required
def assign_message(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    data = request.get_json(silent=True) or {}
    msg.assigned_admin_id = data.get("admin_id")
    db.session.commit()
    return success(msg.to_dict(), "Message assigné.")
