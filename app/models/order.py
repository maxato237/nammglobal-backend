"""
Commande (order).

Créée automatiquement après acceptation + paiement d'un devis.

Workflow statut :
  confirmed → supplier_ordered → in_transit_cn →
  shipped → customs → delivered   (ou issue à n'importe quel stade)
"""
import enum
from datetime import datetime
from app import db


class OrderStatus(str, enum.Enum):
    CONFIRMED        = "confirmed"        # Devis accepté & payé
    SUPPLIER_ORDERED = "supplier_ordered" # Commandé auprès du/des fournisseur(s)
    IN_TRANSIT_CN    = "in_transit_cn"    # En transit en Chine
    SHIPPED          = "shipped"          # Expédié vers le pays client
    CUSTOMS          = "customs"          # En dédouanement
    DELIVERED        = "delivered"        # Livré
    ISSUE            = "issue"            # Problème logistique


STATUS_LABELS = {
    OrderStatus.CONFIRMED:        {"label": "Confirmée & payée",    "icon": "✅"},
    OrderStatus.SUPPLIER_ORDERED: {"label": "Commandé fournisseur", "icon": "🏭"},
    OrderStatus.IN_TRANSIT_CN:    {"label": "Transit Chine",        "icon": "🚛"},
    OrderStatus.SHIPPED:          {"label": "En transit",           "icon": "✈️"},
    OrderStatus.CUSTOMS:          {"label": "Dédouanement",         "icon": "🛃"},
    OrderStatus.DELIVERED:        {"label": "Livré",                "icon": "📦"},
    OrderStatus.ISSUE:            {"label": "Problème logistique",  "icon": "⚠️"},
}


class Order(db.Model):
    __tablename__ = "orders"

    id                  = db.Column(db.Integer,       primary_key=True, autoincrement=True)
    request_id          = db.Column(db.Integer,
                                    db.ForeignKey("requests.id", ondelete="RESTRICT"),
                                    nullable=False, index=True)
    quotation_id        = db.Column(db.Integer,
                                    db.ForeignKey("quotations.id", ondelete="RESTRICT"),
                                    nullable=False, index=True)
    wave_id             = db.Column(db.String(50),
                                    db.ForeignKey("waves.id", ondelete="SET NULL"),
                                    nullable=True, index=True)

    order_number        = db.Column(db.String(100),   nullable=True, unique=True)
    status              = db.Column(
        db.Enum(OrderStatus, name="order_status"),
        default=OrderStatus.CONFIRMED,
        nullable=False,
        index=True,
    )
    total_amount        = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    tracking_number     = db.Column(db.String(255),    nullable=True)
    supplier_platform   = db.Column(db.String(100),    nullable=True)

    ordered_at          = db.Column(db.DateTime, nullable=True)
    shipped_at          = db.Column(db.DateTime, nullable=True)
    delivered_at        = db.Column(db.DateTime, nullable=True)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at          = db.Column(db.DateTime, default=datetime.utcnow,
                                    onupdate=datetime.utcnow)

    # ── Relations ────────────────────────────────────────────
    quotation       = db.relationship("Quotation",       back_populates="orders")
    wave            = db.relationship("Wave",            back_populates="orders")
    tracking_events = db.relationship("OrderTrackingEvent",
                                      back_populates="order",
                                      cascade="all, delete-orphan",
                                      order_by="OrderTrackingEvent.created_at",
                                      lazy="select")
    payments        = db.relationship("Payment",         back_populates="order",
                                      lazy="dynamic")
    supplier_orders = db.relationship("SupplierOrder",   back_populates="order",
                                      lazy="dynamic")

    # ── Business ─────────────────────────────────────────────
    def add_event(self, status: OrderStatus, title: str,
                  description: str = None, location: str = None):
        event = OrderTrackingEvent(
            order_id    = self.id,
            status      = status.value,
            title       = title,
            description = description,
            location    = location,
        )
        db.session.add(event)
        return event

    @staticmethod
    def generate_number() -> str:
        import random, time
        from datetime import date
        year = date.today().year
        ts   = str(int(time.time() * 1000))[-5:]
        rnd  = random.randint(10, 9999)
        return f"CMD-{year}-{ts}-{rnd}"

    def to_dict(self, include_events=False):
        st = STATUS_LABELS.get(self.status, {})
        data = {
            "id":               self.id,
            "requestId":        self.request_id,
            "quotationId":      self.quotation_id,
            "waveId":           self.wave_id,
            "orderNumber":      self.order_number,
            "status":           self.status.value if self.status else None,
            "statusLabel":      st.get("label"),
            "statusIcon":       st.get("icon"),
            "totalAmount":      float(self.total_amount) if self.total_amount else 0,
            "trackingNumber":   self.tracking_number,
            "supplierPlatform": self.supplier_platform,
            "orderedAt":        self.ordered_at.isoformat()   if self.ordered_at   else None,
            "shippedAt":        self.shipped_at.isoformat()   if self.shipped_at   else None,
            "deliveredAt":      self.delivered_at.isoformat() if self.delivered_at else None,
            "createdAt":        self.created_at.isoformat()   if self.created_at   else None,
        }
        if include_events:
            data["trackingEvents"] = [e.to_dict() for e in self.tracking_events]
        return data

    def __repr__(self):
        return f"<Order #{self.id} {self.order_number} status={self.status}>"


# ── OrderTrackingEvent ────────────────────────────────────────

class OrderTrackingEvent(db.Model):
    __tablename__ = "order_tracking_events"

    id          = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    order_id    = db.Column(db.Integer,
                            db.ForeignKey("orders.id", ondelete="CASCADE"),
                            nullable=False, index=True)
    status      = db.Column(db.String(50),  nullable=False)
    title       = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text,        nullable=True)
    location    = db.Column(db.String(255), nullable=True)
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)

    order = db.relationship("Order", back_populates="tracking_events")

    def to_dict(self):
        return {
            "id":          self.id,
            "orderId":     self.order_id,
            "status":      self.status,
            "title":       self.title,
            "description": self.description,
            "location":    self.location,
            "createdAt":   self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<OrderTrackingEvent #{self.id} [{self.status}] {self.title}>"
