from datetime import date, timedelta
from app import db
from app.models import Quotation, QuotationCost, QuotationStatus, RequestStatus
from app.services.notification_service import NotificationService


class QuotationService:

    @staticmethod
    def create_draft(request, data: dict) -> Quotation:
        valid_days = int(data.get("validDays", 7))

        quot = Quotation(
            request_id    = request.id,
            status        = QuotationStatus.DRAFT,
            currency      = data.get("currency", "FCFA"),
            valid_until   = date.today() + timedelta(days=valid_days),
            notes         = data.get("notes"),
            # ── champs directs du modèle ──────────────────
            quantity      = data.get("quantity", 1),
            product_cost  = data.get("productCost", 0),
            shipping_cost = data.get("shippingCost", 0),
            service_fee   = data.get("serviceFee", 0),
            customs_fee   = data.get("customsFee", 0),
            other_fee     = data.get("otherFee", 0),
        )
        db.session.add(quot)
        db.session.flush()   # obtenir quot.id avant d'ajouter les costs

        for c in (data.get("costs") or []):
            db.session.add(QuotationCost(
                quotation_id = quot.id,
                type         = c.get("type"),
                label        = c.get("label", ""),
                amount       = c.get("amount", 0),
            ))

        db.session.flush()
        quot.recompute_total()   # modifie total_amount en place
        db.session.commit()
        db.session.refresh(quot)
        return quot

    # ─────────────────────────────────────────────────────────

    @staticmethod
    def update_draft(quotation: Quotation, data: dict) -> Quotation:
        if quotation.status != QuotationStatus.DRAFT:
            raise ValueError("Seul un brouillon peut être modifié.")

        # ── champs scalaires ──────────────────────────────
        if "currency"  in data: quotation.currency      = data["currency"]
        if "notes"     in data: quotation.notes         = data["notes"]
        if "quantity"  in data: quotation.quantity      = int(data["quantity"])
        if "validDays" in data:
            quotation.valid_until = date.today() + timedelta(days=int(data["validDays"]))

        # ── champs de coûts directs ───────────────────────
        for field, key in [
            ("product_cost",  "productCost"),
            ("shipping_cost", "shippingCost"),
            ("service_fee",   "serviceFee"),
            ("customs_fee",   "customsFee"),
            ("other_fee",     "otherFee"),
        ]:
            if key in data:
                setattr(quotation, field, data[key])

        # ── costs supplémentaires ─────────────────────────
        if "costs" in data:
            QuotationCost.query.filter_by(quotation_id=quotation.id).delete()
            for c in data["costs"]:
                db.session.add(QuotationCost(
                    quotation_id = quotation.id,
                    type         = c.get("type"),
                    label        = c.get("label", ""),
                    amount       = c.get("amount", 0),
                ))

        db.session.flush()
        quotation.recompute_total()
        db.session.commit()
        db.session.refresh(quotation)
        return quotation

    # ─────────────────────────────────────────────────────────

    @staticmethod
    def send_to_client(quotation: Quotation) -> Quotation:
        if quotation.status != QuotationStatus.DRAFT:
            raise ValueError("Seul un brouillon peut être envoyé.")

        quotation.status         = QuotationStatus.SENT
        quotation.request.status = RequestStatus.QUOTED

        if quotation.request.user_id:
            NotificationService.quote_available(
                quotation.request.user_id,
                quotation.request_id,
                quotation.id,
                float(quotation.total_amount or 0),
            )

        db.session.commit()
        return quotation

    # ─────────────────────────────────────────────────────────

    @staticmethod
    def accept(quotation: Quotation) -> Quotation:
        if quotation.status != QuotationStatus.SENT:
            raise ValueError("Ce devis ne peut pas être accepté.")

        if quotation.is_expired:
            quotation.status = QuotationStatus.EXPIRED
            db.session.commit()
            raise ValueError("Ce devis a expiré.")

        quotation.status         = QuotationStatus.ACCEPTED
        quotation.request.status = RequestStatus.ACCEPTED
        db.session.commit()
        return quotation

    # ─────────────────────────────────────────────────────────

    @staticmethod
    def reject(quotation: Quotation) -> Quotation:
        if quotation.status not in (QuotationStatus.SENT,):
            raise ValueError("Seul un devis envoyé peut être refusé.")

        quotation.status         = QuotationStatus.REJECTED
        quotation.request.status = RequestStatus.REJECTED
        db.session.commit()
        return quotation