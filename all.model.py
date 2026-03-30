from datetime import datetime
from app import db


class GalleryItem(db.Model):
    __tablename__ = "gallery_items"
    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type         = db.Column(db.String(50),  nullable=False, default="photo")
    thumb_url    = db.Column(db.Text,        nullable=False)
    full_url     = db.Column(db.Text,        nullable=True)
    product_name = db.Column(db.String(255), nullable=False)
    category     = db.Column(db.String(100), nullable=True)
    order_date   = db.Column(db.Date,        nullable=True)
    arrival_date = db.Column(db.Date,        nullable=True)
    weight       = db.Column(db.Float,       nullable=True)
    client_name  = db.Column(db.String(255), nullable=True)
    client_city  = db.Column(db.String(100), nullable=True)
    comment      = db.Column(db.Text,        nullable=True)
    rating       = db.Column(db.Integer,     nullable=True, default=5)
    order_id     = db.Column(db.Integer,     db.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    is_published = db.Column(db.Boolean,     default=True)
    created_at   = db.Column(db.DateTime,    default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "type": self.type, "thumbUrl": self.thumb_url,
                "fullUrl": self.full_url or self.thumb_url,
                "product": self.product_name, "category": self.category,
                "orderDate": self.order_date.isoformat() if self.order_date else None,
                "arrivalDate": self.arrival_date.isoformat() if self.arrival_date else None,
                "weight": self.weight,
                "client": self.client_name,
                "clientCity": self.client_city,
                "comment": self.comment, "rating": self.rating,
                "orderId": self.order_id, "isPublished": self.is_published,
                "createdAt": self.created_at.isoformat() if self.created_at else None}
    def __repr__(self): return f"<GalleryItem #{self.id} {self.product_name}>"


from datetime import datetime
from app import db


class Notification(db.Model):
    __tablename__ = "notifications"
    id         = db.Column(db.Integer,  primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer,  db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type       = db.Column(db.String(50),  nullable=False)
    title      = db.Column(db.String(255), nullable=False)
    message    = db.Column(db.Text,        nullable=True)
    is_read    = db.Column(db.Boolean,     default=False, index=True)
    meta_data   = db.Column(db.JSON,        nullable=True)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)
    user       = db.relationship("User", back_populates="notifications")

    def to_dict(self):
        return {"id": self.id, "userId": self.user_id, "type": self.type,
                "title": self.title, "message": self.message, "read": self.is_read,
                "meta_data": self.meta_data,
                "createdAt": self.created_at.isoformat() if self.created_at else None}
    def __repr__(self): return f"<Notification #{self.id} {self.type}>"


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
    request         = db.relationship("Request",   back_populates="orders")
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
        rnd  = random.randint(10, 99)
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


import enum
from datetime import datetime
from app import db

class PaymentStatus(str, enum.Enum):
    PENDING   = "pending"
    COMPLETED = "completed"
    FAILED    = "failed"
    REFUNDED  = "refunded"

class Payment(db.Model):
    __tablename__ = "payments"
    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id        = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    amount          = db.Column(db.Numeric(12, 2), nullable=False)
    method          = db.Column(db.String(50),  nullable=True)
    status          = db.Column(db.Enum(PaymentStatus, name="payment_status"), default=PaymentStatus.PENDING, nullable=False)
    transaction_ref = db.Column(db.String(255), nullable=True, unique=True)
    created_at      = db.Column(db.DateTime,    default=datetime.utcnow)
    order           = db.relationship("Order", back_populates="payments")

    def to_dict(self):
        return {"id": self.id, "orderId": self.order_id,
                "amount": float(self.amount) if self.amount else 0,
                "method": self.method, "status": self.status.value if self.status else None,
                "transactionRef": self.transaction_ref,
                "createdAt": self.created_at.isoformat() if self.created_at else None}
    def __repr__(self): return f"<Payment #{self.id} {self.status}>"

from datetime import datetime
from app import db


class ServiceFeeRule(db.Model):
    """Tranche de frais de service NAMM (ex: 0-100k FCFA → 15%)."""
    __tablename__ = "service_fee_rules"
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    min_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    max_amount = db.Column(db.Numeric(12, 2), nullable=True)   # NULL = illimité
    percentage = db.Column(db.Float,          nullable=False)
    label      = db.Column(db.String(255),    nullable=True)
    created_at = db.Column(db.DateTime,       default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id,
                "minAmount": float(self.min_amount) if self.min_amount else 0,
                "maxAmount": float(self.max_amount) if self.max_amount else None,
                "percentage": self.percentage, "label": self.label}


class ShippingMethod(db.Model):
    """Tarif de transport par kg."""
    __tablename__ = "shipping_methods"
    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name        = db.Column(db.String(100),   nullable=False)
    timeframe   = db.Column(db.String(100),   nullable=True)
    price_per_kg= db.Column(db.Numeric(12, 2),nullable=False)
    max_kg      = db.Column(db.Numeric(12, 2),nullable=True)
    icon        = db.Column(db.String(50),    nullable=True)
    is_active   = db.Column(db.Boolean,       default=True)
    created_at  = db.Column(db.DateTime,      default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "timeframe": self.timeframe,
                "pricePerKg": float(self.price_per_kg) if self.price_per_kg else 0,
                "maxKg": float(self.max_kg) if self.max_kg else None,
                "icon": self.icon, "isActive": self.is_active}


class ProductCategoryRule(db.Model):
    """Surcharge par catégorie de produit."""
    __tablename__ = "product_category_rules"
    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_name   = db.Column(db.String(100),   nullable=False)
    surcharge_per_kg= db.Column(db.Numeric(12, 2),nullable=True, default=0)
    surcharge_type  = db.Column(db.String(50),    nullable=True)  # per_kg | fixed | none
    note            = db.Column(db.Text,           nullable=True)
    icon            = db.Column(db.String(50),    nullable=True)
    created_at      = db.Column(db.DateTime,       default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "categoryName": self.category_name,
                "surchargePerKg": float(self.surcharge_per_kg) if self.surcharge_per_kg else 0,
                "surchargeType": self.surcharge_type,
                "note": self.note, "icon": self.icon}


"""
Devis (quotation).

Workflow statut : draft → sent → accepted | rejected | expired

- Un Quotation est créé par l'admin pour une Request.
- Des QuotationCosts globaux s'ajoutent (frais fixe, assurance…).
- Quand le client l'accepte, une Order est créée automatiquement.
"""
import enum
from datetime import datetime
from decimal import Decimal
from app import db


class QuotationStatus(str, enum.Enum):
    DRAFT    = "draft"     # L'admin prépare le devis
    SENT     = "sent"      # Envoyé au client, en attente de validation
    ACCEPTED = "accepted"  # Validé par le client
    REJECTED = "rejected"  # Refusé par le client
    EXPIRED  = "expired"   # Date de validité dépassée


class Quotation(db.Model):
    __tablename__ = "quotations"

    id           = db.Column(db.Integer,       primary_key=True, autoincrement=True)
    request_id   = db.Column(db.Integer,
                             db.ForeignKey("requests.id", ondelete="CASCADE"),
                             nullable=False, index=True)
    status       = db.Column(
        db.Enum(QuotationStatus, name="quotation_status"),
        default=QuotationStatus.DRAFT,
        nullable=False,
        index=True,
    )
    currency     = db.Column(db.String(10),     nullable=False, default="FCFA")
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    valid_until  = db.Column(db.Date,           nullable=True)
    notes        = db.Column(db.Text,           nullable=True)  # Note admin
    quantity         = db.Column(db.Integer,        nullable=False, default=1)
    product_cost     = db.Column(db.Numeric(12, 2), nullable=True, default=0)
    shipping_cost    = db.Column(db.Numeric(12, 2), nullable=True, default=0)
    service_fee      = db.Column(db.Numeric(12, 2), nullable=True, default=0)
    customs_fee      = db.Column(db.Numeric(12, 2), nullable=True, default=0)
    other_fee        = db.Column(db.Numeric(12, 2), nullable=True, default=0)

    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow,
                             onupdate=datetime.utcnow)

    # ── Relations ────────────────────────────────────────────
    request = db.relationship("Request", back_populates="quotations")
    costs   = db.relationship("QuotationCost", back_populates="quotation",
                              cascade="all, delete-orphan", lazy="select")
    orders  = db.relationship("Order",         back_populates="quotation",
                              lazy="dynamic")

    # ── Business ─────────────────────────────────────────────
    def recompute_total(self):
        """Recalcule total_amount à partir des items + costs."""
        costs_total = sum(
            (c.amount or Decimal("0")) for c in self.costs
        )
        self.total_amount = (self.product_cost or Decimal("0")) + (self.shipping_cost or Decimal("0")) + (self.service_fee or Decimal("0")) + (self.customs_fee or Decimal("0")) + (self.other_fee or Decimal("0")) + costs_total

    @property
    def is_expired(self) -> bool:
        from datetime import date
        if self.valid_until and self.valid_until < date.today():
            return True
        return False

    def to_dict(self, include_items=True, include_costs=True):
        data = {
            "id":          self.id,
            "requestId":   self.request_id,
            "status":      self.status.value if self.status else None,
            "currency":    self.currency,
            "totalAmount": float(self.total_amount) if self.total_amount else 0,
            "productCost": float(self.product_cost) if self.product_cost else 0,
            "shippingCost": float(self.shipping_cost) if self.shipping_cost else 0,
            "serviceFee":  float(self.service_fee) if self.service_fee else 0,
            "customsFee":  float(self.customs_fee) if self.customs_fee else 0,
            "otherFee":    float(self.other_fee) if self.other_fee else 0,
            "quantity":    self.quantity,
            "validUntil":  self.valid_until.isoformat() if self.valid_until else None,
            "notes":       self.notes,
            "isExpired":   self.is_expired,
            "createdAt":   self.created_at.isoformat() if self.created_at else None,
            "updatedAt":   self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_costs:
            data["costs"] = [c.to_dict() for c in self.costs]
        return data

    def __repr__(self):
        return f"<Quotation #{self.id} request={self.request_id} status={self.status}>"


# ── QuotationCost ─────────────────────────────────────────────

class QuotationCost(db.Model):
    """Coût global supplémentaire sur un devis (assurance, manutention…)."""
    __tablename__ = "quotation_costs"

    id           = db.Column(db.Integer,       primary_key=True, autoincrement=True)
    quotation_id = db.Column(db.Integer,
                             db.ForeignKey("quotations.id", ondelete="CASCADE"),
                             nullable=False, index=True)
    type         = db.Column(db.String(50),    nullable=True)    # assurance, manutention…
    label        = db.Column(db.String(255),   nullable=False)
    amount       = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    created_at   = db.Column(db.DateTime,       default=datetime.utcnow)

    quotation = db.relationship("Quotation", back_populates="costs")

    def to_dict(self):
        return {
            "id":          self.id,
            "quotationId": self.quotation_id,
            "type":        self.type,
            "label":       self.label,
            "amount":      float(self.amount) if self.amount else 0,
        }

    def __repr__(self):
        return f"<QuotationCost #{self.id} {self.label}={self.amount}>"


from app import db
from datetime import datetime
import enum

class RequestStatus(str, enum.Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    QUOTED     = "quoted"
    ACCEPTED   = "accepted"
    REJECTED   = "rejected"
    ORDERED    = "ordered"
    CANCELLED  = "cancelled"

REQUEST_STATUS_LABELS = {
    RequestStatus.PENDING:    {"label":"En attente",        "icon":"📝"},
    RequestStatus.PROCESSING: {"label":"En traitement",     "icon":"⚙️"},
    RequestStatus.QUOTED:     {"label":"Devis disponible",  "icon":"💰"},
    RequestStatus.ACCEPTED:   {"label":"Devis accepté",     "icon":"✅"},
    RequestStatus.REJECTED:   {"label":"Devis refusé",      "icon":"❌"},
    RequestStatus.ORDERED:    {"label":"Commandé",          "icon":"📦"},
    RequestStatus.CANCELLED:  {"label":"Annulée",           "icon":"🚫"},
}

class Request(db.Model):
    __tablename__ = "requests"
    id         = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer,     db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    full_name  = db.Column(db.String(255), nullable=False)
    whatsapp   = db.Column(db.String(50),  nullable=True)
    country    = db.Column(db.String(100), nullable=True)
    city       = db.Column(db.String(100), nullable=True)
    notes      = db.Column(db.Text,        nullable=True)
    quantity     = db.Column(db.Integer,     nullable=True, default=1)
    status     = db.Column(db.Enum(RequestStatus, name="request_status"),
                            nullable=False, default=RequestStatus.PENDING, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    quotations = db.relationship("Quotation", back_populates="request", lazy="dynamic")

    user       = db.relationship("User",          back_populates="requests")
    images     = db.relationship("RequestItemImage",  back_populates="request",
                                  lazy="joined",  cascade="all, delete-orphan")

    @property
    def active_quotation(self):
        return (self.quotations
                .filter_by(is_active=True)
                .order_by(db.desc("created_at"))
                .first())

    @staticmethod
    def update_status(request, new_status):
        request.status = new_status

    def to_dict(self, include_images=True):
        st = REQUEST_STATUS_LABELS.get(self.status, {})
        data = {
            "id":self.id,
            "userId":self.user_id,
            "fullName":self.full_name,
            "whatsapp":self.whatsapp,
            "country":self.country,"city":self.city,"notes":self.notes,
            "status":self.status.value if self.status else None,
            "statusLabel":st.get("label"),"statusIcon":st.get("icon"),
            "createdAt":self.created_at.isoformat() if self.created_at else None,
            "updatedAt":self.updated_at.isoformat() if self.updated_at else None,
            "quantity":self.quantity
        }
        
        if include_images: data["images"] = [img.to_dict() for img in self.images]
        return data

    def __repr__(self): return f"<Request #{self.id} [{self.status}]>"

class RequestItemImage(db.Model):
    __tablename__ = "request_images"
    id         = db.Column(db.Integer,  primary_key=True, autoincrement=True)
    request_id = db.Column(db.Integer,  db.ForeignKey("requests.id"), nullable=False, index=True)
    image_url  = db.Column(db.Text,     nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    request = db.relationship("Request", back_populates="images")

    def to_dict(self):
        return {"id":self.id,"requestId":self.request_id,"imageUrl":self.image_url}


from app import db
from datetime import datetime
import enum

class RequestStatus(str, enum.Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    QUOTED     = "quoted"
    ACCEPTED   = "accepted"
    REJECTED   = "rejected"
    ORDERED    = "ordered"
    CANCELLED  = "cancelled"

REQUEST_STATUS_LABELS = {
    RequestStatus.PENDING:    {"label":"En attente",        "icon":"📝"},
    RequestStatus.PROCESSING: {"label":"En traitement",     "icon":"⚙️"},
    RequestStatus.QUOTED:     {"label":"Devis disponible",  "icon":"💰"},
    RequestStatus.ACCEPTED:   {"label":"Devis accepté",     "icon":"✅"},
    RequestStatus.REJECTED:   {"label":"Devis refusé",      "icon":"❌"},
    RequestStatus.ORDERED:    {"label":"Commandé",          "icon":"📦"},
    RequestStatus.CANCELLED:  {"label":"Annulée",           "icon":"🚫"},
}

class Request(db.Model):
    __tablename__ = "requests"
    id         = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer,     db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    full_name  = db.Column(db.String(255), nullable=False)
    whatsapp   = db.Column(db.String(50),  nullable=True)
    country    = db.Column(db.String(100), nullable=True)
    city       = db.Column(db.String(100), nullable=True)
    notes      = db.Column(db.Text,        nullable=True)
    quantity     = db.Column(db.Integer,     nullable=True, default=1)
    status     = db.Column(db.Enum(RequestStatus, name="request_status"),
                            nullable=False, default=RequestStatus.PENDING, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    quotations = db.relationship("Quotation", back_populates="request", lazy="dynamic")

    user       = db.relationship("User",          back_populates="requests")
    images     = db.relationship("RequestItemImage",  back_populates="request",
                                  lazy="joined",  cascade="all, delete-orphan")

    @property
    def active_quotation(self):
        return (self.quotations
                .filter_by(is_active=True)
                .order_by(db.desc("created_at"))
                .first())

    @staticmethod
    def update_status(request, new_status):
        request.status = new_status

    def to_dict(self, include_images=True):
        st = REQUEST_STATUS_LABELS.get(self.status, {})
        data = {
            "id":self.id,
            "userId":self.user_id,
            "fullName":self.full_name,
            "whatsapp":self.whatsapp,
            "country":self.country,"city":self.city,"notes":self.notes,
            "status":self.status.value if self.status else None,
            "statusLabel":st.get("label"),"statusIcon":st.get("icon"),
            "createdAt":self.created_at.isoformat() if self.created_at else None,
            "updatedAt":self.updated_at.isoformat() if self.updated_at else None,
            "quantity":self.quantity
        }
        
        if include_images: data["images"] = [img.to_dict() for img in self.images]
        return data

    def __repr__(self): return f"<Request #{self.id} [{self.status}]>"

class RequestItemImage(db.Model):
    __tablename__ = "request_images"
    id         = db.Column(db.Integer,  primary_key=True, autoincrement=True)
    request_id = db.Column(db.Integer,  db.ForeignKey("requests.id"), nullable=False, index=True)
    image_url  = db.Column(db.Text,     nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    request = db.relationship("Request", back_populates="images")

    def to_dict(self):
        return {"id":self.id,"requestId":self.request_id,"imageUrl":self.image_url}


from datetime import datetime
from app import db


class Stat(db.Model):
    """Statistiques affichées sur la page d'accueil (gérées par l'admin)."""
    __tablename__ = "stats"
    id         = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    value      = db.Column(db.Integer,     nullable=False, default=0)
    suffix     = db.Column(db.String(10),  nullable=True)
    label      = db.Column(db.String(255), nullable=False)
    icon       = db.Column(db.String(50),  nullable=True)
    is_active  = db.Column(db.Boolean,     default=True)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "value": self.value, "suffix": self.suffix,
                "label": self.label, "icon": self.icon, "isActive": self.is_active}
    def __repr__(self): return f"<Stat {self.label}={self.value}>"


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
    quotation_item_id = db.Column(db.Integer, db.ForeignKey("quotation_items.id", ondelete="SET NULL"), nullable=True)
    product_name      = db.Column(db.String(255), nullable=False)
    quantity          = db.Column(db.Integer, nullable=False, default=1)
    unit_price        = db.Column(db.Numeric(12, 2), nullable=True)
    total_price       = db.Column(db.Numeric(12, 2), nullable=True)
    notes             = db.Column(db.Text, nullable=True)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    supplier_order = db.relationship("SupplierOrder", back_populates="items")

    def to_dict(self):
        return {"id": self.id, "supplierOrderId": self.supplier_order_id,
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


from datetime import datetime
from app import db, bcrypt
import re


class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    full_name     = db.Column(db.String(255), nullable=False)
    phone         = db.Column(db.String(50),  nullable=True, unique=True, index=True)
    whatsapp      = db.Column(db.String(50),  nullable=True)
    email         = db.Column(db.String(255), nullable=True, unique=True, index=True)
    country       = db.Column(db.String(100), nullable=True)
    city          = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.Text,        nullable=False)
    role          = db.Column(db.String(50),  nullable=False, default="client")  # "client" | "admin"
    is_active     = db.Column(db.Boolean,     default=True,   nullable=False)
    created_at    = db.Column(db.DateTime,    default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime,    default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Relations ─────────────────────────────────────────────
    requests      = db.relationship("Request",      back_populates="user", lazy="dynamic")
    notifications = db.relationship("Notification", back_populates="user", lazy="dynamic")

    # ── Password ──────────────────────────────────────────────
    def set_password(self, plain: str):
        self.password_hash = bcrypt.generate_password_hash(plain).decode("utf-8")

    def check_password(self, plain: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, plain)

    # ── Helpers ───────────────────────────────────────────────
    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def avatar(self) -> str:
        parts = (self.full_name or "?").strip().split()
        return "".join(p[0].upper() for p in parts[:2])

    @property
    def is_profile_complete(self) -> bool:
        return bool(self.full_name and self.phone and self.country and self.city)

    def to_dict(self):
        return {
            "id":              self.id,
            "fullName":        self.full_name,
            "phone":           self.phone,
            "whatsapp":        self.whatsapp,
            "email":           self.email,
            "country":         self.country,
            "city":            self.city,
            "role":            self.role,
            "avatar":          self.avatar,
            "profileComplete": self.is_profile_complete,
            "createdAt":       self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User #{self.id} {self.full_name} [{self.role}]>"


from datetime import datetime, date
from app import db


class Wave(db.Model):
    __tablename__ = "waves"

    id             = db.Column(db.String(50),  primary_key=True)
    name           = db.Column(db.String(100), nullable=False)
    deadline_date  = db.Column(db.Date,        nullable=False)
    shipping_date  = db.Column(db.Date,        nullable=False)
    arrival_date   = db.Column(db.Date,        nullable=False)
    transport_type = db.Column(db.String(100), nullable=True)
    notes          = db.Column(db.Text,        nullable=True)
    is_active      = db.Column(db.Boolean,     default=True, nullable=False)
    created_at     = db.Column(db.DateTime,    default=datetime.utcnow)

    orders = db.relationship("Order", back_populates="wave", lazy="dynamic")

    @property
    def is_open(self) -> bool:
        return self.is_active and self.deadline_date >= date.today()

    @property
    def days_left(self) -> int:
        return max((self.deadline_date - date.today()).days, 0)

    @staticmethod
    def generate_id() -> str:
        import uuid
        return "WAVE-" + str(uuid.uuid4())[:8].upper()

    def to_dict(self):
        return {
            "id":            self.id,
            "name":          self.name,
            "deadlineDate":  self.deadline_date.isoformat()  if self.deadline_date else None,
            "shippingDate":  self.shipping_date.isoformat()  if self.shipping_date else None,
            "arrivalDate":   self.arrival_date.isoformat()   if self.arrival_date  else None,
            "transportType": self.transport_type,
            "notes":         self.notes,
            "isActive":      self.is_active,
            "isOpen":        self.is_open,
            "daysLeft":      self.days_left,
        }

    def __repr__(self):
        return f"<Wave {self.id} {self.name}>"

