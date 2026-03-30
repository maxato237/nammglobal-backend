from app import db
from app.models import Payment, PaymentStatus, Quotation, QuotationStatus
from app.services.order_service import OrderService
from app.services.notification_service import NotificationService


class PaymentService:

    @staticmethod
    def _payment_exists(transaction_ref: str) -> bool:
        """Vérifie l'idempotence : évite les doublons sur webhook rejoué."""
        return Payment.query.filter_by(transaction_ref=transaction_ref).first() is not None

    # ─────────────────────────────────────────────────────────

    @staticmethod
    def verify_and_confirm(quotation_id: int, flw_ref: str, amount: float, method: str):
        quotation = Quotation.query.get(quotation_id)
        if not quotation:
            raise ValueError("Devis introuvable.")
        if quotation.status != QuotationStatus.ACCEPTED:
            raise ValueError("Devis non accepté.")

        # ── idempotence ───────────────────────────────────────
        if PaymentService._payment_exists(flw_ref):
            raise ValueError("Ce paiement a déjà été enregistré.")

        try:
            order = OrderService.create_from_quotation(quotation, flw_ref)

            db.session.add(Payment(
                order_id        = order.id,
                amount          = amount,
                method          = method,
                status          = PaymentStatus.COMPLETED,
                transaction_ref = flw_ref,
                # ← pas de metadata, colonne inexistante dans le modèle
            ))

            request = quotation.request
            if request and request.user_id:
                NotificationService.payment_received(
                    request.user_id, order.id, amount, flw_ref
                )

            db.session.commit()
            return order

        except Exception as e:
            db.session.rollback()
            raise e

    # ─────────────────────────────────────────────────────────

    @staticmethod
    def handle_flw_webhook(payload: dict):
        data    = payload.get("data", {})
        status  = data.get("status", "")
        tx_ref  = data.get("tx_ref", "")
        flw_ref = data.get("flw_ref", "")
        amount  = float(data.get("amount", 0))

        if status != "successful":
            return False, "Paiement non réussi.", None
        if not tx_ref.startswith("PAY-"):
            return False, "tx_ref invalide.", None

        try:
            quotation_id = int(tx_ref.split("-")[1])
        except (IndexError, ValueError):
            return False, "Impossible de parser le quotation_id.", None

        # ── idempotence ───────────────────────────────────────
        if PaymentService._payment_exists(flw_ref):
            existing_payment = Payment.query.filter_by(transaction_ref=flw_ref).first()
            return True, "Paiement déjà traité.", existing_payment.order

        quotation = Quotation.query.get(quotation_id)
        if not quotation:
            return False, "Devis introuvable.", None
        if quotation.status != QuotationStatus.ACCEPTED:
            return False, "Devis non accepté.", None

        try:
            order = OrderService.create_from_quotation(quotation, flw_ref)

            db.session.add(Payment(
                order_id        = order.id,
                amount          = amount,
                method          = data.get("payment_type"),
                status          = PaymentStatus.COMPLETED,
                transaction_ref = flw_ref,
                # ← metadata supprimé, colonne inexistante dans le modèle
            ))

            request = quotation.request
            if request and request.user_id:
                NotificationService.payment_received(
                    request.user_id, order.id, amount, flw_ref
                )

            db.session.commit()
            return True, "Commande créée.", order

        except Exception as e:
            db.session.rollback()
            return False, str(e), None