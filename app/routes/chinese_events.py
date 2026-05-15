from datetime import date, timedelta
from flask import Blueprint, request
from app.extensions import db
from app.models import ChineseEvent
from app.utils import success, created, error, not_found
from app.utils.auth_decorators import admin_required

chinese_events_bp = Blueprint("chinese_events", __name__, url_prefix="/api/v1/chinese-events")


@chinese_events_bp.route("", methods=["GET"])
def list_events():
    year = request.args.get("year", type=int)
    event_type = request.args.get("type")
    q = ChineseEvent.query
    if year:
        q = q.filter_by(year=year)
    if event_type:
        q = q.filter_by(type=event_type)
    events = q.order_by(ChineseEvent.date_start).all()
    return success([e.to_dict() for e in events])


@chinese_events_bp.route("/active", methods=["GET"])
def list_active():
    today = date.today()
    in_30 = today + timedelta(days=30)
    events = (
        ChineseEvent.query
        .filter(ChineseEvent.date_end >= today, ChineseEvent.date_start <= in_30)
        .order_by(ChineseEvent.date_start)
        .all()
    )
    return success([e.to_dict() for e in events])


@chinese_events_bp.route("", methods=["POST"])
@admin_required
def create_event():
    data = request.get_json(silent=True) or {}
    required = ("name", "type", "date_start", "date_end", "year")
    if not all(data.get(f) for f in required):
        return error(f"Champs requis : {', '.join(required)}.")
    from datetime import datetime
    event = ChineseEvent(
        name=data["name"],
        type=data["type"],
        date_start=datetime.strptime(data["date_start"], "%Y-%m-%d").date(),
        date_end=datetime.strptime(data["date_end"], "%Y-%m-%d").date(),
        year=data["year"],
        severity=data.get("severity", "medium"),
        description=data.get("description"),
        color=data.get("color"),
        icon=data.get("icon"),
    )
    db.session.add(event)
    db.session.commit()
    return created(event.to_dict(), "Événement créé.")


@chinese_events_bp.route("/<int:event_id>", methods=["PATCH"])
@admin_required
def update_event(event_id):
    event = ChineseEvent.query.get_or_404(event_id)
    data = request.get_json(silent=True) or {}
    for field in ("name", "type", "severity", "description", "color", "icon"):
        if field in data:
            setattr(event, field, data[field])
    db.session.commit()
    return success(event.to_dict(), "Événement mis à jour.")


@chinese_events_bp.route("/<int:event_id>", methods=["DELETE"])
@admin_required
def delete_event(event_id):
    event = ChineseEvent.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return success(message="Événement supprimé.")
