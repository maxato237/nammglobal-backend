from flask import Blueprint, request as req
from app import db
from app.models import GalleryItem
from app.utils import success, created, error, not_found, admin_required, parse_date

gallery_bp = Blueprint("gallery", __name__, url_prefix="/api/gallery")

@gallery_bp.route("", methods=["GET"])
def list_gallery():
    filter_type = req.args.get("type")
    q = GalleryItem.query.filter_by(is_published=True)
    if filter_type in ("photo","video"): q = q.filter_by(type=filter_type)
    items = q.order_by(GalleryItem.created_at.desc()).all()
    return success([i.to_dict() for i in items])

@gallery_bp.route("/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = GalleryItem.query.get(item_id)
    if not item or not item.is_published: return not_found("Élément introuvable.")
    return success(item.to_dict())

@gallery_bp.route("", methods=["POST"])
@admin_required
def create_item():
    data = req.get_json(silent=True) or {}
    if not data.get("productName") or not data.get("thumbUrl"):
        return error("productName et thumbUrl sont obligatoires.")
    item = GalleryItem(
        type=data.get("type","photo"), product_name=data["productName"].strip(),
        category=(data.get("category") or "").strip() or None,
        thumb_url=data["thumbUrl"].strip(), full_url=(data.get("fullUrl") or data["thumbUrl"]).strip(),
        client_name=(data.get("clientName") or "").strip() or None,
        client_city=(data.get("clientCity") or "").strip() or None,
        weight=_float(data.get("weight")),
        order_date=parse_date(data.get("orderDate")),
        arrival_date=parse_date(data.get("arrivalDate")),
        comment=(data.get("comment") or "").strip() or None,
        rating=int(data.get("rating") or 5),
        order_id=data.get("orderId") or None,
    )
    db.session.add(item); db.session.commit()
    return created(item.to_dict(), "Élément ajouté à la galerie.")

@gallery_bp.route("/<int:item_id>", methods=["PUT"])
@admin_required
def update_item(item_id):
    item = GalleryItem.query.get(item_id)
    if not item: return not_found("Élément introuvable.")
    data = req.get_json(silent=True) or {}
    if not data.get("productName") or not data.get("thumbUrl"):
        return error("productName et thumbUrl sont obligatoires.")
    item.type         = data.get("type", item.type)
    item.product_name = data["productName"].strip()
    item.category     = (data.get("category") or "").strip() or None
    item.thumb_url    = data["thumbUrl"].strip()
    item.full_url     = (data.get("fullUrl") or item.thumb_url).strip()
    item.client_name  = (data.get("clientName") or "").strip() or None
    item.client_city  = (data.get("clientCity") or "").strip() or None
    item.weight       = _float(data.get("weight"))
    item.order_date   = parse_date(data.get("orderDate"))
    item.arrival_date = parse_date(data.get("arrivalDate"))
    item.comment      = (data.get("comment") or "").strip() or None
    item.rating       = int(data.get("rating") or item.rating or 5)
    db.session.commit(); return success(item.to_dict(), "Élément mis à jour.")

@gallery_bp.route("/<int:item_id>", methods=["DELETE"])
@admin_required
def delete_item(item_id):
    item = GalleryItem.query.get(item_id)
    if not item: return not_found("Élément introuvable.")
    item.is_published = False; db.session.commit()
    return success(message="Élément supprimé.")

def _float(val):
    try: return float(val) if val not in (None,"") else None
    except: return None
