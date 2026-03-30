from datetime import datetime
from app import db
from app.models import Order, OrderStatus, QuotationStatus, RequestStatus, Request
from app.services.notification_service import NotificationService


class OrderService:

    @staticmethod
    def create_from_quotation(quotation, payment_ref: str, wave_id: str = None) -> Order:
        if quotation.status != QuotationStatus.ACCEPTED:
            raise ValueError("Le devis doit être accepté.")

        request = quotation.request
        order = Order(
            request_id   = request.id,
            quotation_id = quotation.id,
            wave_id      = wave_id,                  # ← passé en paramètre, pas depuis request
            order_number = Order.generate_number(),
            status       = OrderStatus.CONFIRMED,
            total_amount = quotation.total_amount,
            ordered_at   = datetime.utcnow(),
        )
        db.session.add(order)
        db.session.flush()

        order.add_event(                             # ← add_event, pas add_tracking
            OrderStatus.CONFIRMED,
            "Commande confirmée",
            f"Paiement reçu (réf: {payment_ref}). Commande {order.order_number} lancée.",
        )
        request.status = RequestStatus.ORDERED
        db.session.commit()
        db.session.refresh(order)

        if request.user_id:
            NotificationService.order_confirmed(request.user_id, order.id, order.order_number)
            db.session.commit()

        return order

    # ─────────────────────────────────────────────────────────

    @staticmethod
    def update_status(
        order: Order,
        new_status: OrderStatus,
        title: str,
        description: str = None,
        location: str = None,
    ) -> Order:
        order.status = new_status

        if new_status == OrderStatus.SHIPPED:        # ← SHIPPED, pas SHIPPING
            order.shipped_at = datetime.utcnow()
        elif new_status == OrderStatus.DELIVERED:
            order.delivered_at = datetime.utcnow()

        order.add_event(new_status, title, description, location)  # ← add_event

        req = order.request
        if req and req.user_id:
            if new_status == OrderStatus.SHIPPED:    # ← SHIPPED
                NotificationService.order_shipped(
                    req.user_id, order.id, order.order_number, description or ""
                )
            elif new_status == OrderStatus.DELIVERED:
                NotificationService.order_delivered(
                    req.user_id, order.id, order.order_number
                )

        db.session.commit()
        return order

    # ─────────────────────────────────────────────────────────

    @staticmethod
    def get_for_user(user_id: int, status: str = None, wave_id: str = None):
        q = db.session.query(Order).join(Order.request).filter(Request.user_id == user_id)
        if status:
            try:
                q = q.filter(Order.status == OrderStatus(status))
            except ValueError:
                pass
        if wave_id:
            q = q.filter(Order.wave_id == wave_id)
        return q.order_by(Order.created_at.desc()).all()

    # ─────────────────────────────────────────────────────────

    @staticmethod
    def get_all(status: str = None, wave_id: str = None):
        q = Order.query
        if status:
            try:
                q = q.filter(Order.status == OrderStatus(status))
            except ValueError:
                pass
        if wave_id:
            q = q.filter_by(wave_id=wave_id)
        return q.order_by(Order.created_at.desc()).all()

    # ─────────────────────────────────────────────────────────

    @staticmethod
    def set_tracking_number(order: Order, tn: str) -> Order:
        order.tracking_number = tn
        db.session.commit()
        return order