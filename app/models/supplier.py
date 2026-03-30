"""
Fournisseurs (suppliers).
Multi-supplier support : un Order peut avoir plusieurs SupplierOrders.
"""
from datetime import datetime
from app import db


class Supplier(db.Model):
    __tablename__ = "suppliers"
    id                = db.Column(db.Integer,      primary_key=True, autoincrement=True)
    name              = db.Column(db.String(255),  nullable=False)
    platform          = db.Column(db.String(100),  nullable=True)
    store_link        = db.Column(db.Text,         nullable=True)
    contact_name      = db.Column(db.String(255),  nullable=True)
    contact_whatsapp  = db.Column(db.String(50),   nullable=True)
    rating            = db.Column(db.Float,        nullable=True)
    notes             = db.Column(db.Text,         nullable=True)
    avg_delivery_time = db.Column(db.Integer,      nullable=True)
    success_rate      = db.Column(db.Float,        nullable=True)
    total_orders      = db.Column(db.Integer,      default=0)
    blacklisted       = db.Column(db.Boolean,      default=False)
    created_at        = db.Column(db.DateTime,     default=datetime.utcnow)
    supplier_orders   = db.relationship("SupplierOrder", back_populates="supplier", lazy="dynamic")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "platform": self.platform,
                "storeLink": self.store_link, "contactName": self.contact_name,
                "contactWhatsapp": self.contact_whatsapp, "rating": self.rating,
                "notes": self.notes, "avgDeliveryTime": self.avg_delivery_time,
                "successRate": self.success_rate, "totalOrders": self.total_orders,
                "blacklisted": self.blacklisted,
                "createdAt": self.created_at.isoformat() if self.created_at else None}
    def __repr__(self): return f"<Supplier #{self.id} {self.name}>"


class SupplierOrder(db.Model):
    __tablename__ = "supplier_orders"
    id                = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id          = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id       = db.Column(db.Integer, db.ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True)
    supplier_name     = db.Column(db.String(255), nullable=True)
    supplier_platform = db.Column(db.String(100), nullable=True)
    supplier_link     = db.Column(db.Text, nullable=True)
    status            = db.Column(db.String(50), nullable=False, default="pending")
    total_amount      = db.Column(db.Numeric(12, 2), nullable=True)
    currency          = db.Column(db.String(10), nullable=True, default="CNY")
    ordered_at        = db.Column(db.DateTime, nullable=True)
    received_at       = db.Column(db.DateTime, nullable=True)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    order    = db.relationship("Order",    back_populates="supplier_orders")
    supplier = db.relationship("Supplier", back_populates="supplier_orders")
    items    = db.relationship("SupplierOrderItem",     back_populates="supplier_order", cascade="all, delete-orphan", lazy="select")
    tracking = db.relationship("SupplierOrderTracking", back_populates="supplier_order", cascade="all, delete-orphan", order_by="SupplierOrderTracking.created_at", lazy="select")

    def to_dict(self, include_items=True):
        data = {"id": self.id, "orderId": self.order_id, "supplierId": self.supplier_id,
                "supplierName": self.supplier_name, "supplierPlatform": self.supplier_platform,
                "supplierLink": self.supplier_link, "status": self.status,
                "totalAmount": float(self.total_amount) if self.total_amount else None,
                "currency": self.currency,
                "orderedAt": self.ordered_at.isoformat() if self.ordered_at else None,
                "receivedAt": self.received_at.isoformat() if self.received_at else None,
                "createdAt": self.created_at.isoformat() if self.created_at else None,
                "tracking": [t.to_dict() for t in self.tracking]}
        if include_items:
            data["items"] = [i.to_dict() for i in self.items]
        return data
    def __repr__(self): return f"<SupplierOrder #{self.id}>"


class SupplierOrderItem(db.Model):
    __tablename__ = "supplier_order_items"
    id                = db.Column(db.Integer, primary_key=True, autoincrement=True)
    supplier_order_id = db.Column(db.Integer, db.ForeignKey("supplier_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_name      = db.Column(db.String(255), nullable=False)
    quantity          = db.Column(db.Integer, nullable=False, default=1)
    unit_price        = db.Column(db.Numeric(12, 2), nullable=True)
    total_price       = db.Column(db.Numeric(12, 2), nullable=True)
    notes             = db.Column(db.Text, nullable=True)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    supplier_order = db.relationship("SupplierOrder", back_populates="items")

    def to_dict(self):
        return {"id": self.id, "supplierOrderId": self.supplier_order_id,
                "productName": self.product_name,
                "quantity": self.quantity,
                "unitPrice": float(self.unit_price) if self.unit_price else None,
                "totalPrice": float(self.total_price) if self.total_price else None,
                "notes": self.notes}


class SupplierOrderTracking(db.Model):
    __tablename__ = "supplier_order_tracking"
    id                = db.Column(db.Integer, primary_key=True, autoincrement=True)
    supplier_order_id = db.Column(db.Integer, db.ForeignKey("supplier_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    status            = db.Column(db.String(50), nullable=False)
    comment           = db.Column(db.Text, nullable=True)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    supplier_order = db.relationship("SupplierOrder", back_populates="tracking")

    def to_dict(self):
        return {"id": self.id, "supplierOrderId": self.supplier_order_id,
                "status": self.status, "comment": self.comment,
                "createdAt": self.created_at.isoformat() if self.created_at else None}
