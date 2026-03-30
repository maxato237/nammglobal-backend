from flask import Blueprint, request as req
from app import db
from app.models import Wave
from app.utils import success, created, error, not_found, admin_required, parse_date
import uuid

waves_bp = Blueprint("waves", __name__, url_prefix="/api/waves")

@waves_bp.route("", methods=["GET"])
def list_waves():
    waves = Wave.query.filter_by(is_active=True).order_by(Wave.deadline_date.asc()).all()
    return success([w.to_dict() for w in waves])

@waves_bp.route("/<string:wave_id>", methods=["GET"])
def get_wave(wave_id):
    w = Wave.query.get(wave_id)
    if not w or not w.is_active: return not_found("Vague introuvable.")
    return success(w.to_dict())

@waves_bp.route("", methods=["POST"])
@admin_required
def create_wave():
    data = req.get_json(silent=True) or {}
    err  = _validate(data)
    if err: return error(err)
    w = Wave(id="WAVE-"+str(uuid.uuid4())[:8].upper(),
        name=data["name"].strip(), deadline_date=parse_date(data["deadlineDate"]),
        shipping_date=parse_date(data["shippingDate"]), arrival_date=parse_date(data["arrivalDate"]),
        transport_type=(data.get("transportType") or "").strip() or None,
        notes=(data.get("notes") or "").strip() or None)
    db.session.add(w); db.session.commit()
    return created(w.to_dict(), "Vague créée.")

@waves_bp.route("/<string:wave_id>", methods=["PUT"])
@admin_required
def update_wave(wave_id):
    w = Wave.query.get(wave_id)
    if not w: return not_found("Vague introuvable.")
    data = req.get_json(silent=True) or {}
    err  = _validate(data)
    if err: return error(err)
    w.name          = data["name"].strip()
    w.deadline_date = parse_date(data["deadlineDate"])
    w.shipping_date = parse_date(data["shippingDate"])
    w.arrival_date  = parse_date(data["arrivalDate"])
    w.transport_type = (data.get("transportType") or "").strip() or None
    w.notes          = (data.get("notes") or "").strip() or None
    db.session.commit(); return success(w.to_dict(), "Vague mise à jour.")

@waves_bp.route("/<string:wave_id>", methods=["DELETE"])
@admin_required
def delete_wave(wave_id):
    w = Wave.query.get(wave_id)
    if not w: return not_found("Vague introuvable.")
    w.is_active = False; db.session.commit()
    return success(message="Vague supprimée.")

def _validate(data):
    if not data.get("name"):           return "Le nom de la vague est obligatoire."
    if not data.get("deadlineDate"):   return "La date limite est obligatoire."
    if not data.get("shippingDate"):   return "La date d'expédition est obligatoire."
    if not data.get("arrivalDate"):    return "La date d'arrivée est obligatoire."
    return None
