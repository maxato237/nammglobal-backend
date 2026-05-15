from flask import Blueprint, request
from app.utils import success
from app.utils.auth_decorators import admin_required
from app.models import Request, Order, Quotation, Payment, User, AuditLog
from app.extensions import db
from sqlalchemy import func
from datetime import datetime, timedelta

admin_bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")


@admin_bp.route("/overview", methods=["GET"])
@admin_required
def overview():
    """KPIs agrégés pour le tableau de bord admin."""
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    revenue_month = db.session.query(func.sum(Payment.amount_fcfa)).filter(
        Payment.status == "completed", Payment.paid_at >= month_start
    ).scalar() or 0

    active_orders = Order.query.filter(Order.status.notin_(["delivered", "cancelled"])).count()
    pending_requests = Request.query.filter_by(status="pending").count()
    pending_quotations = Quotation.query.filter_by(status="sent").count()
    issues_count = Order.query.filter_by(has_issue=True).count()

    recent_activity = (
        AuditLog.query
        .order_by(AuditLog.created_at.desc())
        .limit(10)
        .all()
    )

    return success({
        "kpis": {
            "revenue_month_fcfa": float(revenue_month),
            "active_orders": active_orders,
            "pending_requests": pending_requests,
            "pending_quotations": pending_quotations,
            "issues": issues_count,
        },
        "recent_activity": [a.to_dict() for a in recent_activity],
    })


@admin_bp.route("/search", methods=["GET"])
@admin_required
def global_search():
    """Recherche globale : users / requests / quotations / orders."""
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return success({"users": [], "requests": [], "orders": [], "quotations": []})

    like = f"%{q}%"
    users = User.query.filter(
        (User.full_name.ilike(like)) | (User.phone.ilike(like)) | (User.email.ilike(like))
    ).limit(5).all()

    requests_res = Request.query.filter(
        (Request.request_number.ilike(like)) | (Request.full_name.ilike(like)) | (Request.phone.ilike(like))
    ).limit(5).all()

    orders_res = Order.query.filter(Order.order_number.ilike(like)).limit(5).all()

    quotations_res = Quotation.query.filter(Quotation.quotation_number.ilike(like)).limit(5).all()

    return success({
        "users": [u.to_dict() for u in users],
        "requests": [r.to_dict() for r in requests_res],
        "orders": [o.to_dict() for o in orders_res],
        "quotations": [qt.to_dict() for qt in quotations_res],
    })


@admin_bp.route("/audit-log", methods=["GET"])
@admin_required
def audit_log():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    actor_id = request.args.get("actor_id", type=int)
    entity = request.args.get("entity")
    action = request.args.get("action")

    q = AuditLog.query
    if actor_id:
        q = q.filter_by(actor_user_id=actor_id)
    if entity:
        q = q.filter_by(entity_type=entity)
    if action:
        q = q.filter_by(action=action)

    paginated = q.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return success({
        "items": [a.to_dict() for a in paginated.items],
        "total": paginated.total,
        "page": paginated.page,
        "pages": paginated.pages,
    })


@admin_bp.route("/activity-feed", methods=["GET"])
@admin_required
def activity_feed():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    paginated = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return success({
        "items": [a.to_dict() for a in paginated.items],
        "total": paginated.total,
        "page": paginated.page,
        "pages": paginated.pages,
    })
