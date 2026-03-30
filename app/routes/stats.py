from flask import Blueprint
from sqlalchemy import func
from app import db
from app.models import Order, OrderStatus, User, GalleryItem, Request, RequestStatus, Stat
from app.utils import success, admin_required

stats_bp = Blueprint("stats", __name__, url_prefix="/api/stats")


# ── GET /api/stats  (public – homepage) ───────────────────────
@stats_bp.route("", methods=["GET"])
def public_stats():
    """
    Retourne les stats de la page d'accueil.
    Priorité : table `stats` si remplie, sinon calcul live.
    """
    rows = Stat.query.filter_by(is_active=True).order_by(Stat.id).all()
    if rows:
        return success([s.to_dict() for s in rows])

    # Calcul live en fallback
    delivered   = Order.query.filter_by(status=OrderStatus.DELIVERED).count()
    total_users = User.query.filter_by(role="client", is_active=True).count()
    countries   = (
        db.session.query(func.count(func.distinct(Request.country)))
        .filter(Request.country.isnot(None))
        .scalar()
    ) or 0

    return success([
        {"icon": "👥", "value": max(450, total_users + 440), "suffix": "+", "label": "Clients satisfaits"},
        {"icon": "📦", "value": max(1200, delivered + 1190), "suffix": "+", "label": "Commandes livrées"},
        {"icon": "⭐", "value": 98,                           "suffix": "%", "label": "Taux de satisfaction"},
        {"icon": "🌍", "value": max(15, countries + 12),      "suffix": "+", "label": "Pays couverts"},
    ])


# ── GET /api/stats/admin  (admin – tableau de bord) ───────────
@stats_bp.route("/admin", methods=["GET"])
@admin_required
def admin_stats():
    total_requests = Request.query.count()
    pending_quote  = Request.query.filter_by(status=RequestStatus.PENDING).count()
    quoted         = Request.query.filter_by(status=RequestStatus.QUOTED).count()
    total_orders   = Order.query.count()
    in_transit     = Order.query.filter(Order.status.in_([
        OrderStatus.CONFIRMED, OrderStatus.CN_TRANSIT,
        OrderStatus.SHIPPING,  OrderStatus.CUSTOMS,
    ])).count()
    delivered      = Order.query.filter_by(status=OrderStatus.DELIVERED).count()
    issues         = Order.query.filter_by(status=OrderStatus.ISSUE).count()
    total_users    = User.query.filter_by(role="client", is_active=True).count()
    gallery_count  = GalleryItem.query.filter_by(is_published=True).count()

    # Chiffre d'affaires estimé (somme des commandes payées)
    paid_orders = Order.query.filter(
        Order.status.in_([
            OrderStatus.CONFIRMED, OrderStatus.CN_TRANSIT,
            OrderStatus.SHIPPING,  OrderStatus.CUSTOMS, OrderStatus.DELIVERED,
        ]),
        Order.total_amount.isnot(None),
    ).all()
    revenue = sum(float(o.total_amount or 0) for o in paid_orders)

    return success({
        "requests": {
            "total":        total_requests,
            "pendingQuote": pending_quote,
            "quoted":       quoted,
        },
        "orders": {
            "total":     total_orders,
            "inTransit": in_transit,
            "delivered": delivered,
            "issues":    issues,
        },
        "users":         total_users,
        "gallery":       gallery_count,
        "revenue":       revenue,
        "pendingAction": pending_quote + quoted,
    })


# ── CRUD table stats (admin) ──────────────────────────────────

@stats_bp.route("/admin/stats-table", methods=["GET"])
@admin_required
def list_stats():
    return success([s.to_dict() for s in Stat.query.order_by(Stat.id).all()])


@stats_bp.route("/admin/stats-table", methods=["POST"])
@admin_required
def create_stat():
    from flask import request as req
    data = req.get_json(silent=True) or {}
    if not data.get("label"):
        from app.utils import error
        return error("label est obligatoire.")
    s = Stat(
        value=int(data.get("value", 0)),
        suffix=data.get("suffix", ""),
        label=data["label"],
        icon=data.get("icon"),
    )
    db.session.add(s)
    db.session.commit()
    return success(s.to_dict(), "Stat créée.")


@stats_bp.route("/admin/stats-table/<int:stat_id>", methods=["PUT"])
@admin_required
def update_stat(stat_id):
    from flask import request as req
    from app.utils import not_found as nf
    s = Stat.query.get(stat_id)
    if not s:
        return nf("Stat introuvable.")
    data = req.get_json(silent=True) or {}
    if "value"    in data: s.value    = int(data["value"])
    if "suffix"   in data: s.suffix   = data["suffix"]
    if "label"    in data: s.label    = data["label"]
    if "icon"     in data: s.icon     = data["icon"]
    if "isActive" in data: s.is_active = bool(data["isActive"])
    db.session.commit()
    return success(s.to_dict(), "Stat mise à jour.")


@stats_bp.route("/admin/stats-table/<int:stat_id>", methods=["DELETE"])
@admin_required
def delete_stat(stat_id):
    from app.utils import not_found as nf
    s = Stat.query.get(stat_id)
    if not s:
        return nf("Stat introuvable.")
    db.session.delete(s)
    db.session.commit()
    return success(message="Stat supprimée.")
