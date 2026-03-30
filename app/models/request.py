import enum
from datetime import datetime
from app import db
from app.models.quotation import Quotation


# ============================================================
# ENUMS
# ============================================================

class RequestStatus(str, enum.Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    QUOTED     = "quoted"
    ACCEPTED   = "accepted"
    REJECTED   = "rejected"
    ORDERED    = "ordered"
    CANCELLED  = "cancelled"


REQUEST_STATUS_LABELS = {
    RequestStatus.PENDING:    {"label": "En attente",        "icon": "📝"},
    RequestStatus.PROCESSING: {"label": "En traitement",     "icon": "⚙️"},
    RequestStatus.QUOTED:     {"label": "Devis disponible",  "icon": "💰"},
    RequestStatus.ACCEPTED:   {"label": "Devis accepté",     "icon": "✅"},
    RequestStatus.REJECTED:   {"label": "Devis refusé",      "icon": "❌"},
    RequestStatus.ORDERED:    {"label": "Commandé",          "icon": "📦"},
    RequestStatus.CANCELLED:  {"label": "Annulée",           "icon": "🚫"},
}


# ============================================================
# REQUEST (container global)
# ============================================================

class Request(db.Model):
    __tablename__ = "requests"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # 🔥 clé business
    grouped = db.Column(db.Boolean, default=True)

    status = db.Column(
        db.Enum(RequestStatus, name="request_status"),
        nullable=False,
        default=RequestStatus.PENDING,
        index=True
    )

    country = db.Column(db.String(100))
    city    = db.Column(db.String(100))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    user  = db.relationship("User", back_populates="requests")
    items = db.relationship(
        "RequestItem",
        back_populates="request",
        cascade="all, delete-orphan",
        lazy="joined"
    )

    quotations = db.relationship(
        "Quotation",
        back_populates="request",
        lazy="dynamic"
    )

    # ========================================================
    # Helpers
    # ========================================================

    @property
    def active_quotation(self):
        from app.models.quotation import QuotationStatus
        return self.quotations.filter(
            Quotation.status.in_([QuotationStatus.SENT, QuotationStatus.ACCEPTED])
        )

    @staticmethod
    def update_status(request, new_status):
        request.status = new_status

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(self):
        st = REQUEST_STATUS_LABELS.get(self.status, {})

        return {
            "id": self.id,
            "userId": self.user_id,
            "grouped": self.grouped,

            "status": self.status.value if self.status else None,
            "statusLabel": st.get("label"),
            "statusIcon": st.get("icon"),

            "country": self.country,
            "city": self.city,

            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,

            "items": [item.to_dict() for item in self.items]
        }

    def __repr__(self):
        return f"<Request #{self.id} [{self.status}]>"


# ============================================================
# REQUEST ITEM (produit)
# ============================================================

class RequestItem(db.Model):
    __tablename__ = "request_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    request_id = db.Column(
        db.Integer,
        db.ForeignKey("requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Core produit
    product_link = db.Column(db.Text, nullable=False)
    quantity     = db.Column(db.Integer, default=1)

    category  = db.Column(db.String(100))
    transport = db.Column(db.String(50))
    wave_id   = db.Column(db.Integer, nullable=True)

    message = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations
    request = db.relationship("Request", back_populates="items")

    images = db.relationship(
        "RequestItemImage",
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="joined"
    )

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(self):
        return {
            "id": self.id,
            "requestId": self.request_id,

            "productLink": self.product_link,
            "quantity": self.quantity,

            "category": self.category,
            "transport": self.transport,
            "waveId": self.wave_id,

            "message": self.message,

            "images": [img.to_dict() for img in self.images]
        }

    def __repr__(self):
        return f"<RequestItem #{self.id} (Request {self.request_id})>"


# ============================================================
# IMAGES PAR ITEM
# ============================================================

class RequestItemImage(db.Model):
    __tablename__ = "request_item_images"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    item_id = db.Column(
        db.Integer,
        db.ForeignKey("request_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    image_url = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    item = db.relationship("RequestItem", back_populates="images")

    def to_dict(self):
        return {
            "id": self.id,
            "itemId": self.item_id,
            "imageUrl": self.image_url
        }

    def __repr__(self):
        return f"<RequestItemImage #{self.id}>"