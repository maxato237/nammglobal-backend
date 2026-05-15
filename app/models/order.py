"""
Commande (Order).

Workflow statut :
  confirmed → supplier_ordered → in_transit_cn →
  shipped → customs → delivered   (ou issue / cancelled)
"""
import enum
from datetime import datetime
from app import db


class OrderStatus(str, enum.Enum):
    CONFIRMED        = "confirmed"
    SUPPLIER_ORDERED = "supplier_ordered"
    IN_TRANSIT_CN    = "in_transit_cn"
    SHIPPED          = "shipped"
    CUSTOMS          = "customs"
    DELIVERED        = "delivered"
    ISSUE            = "issue"
    CANCELLED        = "cancelled"


STATUS_LABELS = {
    OrderStatus.CONFIRMED:        {"label": "Confirmée & payée",    "icon": "✅"},
    OrderStatus.SUPPLIER_ORDERED: {"label": "Commandé fournisseur", "icon": "🏭"},
    OrderStatus.IN_TRANSIT_CN:    {"label": "Transit Chine",        "icon": "🚛"},
    OrderStatus.SHIPPED:          {"label": "En transit",           "icon": "✈️"},
    OrderStatus.CUSTOMS:          {"label": "Dédouanement",         "icon": "🛃"},
    OrderStatus.DELIVERED:        {"label": "Livré",                "icon": "📦"},
    OrderStatus.ISSUE:            {"label": "Problème logistique",  "icon": "⚠️"},
    OrderStatus.CANCELLED:        {"label": "Annulée",              "icon": "🚫"},
}


# ─────────────────────────────────────────────
# ORDER
# ─────────────────────────────────────────────

class Order(db.Model):
    __tablename__ = "orders"

    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_number = db.Column(db.String(100), nullable=True, unique=True)  # CMD-2026-00001

    # Liens FK
    request_id   = db.Column(db.Integer, db.ForeignKey("requests.id",   ondelete="RESTRICT"), nullable=False, index=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey("quotations.id", ondelete="RESTRICT"), nullable=False, index=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id",      ondelete="SET NULL"), nullable=True,  index=True)
    wave_id      = db.Column(db.String(50), db.ForeignKey("waves.id",   ondelete="SET NULL"), nullable=True,  index=True)

    status = db.Column(
        db.Enum(OrderStatus, name="order_status"),
        default=OrderStatus.CONFIRMED,
        nullable=False,
        index=True,
    )

    total_amount_fcfa = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    paid_amount_fcfa  = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    tracking_number  = db.Column(db.String(255), nullable=True)
    has_issue        = db.Column(db.Boolean, default=False, nullable=False)
    issue_description = db.Column(db.Text, nullable=True)

    # Timestamps de progression
    ordered_at             = db.Column(db.DateTime, nullable=True)
    supplier_received_at   = db.Column(db.DateTime, nullable=True)
    in_transit_cn_at       = db.Column(db.DateTime, nullable=True)
    shipped_at             = db.Column(db.DateTime, nullable=True)
    customs_at             = db.Column(db.DateTime, nullable=True)
    delivered_at           = db.Column(db.DateTime, nullable=True)
    estimated_delivery_at  = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Relations ─────────────────────────────────────────────
    user            = db.relationship("User", backref=db.backref("orders", lazy="dynamic"), foreign_keys=[user_id])
    quotation       = db.relationship("Quotation", back_populates="orders")
    wave            = db.relationship("Wave", back_populates="orders")
    tracking_events = db.relationship(
        "OrderTrackingEvent",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderTrackingEvent.created_at",
        lazy="select",
    )
    messages = db.relationship(
        "OrderMessage",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderMessage.created_at",
        lazy="dynamic",
    )
    payments        = db.relationship("Payment",       back_populates="order", lazy="dynamic")
    supplier_orders = db.relationship("SupplierOrder", back_populates="order", lazy="dynamic")

    # ── Business ─────────────────────────────────────────────
    def add_event(self, status: str, title: str,
                  description: str = None, location: str = None,
                  is_public: bool = True, created_by_user_id: int = None):
        event = OrderTrackingEvent(
            order_id=self.id,
            status=status,
            title=title,
            description=description,
            location=location,
            is_public=is_public,
            created_by_user_id=created_by_user_id,
        )
        db.session.add(event)
        return event

    @staticmethod
    def generate_number(seq: int) -> str:
        from datetime import date
        year = date.today().year
        return f"CMD-{year}-{seq:05d}"

    def to_dict(self, include_events=False):
        st = STATUS_LABELS.get(self.status, {})
        data = {
            "id":                   self.id,
            "orderNumber":          self.order_number,
            "requestId":            self.request_id,
            "quotationId":          self.quotation_id,
            "userId":               self.user_id,
            "waveId":               self.wave_id,
            "status":               self.status.value if self.status else None,
            "statusLabel":          st.get("label"),
            "statusIcon":           st.get("icon"),
            "totalAmountFcfa":      float(self.total_amount_fcfa)  if self.total_amount_fcfa  else 0,
            "paidAmountFcfa":       float(self.paid_amount_fcfa)   if self.paid_amount_fcfa   else 0,
            "trackingNumber":       self.tracking_number,
            "hasIssue":             self.has_issue,
            "issueDescription":     self.issue_description,
            "orderedAt":            self.ordered_at.isoformat()            if self.ordered_at            else None,
            "supplierReceivedAt":   self.supplier_received_at.isoformat()  if self.supplier_received_at  else None,
            "inTransitCnAt":        self.in_transit_cn_at.isoformat()      if self.in_transit_cn_at      else None,
            "shippedAt":            self.shipped_at.isoformat()            if self.shipped_at            else None,
            "customsAt":            self.customs_at.isoformat()            if self.customs_at            else None,
            "deliveredAt":          self.delivered_at.isoformat()          if self.delivered_at          else None,
            "estimatedDeliveryAt":  self.estimated_delivery_at.isoformat() if self.estimated_delivery_at else None,
            "createdAt":            self.created_at.isoformat()            if self.created_at            else None,
        }
        if include_events:
            data["trackingEvents"] = [e.to_dict() for e in self.tracking_events]
        return data

    def __repr__(self):
        return f"<Order #{self.id} {self.order_number} status={self.status}>"


# ─────────────────────────────────────────────
# ORDER TRACKING EVENT
# ─────────────────────────────────────────────

class OrderTrackingEvent(db.Model):
    __tablename__ = "order_tracking_events"

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id    = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)

    status      = db.Column(db.String(50),  nullable=False)
    title       = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text,        nullable=True)
    location    = db.Column(db.String(255), nullable=True)

    # Photo optionnelle (Cloudinary)
    image_public_id = db.Column(db.String(255), nullable=True)
    image_url       = db.Column(db.Text,        nullable=True)

    is_public          = db.Column(db.Boolean, default=True, nullable=False)   # visible client ou interne admin
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order       = db.relationship("Order", back_populates="tracking_events")
    created_by  = db.relationship("User",  backref=db.backref("order_events_created", lazy="dynamic"),
                                  foreign_keys=[created_by_user_id])

    def to_dict(self):
        return {
            "id":               self.id,
            "orderId":          self.order_id,
            "status":           self.status,
            "title":            self.title,
            "description":      self.description,
            "location":         self.location,
            "imageUrl":         self.image_url,
            "isPublic":         self.is_public,
            "createdByUserId":  self.created_by_user_id,
            "createdAt":        self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<OrderTrackingEvent #{self.id} [{self.status}] {self.title}>"


# ─────────────────────────────────────────────
# ORDER MESSAGE — chat client ↔ admin
# ─────────────────────────────────────────────

class OrderMessage(db.Model):
    __tablename__ = "order_messages"

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id       = db.Column(db.Integer, db.ForeignKey("orders.id",   ondelete="CASCADE"),   nullable=False, index=True)
    sender_user_id = db.Column(db.Integer, db.ForeignKey("users.id",    ondelete="SET NULL"),  nullable=True,  index=True)

    sender_role    = db.Column(db.String(20), nullable=False)   # snapshot : 'client' | 'operator' | 'super_admin'
    content        = db.Column(db.Text, nullable=False)

    # Pièce jointe optionnelle (Cloudinary)
    attachment_url = db.Column(db.Text, nullable=True)

    is_read    = db.Column(db.Boolean,  default=False, nullable=False)
    read_at    = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Relations ─────────────────────────────────────────────
    order  = db.relationship("Order", back_populates="messages")
    sender = db.relationship("User",  backref=db.backref("order_messages_sent", lazy="dynamic"),
                             foreign_keys=[sender_user_id])

    def to_dict(self):
        return {
            "id":            self.id,
            "orderId":       self.order_id,
            "senderUserId":  self.sender_user_id,
            "senderRole":    self.sender_role,
            "content":       self.content,
            "attachmentUrl": self.attachment_url,
            "isRead":        self.is_read,
            "readAt":        self.read_at.isoformat()    if self.read_at    else None,
            "createdAt":     self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<OrderMessage #{self.id} order={self.order_id} sender={self.sender_user_id}>"
