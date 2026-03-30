from app import db
from app.models import Notification

class NotificationService:
    @staticmethod
    def send(user_id, type_, title, message, meta_data=None):
        n = Notification(user_id=user_id, type=type_, title=title, message=message, meta_data=meta_data or {})
        db.session.add(n)
        return n

    @staticmethod
    def quote_available(user_id, request_id, quotation_id, total):
        return NotificationService.send(user_id, "QUOTE_AVAILABLE",
            "Votre devis est disponible !",
            f"Devis #{quotation_id} – Total : {int(total):,} FCFA. Consultez et validez.",
            {"requestId": request_id, "quotationId": quotation_id})

    @staticmethod
    def order_confirmed(user_id, order_id, order_number):
        return NotificationService.send(user_id, "ORDER_CONFIRMED",
            "Commande confirmée !",
            f"Votre commande {order_number} est en cours de traitement.",
            {"orderId": order_id})

    @staticmethod
    def order_shipped(user_id, order_id, order_number, note=""):
        return NotificationService.send(user_id, "ORDER_SHIPPED",
            "Votre commande est en route !",
            f"La commande {order_number} a quitté la Chine. {note}".strip(),
            {"orderId": order_id})

    @staticmethod
    def order_delivered(user_id, order_id, order_number):
        return NotificationService.send(user_id, "ORDER_DELIVERED",
            "Votre commande est livrée !",
            f"La commande {order_number} a été livrée. Merci de votre confiance !",
            {"orderId": order_id})

    @staticmethod
    def payment_received(user_id, order_id, amount, ref):
        return NotificationService.send(user_id, "PAYMENT_RECEIVED",
            "Paiement reçu !",
            f"Paiement de {int(amount):,} FCFA confirmé (réf: {ref}).",
            {"orderId": order_id, "ref": ref, "amount": amount})
