from flask import Blueprint, request
from app.extensions import db
from app.models import SystemSetting
from app.utils import success, created, error, not_found
from app.utils.auth_decorators import admin_required

settings_bp = Blueprint("settings", __name__, url_prefix="/api/v1/settings")


@settings_bp.route("", methods=["GET"])
@admin_required
def list_settings():
    category = request.args.get("category")
    q = SystemSetting.query
    if category:
        q = q.filter_by(category=category)
    settings = q.order_by(SystemSetting.key).all()
    return success([s.to_dict() for s in settings])


@settings_bp.route("/public", methods=["GET"])
def public_settings():
    settings = SystemSetting.query.filter_by(is_public=True).all()
    return success({s.key: s.get_typed_value() for s in settings})


@settings_bp.route("/<key>", methods=["GET"])
@admin_required
def get_setting(key):
    setting = SystemSetting.query.get(key)
    if not setting:
        return not_found("Paramètre introuvable.")
    return success(setting.to_dict())


@settings_bp.route("/<key>", methods=["PATCH"])
@admin_required
def update_setting(key):
    setting = SystemSetting.query.get(key)
    if not setting:
        return not_found("Paramètre introuvable.")
    data = request.get_json(silent=True) or {}
    if "value" in data:
        setting.value = str(data["value"])
    if "is_public" in data:
        setting.is_public = bool(data["is_public"])
    from app.utils.auth_decorators import current_user
    u = current_user()
    setting.updated_by_user_id = u.id if u else None
    db.session.commit()
    return success(setting.to_dict(), "Paramètre mis à jour.")


@settings_bp.route("", methods=["POST"])
@admin_required
def create_setting():
    data = request.get_json(silent=True) or {}
    key = (data.get("key") or "").strip()
    if not key:
        return error("La clé est requise.")
    if SystemSetting.query.get(key):
        return error("Ce paramètre existe déjà.", 409)
    setting = SystemSetting(
        key=key,
        value=str(data.get("value", "")),
        value_type=data.get("value_type", "string"),
        description=data.get("description"),
        category=data.get("category"),
        is_public=data.get("is_public", False),
    )
    db.session.add(setting)
    db.session.commit()
    return created(setting.to_dict(), "Paramètre créé.")
