from flask import Blueprint, request as req, g
from pydantic import ValidationError

from app import db
from app.models import (
    ServiceFeeRule, ShippingMethod, ProductCategoryRule,
    CustomsRule, ExchangeRate, Country,
)
from app.services import PricingService
from app.services.audit_service import AuditService
from app.schemas.pricing import (
    ShippingMethodCreateIn, ShippingMethodUpdateIn,
    ServiceFeeRuleCreateIn, ServiceFeeRuleUpdateIn,
    ProductCategoryRuleCreateIn, ProductCategoryRuleUpdateIn,
    CustomsRuleCreateIn, CustomsRuleUpdateIn,
    ExchangeRateCreateIn,
    QuoteEstimateIn,
)
from app.utils import success, created, error, not_found, admin_required, login_required, current_user

pricing_bp = Blueprint("pricing", __name__, url_prefix="/api/pricing")


def _validate(schema_cls, data: dict):
    """Valide data avec le schema Pydantic. Retourne (instance, None) ou (None, error_response)."""
    try:
        return schema_cls(**data), None
    except ValidationError as e:
        msgs = [f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in e.errors()]
        return None, error("Données invalides.", 422, errors=msgs)


def _country_or_404(cc: str):
    """Vérifie que le code pays existe et est desservi."""
    cc = cc.upper()
    country = Country.query.filter_by(code=cc).first()
    if not country:
        return None, not_found(f"Pays '{cc}' introuvable.")
    return cc, None


# ── Bundle complet ─────────────────────────────────────────────

@pricing_bp.route("/<cc>", methods=["GET"])
def get_bundle(cc: str):
    """Retourne le pricing complet d'un pays en un seul appel."""
    cc, err = _country_or_404(cc)
    if err:
        return err
    return success(PricingService.get_pricing_bundle(cc))


# ── Taux de change ─────────────────────────────────────────────

@pricing_bp.route("/exchange-rate", methods=["GET"])
def get_exchange_rate():
    rate = PricingService.get_active_exchange_rate("CNY", "XAF")
    if not rate:
        return not_found("Aucun taux de change CNY/FCFA actif.")
    return success(rate.to_dict())


@pricing_bp.route("/exchange-rate", methods=["POST"])
@admin_required
def create_exchange_rate():
    user = current_user()
    if user.role != "super_admin":
        return error("Réservé au super_admin.", 403)

    payload, err = _validate(ExchangeRateCreateIn, req.get_json(silent=True) or {})
    if err:
        return err

    rate = PricingService.update_exchange_rate(
        from_currency=payload.from_currency,
        to_currency=payload.to_currency,
        rate=payload.rate,
        actor=user,
        ip=req.remote_addr,
        ua=req.headers.get("User-Agent", ""),
    )
    return created(rate.to_dict(), "Taux de change mis à jour.")


# ── Simulateur de devis ────────────────────────────────────────

@pricing_bp.route("/quote/estimate", methods=["POST"])
@login_required
def quote_estimate():
    payload, err = _validate(QuoteEstimateIn, req.get_json(silent=True) or {})
    if err:
        return err

    cc, err = _country_or_404(payload.country_code)
    if err:
        return err

    try:
        result = PricingService.estimate_quote(
            country_code=cc,
            items=[item.model_dump() for item in payload.items],
            shipping_method_id=payload.shipping_method_id,
        )
        return success(result)
    except ValueError as e:
        return error(str(e))


# ── Méthodes d'expédition ──────────────────────────────────────

@pricing_bp.route("/<cc>/shipping", methods=["GET"])
def list_shipping(cc: str):
    cc, err = _country_or_404(cc)
    if err:
        return err
    show_all = req.args.get("all") == "1"
    q = ShippingMethod.query.filter_by(country_code=cc)
    if not show_all:
        q = q.filter_by(is_active=True)
    return success([m.to_dict() for m in q.order_by(ShippingMethod.sort_order).all()])


@pricing_bp.route("/<cc>/shipping", methods=["POST"])
@admin_required
def create_shipping(cc: str):
    cc, err = _country_or_404(cc)
    if err:
        return err

    data = req.get_json(silent=True) or {}
    data["country_code"] = cc
    payload, err = _validate(ShippingMethodCreateIn, data)
    if err:
        return err

    m = ShippingMethod(
        country_code=cc,
        name=payload.name,
        timeframe_days_min=payload.timeframe_days_min,
        timeframe_days_max=payload.timeframe_days_max,
        price_per_kg=payload.price_per_kg,
        min_kg=payload.min_kg,
        max_kg=payload.max_kg,
        icon=payload.icon,
        is_active=payload.is_active,
        sort_order=payload.sort_order,
    )
    db.session.add(m)
    db.session.commit()

    AuditService.log("shipping_method", "create", entity_id=m.id, actor=current_user(),
                     after_state=m.to_dict(), ip_address=req.remote_addr)
    return created(m.to_dict(), "Mode d'expédition créé.")


@pricing_bp.route("/<cc>/shipping/<int:method_id>", methods=["PATCH"])
@admin_required
def update_shipping(cc: str, method_id: int):
    cc, err = _country_or_404(cc)
    if err:
        return err

    m = ShippingMethod.query.filter_by(id=method_id, country_code=cc).first()
    if not m:
        return not_found("Mode d'expédition introuvable.")

    payload, err = _validate(ShippingMethodUpdateIn, req.get_json(silent=True) or {})
    if err:
        return err

    before = m.to_dict()
    if payload.name               is not None: m.name               = payload.name
    if payload.timeframe_days_min is not None: m.timeframe_days_min = payload.timeframe_days_min
    if payload.timeframe_days_max is not None: m.timeframe_days_max = payload.timeframe_days_max
    if payload.price_per_kg       is not None: m.price_per_kg       = payload.price_per_kg
    if payload.min_kg             is not None: m.min_kg             = payload.min_kg
    if payload.max_kg             is not None: m.max_kg             = payload.max_kg
    if payload.icon               is not None: m.icon               = payload.icon
    if payload.is_active          is not None: m.is_active          = payload.is_active
    if payload.sort_order         is not None: m.sort_order         = payload.sort_order
    db.session.commit()

    AuditService.log("shipping_method", "update", entity_id=m.id, actor=current_user(),
                     before_state=before, after_state=m.to_dict(), ip_address=req.remote_addr)
    return success(m.to_dict(), "Mode d'expédition mis à jour.")


@pricing_bp.route("/<cc>/shipping/<int:method_id>", methods=["DELETE"])
@admin_required
def delete_shipping(cc: str, method_id: int):
    cc, err = _country_or_404(cc)
    if err:
        return err

    m = ShippingMethod.query.filter_by(id=method_id, country_code=cc).first()
    if not m:
        return not_found("Mode d'expédition introuvable.")

    # Soft-delete : des devis peuvent référencer ce mode
    before = m.to_dict()
    m.is_active = False
    db.session.commit()

    AuditService.log("shipping_method", "deactivate", entity_id=m.id, actor=current_user(),
                     before_state=before, after_state=m.to_dict(), ip_address=req.remote_addr)
    return success(message="Mode d'expédition désactivé.")


# ── Frais de service ───────────────────────────────────────────

@pricing_bp.route("/<cc>/service-fees", methods=["GET"])
def list_fees(cc: str):
    cc, err = _country_or_404(cc)
    if err:
        return err
    rules = ServiceFeeRule.query.filter_by(country_code=cc).order_by(ServiceFeeRule.min_amount_fcfa).all()
    return success([r.to_dict() for r in rules])


@pricing_bp.route("/<cc>/service-fees", methods=["POST"])
@admin_required
def create_fee(cc: str):
    cc, err = _country_or_404(cc)
    if err:
        return err

    data = req.get_json(silent=True) or {}
    data["country_code"] = cc
    payload, err = _validate(ServiceFeeRuleCreateIn, data)
    if err:
        return err

    rule = ServiceFeeRule(
        country_code=cc,
        min_amount_fcfa=payload.min_amount_fcfa,
        max_amount_fcfa=payload.max_amount_fcfa,
        percentage=payload.percentage,
        label=payload.label,
    )
    db.session.add(rule)
    db.session.commit()

    AuditService.log("service_fee_rule", "create", entity_id=rule.id, actor=current_user(),
                     after_state=rule.to_dict(), ip_address=req.remote_addr)
    return created(rule.to_dict(), "Règle de frais créée.")


@pricing_bp.route("/<cc>/service-fees/<int:rule_id>", methods=["PATCH"])
@admin_required
def update_fee(cc: str, rule_id: int):
    cc, err = _country_or_404(cc)
    if err:
        return err

    rule = ServiceFeeRule.query.filter_by(id=rule_id, country_code=cc).first()
    if not rule:
        return not_found("Règle introuvable.")

    payload, err = _validate(ServiceFeeRuleUpdateIn, req.get_json(silent=True) or {})
    if err:
        return err

    before = rule.to_dict()
    if payload.min_amount_fcfa is not None: rule.min_amount_fcfa = payload.min_amount_fcfa
    if payload.max_amount_fcfa is not None: rule.max_amount_fcfa = payload.max_amount_fcfa
    if payload.percentage      is not None: rule.percentage      = payload.percentage
    if payload.label           is not None: rule.label           = payload.label
    db.session.commit()

    AuditService.log("service_fee_rule", "update", entity_id=rule.id, actor=current_user(),
                     before_state=before, after_state=rule.to_dict(), ip_address=req.remote_addr)
    return success(rule.to_dict(), "Règle mise à jour.")


@pricing_bp.route("/<cc>/service-fees/<int:rule_id>", methods=["DELETE"])
@admin_required
def delete_fee(cc: str, rule_id: int):
    cc, err = _country_or_404(cc)
    if err:
        return err

    rule = ServiceFeeRule.query.filter_by(id=rule_id, country_code=cc).first()
    if not rule:
        return not_found("Règle introuvable.")

    before = rule.to_dict()
    db.session.delete(rule)
    db.session.commit()

    AuditService.log("service_fee_rule", "delete", entity_id=rule_id, actor=current_user(),
                     before_state=before, ip_address=req.remote_addr)
    return success(message="Règle supprimée.")


# ── Catégories produit ─────────────────────────────────────────

@pricing_bp.route("/<cc>/categories", methods=["GET"])
def list_categories(cc: str):
    cc, err = _country_or_404(cc)
    if err:
        return err
    cats = ProductCategoryRule.query.filter_by(country_code=cc).all()
    return success([c.to_dict() for c in cats])


@pricing_bp.route("/<cc>/categories", methods=["POST"])
@admin_required
def create_category(cc: str):
    cc, err = _country_or_404(cc)
    if err:
        return err

    data = req.get_json(silent=True) or {}
    data["country_code"] = cc
    payload, err = _validate(ProductCategoryRuleCreateIn, data)
    if err:
        return err

    cat = ProductCategoryRule(
        country_code=cc,
        category_name=payload.category_name,
        surcharge_per_kg=payload.surcharge_per_kg,
        surcharge_type=payload.surcharge_type,
        customs_rate_pct=payload.customs_rate_pct,
        note=payload.note,
        icon=payload.icon,
    )
    db.session.add(cat)
    db.session.commit()

    AuditService.log("category_rule", "create", entity_id=cat.id, actor=current_user(),
                     after_state=cat.to_dict(), ip_address=req.remote_addr)
    return created(cat.to_dict(), "Catégorie créée.")


@pricing_bp.route("/<cc>/categories/<int:cat_id>", methods=["PATCH"])
@admin_required
def update_category(cc: str, cat_id: int):
    cc, err = _country_or_404(cc)
    if err:
        return err

    cat = ProductCategoryRule.query.filter_by(id=cat_id, country_code=cc).first()
    if not cat:
        return not_found("Catégorie introuvable.")

    payload, err = _validate(ProductCategoryRuleUpdateIn, req.get_json(silent=True) or {})
    if err:
        return err

    before = cat.to_dict()
    if payload.category_name    is not None: cat.category_name    = payload.category_name
    if payload.surcharge_per_kg is not None: cat.surcharge_per_kg = payload.surcharge_per_kg
    if payload.surcharge_type   is not None: cat.surcharge_type   = payload.surcharge_type
    if payload.customs_rate_pct is not None: cat.customs_rate_pct = payload.customs_rate_pct
    if payload.note             is not None: cat.note             = payload.note
    if payload.icon             is not None: cat.icon             = payload.icon
    db.session.commit()

    AuditService.log("category_rule", "update", entity_id=cat.id, actor=current_user(),
                     before_state=before, after_state=cat.to_dict(), ip_address=req.remote_addr)
    return success(cat.to_dict(), "Catégorie mise à jour.")


@pricing_bp.route("/<cc>/categories/<int:cat_id>", methods=["DELETE"])
@admin_required
def delete_category(cc: str, cat_id: int):
    cc, err = _country_or_404(cc)
    if err:
        return err

    cat = ProductCategoryRule.query.filter_by(id=cat_id, country_code=cc).first()
    if not cat:
        return not_found("Catégorie introuvable.")

    before = cat.to_dict()
    db.session.delete(cat)
    db.session.commit()

    AuditService.log("category_rule", "delete", entity_id=cat_id, actor=current_user(),
                     before_state=before, ip_address=req.remote_addr)
    return success(message="Catégorie supprimée.")


# ── Règles douanières ──────────────────────────────────────────

@pricing_bp.route("/<cc>/customs", methods=["GET"])
def list_customs(cc: str):
    cc, err = _country_or_404(cc)
    if err:
        return err
    rules = CustomsRule.query.filter_by(country_code=cc).order_by(CustomsRule.threshold_amount_fcfa).all()
    return success([r.to_dict() for r in rules])


@pricing_bp.route("/<cc>/customs", methods=["POST"])
@admin_required
def create_customs(cc: str):
    cc, err = _country_or_404(cc)
    if err:
        return err

    data = req.get_json(silent=True) or {}
    data["country_code"] = cc
    payload, err = _validate(CustomsRuleCreateIn, data)
    if err:
        return err

    rule = CustomsRule(
        country_code=cc,
        threshold_amount_fcfa=payload.threshold_amount_fcfa,
        rate_pct=payload.rate_pct,
        note=payload.note,
    )
    db.session.add(rule)
    db.session.commit()

    AuditService.log("customs_rule", "create", entity_id=rule.id, actor=current_user(),
                     after_state=rule.to_dict(), ip_address=req.remote_addr)
    return created(rule.to_dict(), "Règle douanière créée.")


@pricing_bp.route("/<cc>/customs/<int:rule_id>", methods=["PATCH"])
@admin_required
def update_customs(cc: str, rule_id: int):
    cc, err = _country_or_404(cc)
    if err:
        return err

    rule = CustomsRule.query.filter_by(id=rule_id, country_code=cc).first()
    if not rule:
        return not_found("Règle douanière introuvable.")

    payload, err = _validate(CustomsRuleUpdateIn, req.get_json(silent=True) or {})
    if err:
        return err

    before = rule.to_dict()
    if payload.threshold_amount_fcfa is not None: rule.threshold_amount_fcfa = payload.threshold_amount_fcfa
    if payload.rate_pct              is not None: rule.rate_pct              = payload.rate_pct
    if payload.note                  is not None: rule.note                  = payload.note
    db.session.commit()

    AuditService.log("customs_rule", "update", entity_id=rule.id, actor=current_user(),
                     before_state=before, after_state=rule.to_dict(), ip_address=req.remote_addr)
    return success(rule.to_dict(), "Règle douanière mise à jour.")


@pricing_bp.route("/<cc>/customs/<int:rule_id>", methods=["DELETE"])
@admin_required
def delete_customs(cc: str, rule_id: int):
    cc, err = _country_or_404(cc)
    if err:
        return err

    rule = CustomsRule.query.filter_by(id=rule_id, country_code=cc).first()
    if not rule:
        return not_found("Règle douanière introuvable.")

    before = rule.to_dict()
    db.session.delete(rule)
    db.session.commit()

    AuditService.log("customs_rule", "delete", entity_id=rule_id, actor=current_user(),
                     before_state=before, ip_address=req.remote_addr)
    return success(message="Règle douanière supprimée.")
