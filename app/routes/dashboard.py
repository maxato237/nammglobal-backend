from flask import Blueprint
from app.utils import success
from app.utils.auth_decorators import login_required, current_user
from app.models import Request, Order, Quotation, Notification, Wave

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/v1/me")


@dashboard_bp.route("/dashboard", methods=["GET"])
@login_required
def client_dashboard():
    """Bundle client agrégé en 1 appel."""
    u = current_user()

    orders = Order.query.filter_by(user_id=u.id).all()
    order_counts = {}
    for o in orders:
        order_counts[o.status] = order_counts.get(o.status, 0) + 1

    recent_requests = (
        Request.query.filter_by(user_id=u.id)
        .order_by(Request.created_at.desc())
        .limit(5)
        .all()
    )

    pending_quotations = (
        Quotation.query
        .join(Request, Quotation.request_id == Request.id)
        .filter(Request.user_id == u.id, Quotation.status == "sent")
        .order_by(Quotation.sent_at.desc())
        .limit(5)
        .all()
    )

    active_orders = (
        Order.query
        .filter(Order.user_id == u.id, Order.status.notin_(["delivered", "cancelled"]))
        .order_by(Order.created_at.desc())
        .limit(5)
        .all()
    )

    notifications = (
        Notification.query
        .filter_by(user_id=u.id, is_read=False)
        .order_by(Notification.created_at.desc())
        .limit(10)
        .all()
    )

    next_wave = (
        Wave.query
        .filter_by(status="open", country_code=getattr(u, "country_code", None))
        .order_by(Wave.deadline_date)
        .first()
    )

    return success({
        "profile": u.to_dict(),
        "order_counts": order_counts,
        "recent_requests": [r.to_dict() for r in recent_requests],
        "pending_quotations": [q.to_dict() for q in pending_quotations],
        "active_orders": [o.to_dict() for o in active_orders],
        "unread_notifications": [n.to_dict() for n in notifications],
        "next_wave": next_wave.to_dict() if next_wave else None,
    })


@dashboard_bp.route("/dashboard/timeline", methods=["GET"])
@login_required
def activity_timeline():
    u = current_user()
    orders = Order.query.filter_by(user_id=u.id).order_by(Order.created_at.desc()).limit(20).all()
    requests = Request.query.filter_by(user_id=u.id).order_by(Request.created_at.desc()).limit(10).all()
    events = []
    for o in orders:
        events.append({"type": "order", "data": o.to_dict(), "date": o.created_at.isoformat() if o.created_at else None})
    for r in requests:
        events.append({"type": "request", "data": r.to_dict(), "date": r.created_at.isoformat() if r.created_at else None})
    events.sort(key=lambda x: x["date"] or "", reverse=True)
    return success(events[:20])
