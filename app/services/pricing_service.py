import logging
from datetime import datetime
from decimal import Decimal

from app.extensions import db
from app.models import ServiceFeeRule, ShippingMethod, ProductCategoryRule, CustomsRule, ExchangeRate

logger = logging.getLogger(__name__)


class PricingService:

    # ── Exchange rate ──────────────────────────────────────────

    @staticmethod
    def get_active_exchange_rate(from_currency: str = "CNY", to_currency: str = "XAF") -> ExchangeRate | None:
        return (
            ExchangeRate.query
            .filter_by(from_currency=from_currency, to_currency=to_currency, is_active=True)
            .order_by(ExchangeRate.effective_at.desc())
            .first()
        )

    @staticmethod
    def convert_cny_to_fcfa(amount_cny: float) -> float:
        rate_obj = PricingService.get_active_exchange_rate("CNY", "XAF")
        if not rate_obj:
            raise ValueError("Aucun taux de change CNY/FCFA actif trouvé.")
        return round(float(amount_cny) * float(rate_obj.rate), 0)

    @staticmethod
    def update_exchange_rate(
        from_currency: str, to_currency: str, rate: float,
        actor=None, ip: str = None, ua: str = None,
    ) -> ExchangeRate:
        from app.services.audit_service import AuditService

        old = ExchangeRate.query.filter_by(
            from_currency=from_currency, to_currency=to_currency, is_active=True,
        ).first()
        before_state = old.to_dict() if old else None
        if old:
            old.is_active = False

        new_rate = ExchangeRate(
            from_currency=from_currency,
            to_currency=to_currency,
            rate=Decimal(str(rate)),
            effective_at=datetime.utcnow(),
            is_active=True,
        )
        db.session.add(new_rate)
        db.session.flush()

        AuditService.log(
            entity_type="exchange_rate",
            action="update",
            entity_id=new_rate.id,
            actor=actor,
            before_state=before_state,
            after_state=new_rate.to_dict(),
            ip_address=ip,
            user_agent=ua,
        )
        db.session.commit()
        return new_rate

    # ── Service fee ────────────────────────────────────────────

    @staticmethod
    def get_service_fee(country_code: str, amount_fcfa: float) -> dict:
        rules = (
            ServiceFeeRule.query
            .filter_by(country_code=country_code)
            .order_by(ServiceFeeRule.min_amount_fcfa.asc())
            .all()
        )
        for r in rules:
            min_ok = float(r.min_amount_fcfa) <= amount_fcfa
            max_ok = r.max_amount_fcfa is None or amount_fcfa <= float(r.max_amount_fcfa)
            if min_ok and max_ok:
                return {
                    "percentage": r.percentage,
                    "amount":     round(amount_fcfa * r.percentage / 100, 0),
                    "ruleId":     r.id,
                    "label":      r.label,
                }
        return {"percentage": 0, "amount": 0, "ruleId": None, "label": None}

    # ── Shipping ───────────────────────────────────────────────

    @staticmethod
    def get_shipping_cost(country_code: str, method_id: int, weight_kg: float) -> dict:
        m = ShippingMethod.query.filter_by(
            id=method_id, country_code=country_code, is_active=True,
        ).first()
        if not m:
            return {"error": "Mode de transport introuvable ou inactif."}
        return {
            "method":     m.name,
            "pricePerKg": float(m.price_per_kg),
            "weightKg":   weight_kg,
            "cost":       round(float(m.price_per_kg) * weight_kg, 0),
        }

    # ── Category surcharge ─────────────────────────────────────

    @staticmethod
    def get_category_surcharge(country_code: str, category: str, weight_kg: float) -> dict:
        r = ProductCategoryRule.query.filter_by(
            country_code=country_code, category_name=category,
        ).first()
        if not r:
            return {"surcharge": 0}

        surcharge_type = r.surcharge_type.value if r.surcharge_type else "none"

        if surcharge_type == "per_kg":
            if not r.surcharge_per_kg:
                return {"surcharge": 0}
            return {
                "surcharge": round(float(r.surcharge_per_kg) * weight_kg, 0),
                "perKg":     float(r.surcharge_per_kg),
                "note":      r.note,
            }

        if surcharge_type == "fixed":
            if not r.surcharge_per_kg:
                return {"surcharge": 0}
            return {
                "surcharge": round(float(r.surcharge_per_kg), 0),
                "note":      r.note,
            }

        return {"surcharge": 0}

    # ── Customs ────────────────────────────────────────────────

    @staticmethod
    def calculate_customs_fee(country_code: str, category: str, total_fcfa: float) -> dict:
        # Priorité : taux douanier de la catégorie produit
        cat_rule = ProductCategoryRule.query.filter_by(
            country_code=country_code, category_name=category,
        ).first()
        if cat_rule and cat_rule.customs_rate_pct:
            fee = round(total_fcfa * cat_rule.customs_rate_pct / 100, 0)
            return {"fee": fee, "ratePct": cat_rule.customs_rate_pct, "source": "category"}

        # Fallback : CustomsRule par seuil
        rule = (
            CustomsRule.query
            .filter_by(country_code=country_code)
            .filter(CustomsRule.threshold_amount_fcfa <= total_fcfa)
            .order_by(CustomsRule.threshold_amount_fcfa.desc())
            .first()
        )
        if rule:
            fee = round(total_fcfa * rule.rate_pct / 100, 0)
            return {"fee": fee, "ratePct": rule.rate_pct, "source": "customs_rule"}

        return {"fee": 0, "ratePct": 0, "source": None}

    # ── Full quote estimation ──────────────────────────────────

    @staticmethod
    def estimate_quote(country_code: str, items: list[dict], shipping_method_id: int = None) -> dict:
        """
        items: [{ product_name, quantity, unit_cost_cny, weight_kg, category }]
        Retourne un breakdown complet par item + totaux globaux en FCFA.
        """
        rate_obj = PricingService.get_active_exchange_rate("CNY", "XAF")
        if not rate_obj:
            raise ValueError("Aucun taux de change CNY/FCFA actif.")

        exchange_rate      = float(rate_obj.rate)
        breakdown          = []
        total_product_fcfa = 0
        total_service_fee  = 0
        total_shipping     = 0
        total_customs      = 0

        for item in items:
            qty          = int(item.get("quantity", 1))
            unit_cny     = float(item.get("unit_cost_cny", 0))
            weight_kg    = float(item.get("weight_kg", 0))
            category     = item.get("category") or ""
            product_name = item.get("product_name", "")

            unit_fcfa  = round(unit_cny * exchange_rate, 0)
            line_fcfa  = round(unit_fcfa * qty, 0)
            total_w    = weight_kg * qty

            svc     = PricingService.get_service_fee(country_code, line_fcfa)
            ship    = (
                PricingService.get_shipping_cost(country_code, shipping_method_id, total_w)
                if shipping_method_id else {"cost": 0}
            )
            if "error" in ship:
                raise ValueError(ship["error"])

            cat     = PricingService.get_category_surcharge(country_code, category, total_w) if category else {"surcharge": 0}
            customs = PricingService.calculate_customs_fee(country_code, category, line_fcfa) if category else {"fee": 0, "ratePct": 0}

            line_svc     = svc.get("amount", 0)
            line_ship    = ship.get("cost", 0) + cat.get("surcharge", 0)
            line_customs = customs.get("fee", 0)
            line_total   = round(line_fcfa + line_svc + line_ship + line_customs, 0)

            breakdown.append({
                "productName":       product_name,
                "quantity":          qty,
                "unitCostCny":       unit_cny,
                "unitCostFcfa":      unit_fcfa,
                "lineCostFcfa":      line_fcfa,
                "serviceFee":        line_svc,
                "serviceFeeRate":    svc.get("percentage", 0),
                "shippingCost":      ship.get("cost", 0),
                "categorySurcharge": cat.get("surcharge", 0),
                "customsFee":        line_customs,
                "customsRate":       customs.get("ratePct", 0),
                "lineTotal":         line_total,
            })

            total_product_fcfa += line_fcfa
            total_service_fee  += line_svc
            total_shipping     += line_ship
            total_customs      += line_customs

        grand_total = round(total_product_fcfa + total_service_fee + total_shipping + total_customs, 0)

        return {
            "countryCode":      country_code,
            "exchangeRate":     exchange_rate,
            "breakdown":        breakdown,
            "totalProductFcfa": total_product_fcfa,
            "totalServiceFee":  total_service_fee,
            "totalShipping":    total_shipping,
            "totalCustoms":     total_customs,
            "grandTotalFcfa":   grand_total,
        }

    # ── Pricing bundle (1 appel = tout le pricing d'un pays) ──

    @staticmethod
    def get_pricing_bundle(country_code: str) -> dict:
        shipping   = (
            ShippingMethod.query
            .filter_by(country_code=country_code, is_active=True)
            .order_by(ShippingMethod.sort_order)
            .all()
        )
        fees       = (
            ServiceFeeRule.query
            .filter_by(country_code=country_code)
            .order_by(ServiceFeeRule.min_amount_fcfa)
            .all()
        )
        categories = ProductCategoryRule.query.filter_by(country_code=country_code).all()
        customs    = (
            CustomsRule.query
            .filter_by(country_code=country_code)
            .order_by(CustomsRule.threshold_amount_fcfa)
            .all()
        )
        rate       = PricingService.get_active_exchange_rate("CNY", "XAF")

        return {
            "countryCode":      country_code,
            "shippingMethods":  [m.to_dict() for m in shipping],
            "serviceFeeRules":  [r.to_dict() for r in fees],
            "categoryRules":    [c.to_dict() for c in categories],
            "customsRules":     [c.to_dict() for c in customs],
            "exchangeRate":     rate.to_dict() if rate else None,
        }
