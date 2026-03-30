from app.models import ServiceFeeRule, ShippingMethod, ProductCategoryRule


class PricingService:

    @staticmethod
    def get_service_fee(amount: float) -> dict:
        rules = ServiceFeeRule.query.order_by(ServiceFeeRule.min_amount.asc()).all()

        for r in rules:
            min_ok = float(r.min_amount) <= amount
            # max_amount NULL = illimité → pas de borne supérieure
            max_ok = r.max_amount is None or amount <= float(r.max_amount)

            if min_ok and max_ok:
                return {
                    "percentage": r.percentage,
                    "amount":     round(amount * r.percentage / 100, 2),
                    "ruleId":     r.id,
                    "label":      r.label,
                }

        return {"percentage": 0, "amount": 0, "ruleId": None}

    # ─────────────────────────────────────────────────────────

    @staticmethod
    def get_shipping_cost(method_id: int, weight_kg: float) -> dict:
        m = ShippingMethod.query.filter_by(id=method_id, is_active=True).first()  # ← filtre is_active

        if not m:
            return {"error": "Mode de transport introuvable ou inactif."}

        return {
            "method":     m.name,
            "pricePerKg": float(m.price_per_kg),
            "weightKg":   weight_kg,
            "cost":       round(float(m.price_per_kg) * weight_kg, 2),
        }

    # ─────────────────────────────────────────────────────────

    @staticmethod
    def get_category_surcharge(category: str, weight_kg: float) -> dict:
        r = ProductCategoryRule.query.filter_by(category_name=category).first()

        if not r:
            return {"surcharge": 0}

        surcharge_type = r.surcharge_type or "per_kg"

        # ── per_kg : surcharge_per_kg × poids ────────────────
        if surcharge_type == "per_kg":
            if not r.surcharge_per_kg:
                return {"surcharge": 0}
            return {
                "surcharge": round(float(r.surcharge_per_kg) * weight_kg, 2),
                "perKg":     float(r.surcharge_per_kg),
                "note":      r.note,
            }

        # ── fixed : montant fixe indépendant du poids ─────────
        if surcharge_type == "fixed":
            if not r.surcharge_per_kg:
                return {"surcharge": 0}
            return {
                "surcharge": round(float(r.surcharge_per_kg), 2),
                "note":      r.note,
            }

        # ── none ou inconnu : pas de surcharge ────────────────
        return {"surcharge": 0}

    # ─────────────────────────────────────────────────────────

    @staticmethod
    def compute_quote_line(
        product_cost: float,
        weight_kg: float,
        shipping_method_id: int,
        category: str = None,
    ) -> dict:
        svc  = PricingService.get_service_fee(product_cost)
        ship = PricingService.get_shipping_cost(shipping_method_id, weight_kg)
        cat  = PricingService.get_category_surcharge(category, weight_kg) if category else {"surcharge": 0}

        # ── erreur transport : remonter proprement ────────────
        if "error" in ship:
            raise ValueError(ship["error"])

        svc_fee   = svc.get("amount", 0)
        ship_cost = ship.get("cost", 0) + cat.get("surcharge", 0)

        return {
            "productCost":  product_cost,
            "serviceFee":   svc_fee,
            "shippingCost": ship_cost,
            "customsFee":   0,
            "otherFee":     0,
            "total":        round(product_cost + svc_fee + ship_cost, 2),
        }