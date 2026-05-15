from flask import Blueprint, request
from app.extensions import db
from app.models import Country
from app.utils import success, error, not_found
from app.utils.auth_decorators import login_required, admin_required

countries_bp = Blueprint("countries", __name__, url_prefix="/api/v1/countries")


@countries_bp.route("", methods=["GET"])
def list_countries():
    countries = Country.query.filter_by(is_served=True).order_by(Country.sort_order).all()
    return success([c.to_dict() for c in countries])


@countries_bp.route("/<code>", methods=["GET"])
def get_country(code):
    country = Country.query.get(code.upper())
    if not country:
        return not_found("Pays introuvable.")
    return success(country.to_dict())


@countries_bp.route("/<code>/dial-codes", methods=["GET"])
def get_dial_codes(code):
    country = Country.query.get(code.upper())
    if not country:
        return not_found("Pays introuvable.")
    return success({"code": country.code, "dial_code": country.dial_code, "flag_emoji": country.flag_emoji})


@countries_bp.route("", methods=["POST"])
@admin_required
def create_country():
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip().upper()
    if not code or len(code) != 2:
        return error("Code pays ISO2 requis (ex: CM).")
    if Country.query.get(code):
        return error("Ce pays existe déjà.", 409)
    country = Country(
        code=code,
        name_fr=data.get("name_fr", ""),
        name_en=data.get("name_en", ""),
        dial_code=data.get("dial_code"),
        currency=data.get("currency"),
        flag_emoji=data.get("flag_emoji"),
        is_served=data.get("is_served", False),
        sort_order=data.get("sort_order", 0),
    )
    db.session.add(country)
    db.session.commit()
    return success(country.to_dict(), "Pays créé."), 201


@countries_bp.route("/<code>", methods=["PATCH"])
@admin_required
def update_country(code):
    country = Country.query.get(code.upper())
    if not country:
        return not_found("Pays introuvable.")
    data = request.get_json(silent=True) or {}
    for field in ("name_fr", "name_en", "dial_code", "currency", "flag_emoji", "is_served", "sort_order"):
        if field in data:
            setattr(country, field, data[field])
    db.session.commit()
    return success(country.to_dict(), "Pays mis à jour.")
