from flask import Blueprint, request as req
from app import db
from app.models import ServiceFeeRule, ShippingMethod, ProductCategoryRule
from app.services import PricingService
from app.utils import success, created, error, not_found, admin_required

pricing_bp = Blueprint("pricing", __name__, url_prefix="/api/pricing")


# ── Frais de service ──────────────────────────────────────────

@pricing_bp.route("/fees", methods=["GET"])
def list_fees():
    rules = ServiceFeeRule.query.order_by(ServiceFeeRule.min_amount).all()
    return success([r.to_dict() for r in rules])


@pricing_bp.route("/fees", methods=["POST"])
@admin_required
def create_fee():
    data = req.get_json(silent=True) or {}

    # minAmount et percentage sont obligatoires ; maxAmount peut être None (tranche illimitée)
    if data.get("minAmount") is None or data.get("percentage") is None:
        return error("minAmount et percentage sont obligatoires.")

    rule = ServiceFeeRule(
        min_amount = float(data["minAmount"]),
        max_amount = float(data["maxAmount"]) if data.get("maxAmount") is not None else None,
        percentage = float(data["percentage"]),
        label      = (data.get("label") or "").strip() or None,
    )
    db.session.add(rule)
    db.session.commit()
    return created(rule.to_dict(), "Règle créée.")


@pricing_bp.route("/fees/<int:rule_id>", methods=["PUT"])
@admin_required
def update_fee(rule_id):
    rule = ServiceFeeRule.query.get(rule_id)
    if not rule:
        return not_found("Règle introuvable.")
    data = req.get_json(silent=True) or {}
    if "minAmount"  in data: rule.min_amount  = float(data["minAmount"])
    if "maxAmount"  in data: rule.max_amount  = float(data["maxAmount"]) if data["maxAmount"] is not None else None
    if "percentage" in data: rule.percentage  = float(data["percentage"])
    if "label"      in data: rule.label       = data["label"]
    db.session.commit()
    return success(rule.to_dict(), "Règle mise à jour.")


@pricing_bp.route("/fees/<int:rule_id>", methods=["DELETE"])
@admin_required
def delete_fee(rule_id):
    rule = ServiceFeeRule.query.get(rule_id)
    if not rule:
        return not_found("Règle introuvable.")
    db.session.delete(rule)
    db.session.commit()
    return success(message="Règle supprimée.")


# ── Modes de transport ────────────────────────────────────────

@pricing_bp.route("/shipping", methods=["GET"])
def list_shipping():
    # Tous les modes pour l'admin (via ?all=1), actifs uniquement pour le public
    show_all = req.args.get("all") == "1"
    q = ShippingMethod.query
    if not show_all:
        q = q.filter_by(is_active=True)
    return success([m.to_dict() for m in q.all()])


@pricing_bp.route("/shipping", methods=["POST"])
@admin_required
def create_shipping():
    data = req.get_json(silent=True) or {}
    if not data.get("name") or data.get("pricePerKg") is None:
        return error("name et pricePerKg sont obligatoires.")
    m = ShippingMethod(
        name         = data["name"].strip(),
        timeframe    = data.get("timeframe"),
        price_per_kg = float(data["pricePerKg"]),
        max_kg       = float(data["maxKg"]) if data.get("maxKg") is not None else None,
        icon         = data.get("icon"),
    )
    db.session.add(m)
    db.session.commit()
    return created(m.to_dict(), "Mode de transport créé.")


@pricing_bp.route("/shipping/<int:method_id>", methods=["PUT"])
@admin_required
def update_shipping(method_id):
    m = ShippingMethod.query.get(method_id)
    if not m:
        return not_found("Mode de transport introuvable.")
    data = req.get_json(silent=True) or {}
    if "name"       in data: m.name         = data["name"].strip()
    if "timeframe"  in data: m.timeframe    = data["timeframe"]
    if "pricePerKg" in data: m.price_per_kg = float(data["pricePerKg"])
    if "maxKg"      in data: m.max_kg       = float(data["maxKg"]) if data["maxKg"] is not None else None
    if "icon"       in data: m.icon         = data["icon"]
    if "isActive"   in data: m.is_active    = bool(data["isActive"])
    db.session.commit()
    return success(m.to_dict(), "Mode de transport mis à jour.")


@pricing_bp.route("/shipping/<int:method_id>", methods=["DELETE"])
@admin_required
def delete_shipping(method_id):
    m = ShippingMethod.query.get(method_id)
    if not m:
        return not_found("Mode de transport introuvable.")
    # Soft-delete : désactivation plutôt que suppression (des devis peuvent référencer ce mode)
    m.is_active = False
    db.session.commit()
    return success(message="Mode de transport désactivé.")


# ── Catégories produit ────────────────────────────────────────

@pricing_bp.route("/categories", methods=["GET"])
def list_categories():
    return success([c.to_dict() for c in ProductCategoryRule.query.all()])


@pricing_bp.route("/categories", methods=["POST"])
@admin_required
def create_category():
    data = req.get_json(silent=True) or {}
    if not data.get("categoryName"):
        return error("categoryName est obligatoire.")

    # surchargeType doit être cohérent avec les valeurs du modèle : per_kg | fixed | none
    surcharge_type = data.get("surchargeType")
    if surcharge_type and surcharge_type not in ("per_kg", "fixed", "none"):
        return error("surchargeType invalide. Valeurs acceptées : per_kg, fixed, none.")

    c = ProductCategoryRule(
        category_name    = data["categoryName"].strip(),
        surcharge_per_kg = float(data["surchargePerKg"]) if data.get("surchargePerKg") is not None else None,
        surcharge_type   = surcharge_type,
        note             = data.get("note"),
        icon             = data.get("icon"),
    )
    db.session.add(c)
    db.session.commit()
    return created(c.to_dict(), "Catégorie créée.")


@pricing_bp.route("/categories/<int:cat_id>", methods=["PUT"])
@admin_required
def update_category(cat_id):
    c = ProductCategoryRule.query.get(cat_id)
    if not c:
        return not_found("Catégorie introuvable.")
    data = req.get_json(silent=True) or {}

    if "surchargeType" in data and data["surchargeType"] not in ("per_kg", "fixed", "none", None):
        return error("surchargeType invalide. Valeurs acceptées : per_kg, fixed, none.")

    if "categoryName"   in data: c.category_name    = data["categoryName"].strip()
    if "surchargePerKg" in data: c.surcharge_per_kg = float(data["surchargePerKg"]) if data["surchargePerKg"] is not None else None
    if "surchargeType"  in data: c.surcharge_type   = data["surchargeType"]
    if "note"           in data: c.note             = data["note"]
    if "icon"           in data: c.icon             = data["icon"]
    db.session.commit()
    return success(c.to_dict(), "Catégorie mise à jour.")


@pricing_bp.route("/categories/<int:cat_id>", methods=["DELETE"])
@admin_required
def delete_category(cat_id):
    c = ProductCategoryRule.query.get(cat_id)
    if not c:
        return not_found("Catégorie introuvable.")
    db.session.delete(c)
    db.session.commit()
    return success(message="Catégorie supprimée.")


# ── Simulateur ────────────────────────────────────────────────

@pricing_bp.route("/simulate", methods=["POST"])
def simulate():
    """Calcule les frais pour un panier (public — utilisé par la page tarifs)."""
    data = req.get_json(silent=True) or {}
    try:
        amount    = float(data.get("amount", 0))
        weight_kg = float(data.get("weightKg", 0))
        method_id = data.get("shippingMethodId")
        category  = data.get("category")

        svc = PricingService.get_service_fee(amount)
        result = {
            "amount":         amount,
            "serviceFee":     svc.get("amount"),
            "serviceFeeRate": svc.get("percentage"),
        }

        if method_id and weight_kg:
            ship = PricingService.get_shipping_cost(int(method_id), weight_kg)
            result["shippingCost"] = ship.get("cost")

        if category and weight_kg:
            cat = PricingService.get_category_surcharge(category, weight_kg)
            result["categorySurcharge"] = cat.get("surcharge")

        return success(result)
    except Exception as e:
        return error(str(e))