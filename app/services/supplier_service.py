from datetime import datetime
from app import db
from app.models import Supplier, SupplierOrder, SupplierOrderItem, SupplierOrderTracking, Order
from sqlalchemy import func


# Statuts en constantes string, cohérent avec String(50) dans le modèle
class SupplierOrderStatus:
    PENDING   = "pending"
    ORDERED   = "ordered"
    SHIPPED   = "shipped"
    RECEIVED  = "received"
    CANCELLED = "cancelled"


class SupplierService:

    @staticmethod
    def create(data: dict) -> Supplier:
        s = Supplier(
            name              = data.get("name", ""),
            platform          = data.get("platform"),
            store_link        = data.get("storeLink"),
            contact_name      = data.get("contactName"),
            contact_whatsapp  = data.get("contactWhatsapp"),
            rating            = data.get("rating"),
            notes             = data.get("notes"),
            avg_delivery_time = data.get("avgDeliveryTime"),
            success_rate      = data.get("successRate"),
            # ── champs ignorés dans l'ancienne version ──
            blacklisted       = data.get("blacklisted", False),
            total_orders      = 0,
        )
        db.session.add(s)
        db.session.commit()
        return s

    # ─────────────────────────────────────────────────────────

    @staticmethod
    def update(supplier: Supplier, data: dict) -> Supplier:
        for json_k, attr in [
            ("name",            "name"),
            ("platform",        "platform"),
            ("storeLink",       "store_link"),
            ("contactName",     "contact_name"),
            ("contactWhatsapp", "contact_whatsapp"),
            ("rating",          "rating"),
            ("notes",           "notes"),
            ("avgDeliveryTime", "avg_delivery_time"),
            ("successRate",     "success_rate"),
            ("blacklisted",     "blacklisted"),
        ]:
            if json_k in data:
                setattr(supplier, attr, data[json_k])
        db.session.commit()
        return supplier

    # ─────────────────────────────────────────────────────────

    @staticmethod
    def delete(supplier: Supplier):
        db.session.delete(supplier)
        db.session.commit()

    # ─────────────────────────────────────────────────────────

    @staticmethod
    def create_supplier_order(order: Order, data: dict) -> SupplierOrder:
        so = SupplierOrder(
            order_id          = order.id,
            supplier_id       = data.get("supplierId"),
            supplier_name     = data.get("supplierName", ""),
            supplier_platform = data.get("supplierPlatform"),
            supplier_link     = data.get("supplierLink"),
            total_amount      = data.get("totalAmount"),
            currency          = data.get("currency", "CNY"),
            status            = SupplierOrderStatus.PENDING,
        )
        db.session.add(so)
        db.session.flush()

        for i in (data.get("items") or []):
            db.session.add(SupplierOrderItem(
                supplier_order_id = so.id,
                product_name      = i.get("productName", ""),
                quantity          = i.get("quantity", 1),
                unit_price        = i.get("unitPrice"),
                total_price       = i.get("totalPrice"),
                notes             = i.get("notes"),
            ))

        # ── incrément sécurisé avec coalesce ──────────────────
        if so.supplier_id:
            Supplier.query.filter_by(id=so.supplier_id).update(
                {"total_orders": func.coalesce(Supplier.total_orders, 0) + 1}
            )

        db.session.commit()
        db.session.refresh(so)
        return so

    # ─────────────────────────────────────────────────────────

    @staticmethod
    def update_status(
        supplier_order: SupplierOrder,
        new_status: str,
        comment: str = None,
    ) -> SupplierOrder:
        supplier_order.status = new_status

        # ── timestamps selon le statut ────────────────────────
        if new_status == SupplierOrderStatus.ORDERED:
            supplier_order.ordered_at  = datetime.utcnow()
        elif new_status == SupplierOrderStatus.RECEIVED:
            supplier_order.received_at = datetime.utcnow()

        # ── entrée de tracking ────────────────────────────────
        db.session.add(SupplierOrderTracking(
            supplier_order_id = supplier_order.id,
            status            = new_status,
            comment           = comment,
        ))

        db.session.commit()
        return supplier_order