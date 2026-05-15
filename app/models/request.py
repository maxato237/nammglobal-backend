import enum
from datetime import datetime
from app import db


# ============================================================
# ENUMS
# ============================================================

class RequestStatus(str, enum.Enum):
    PENDING            = "pending"
    PROCESSING         = "processing"
    QUOTED             = "quoted"
    ACCEPTED           = "accepted"
    PARTIALLY_ACCEPTED = "partially_accepted"
    REJECTED           = "rejected"
    ORDERED            = "ordered"
    CANCELLED          = "cancelled"


REQUEST_STATUS_LABELS = {
    RequestStatus.PENDING:            {"label": "En attente",           "icon": "📝"},
    RequestStatus.PROCESSING:         {"label": "En traitement",        "icon": "⚙️"},
    RequestStatus.QUOTED:             {"label": "Devis disponible",     "icon": "💰"},
    RequestStatus.ACCEPTED:           {"label": "Devis accepté",        "icon": "✅"},
    RequestStatus.PARTIALLY_ACCEPTED: {"label": "Partiellement accepté","icon": "🔀"},
    RequestStatus.REJECTED:           {"label": "Devis refusé",         "icon": "❌"},
    RequestStatus.ORDERED:            {"label": "Commandé",             "icon": "📦"},
    RequestStatus.CANCELLED:          {"label": "Annulée",              "icon": "🚫"},
}


# ============================================================
# REQUEST (container global)
# ============================================================

class Request(db.Model):
    __tablename__ = "requests"

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    request_number = db.Column(db.String(30), unique=True, nullable=True, index=True)  # REQ-2026-00001

    # Lien utilisateur (nullable = demande anonyme avant inscription)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Infos invité (renseignées si user_id is NULL ou dupliquées pour snapshot)
    full_name = db.Column(db.String(255), nullable=True)
    email     = db.Column(db.String(255), nullable=True)
    phone     = db.Column(db.String(50),  nullable=True)
    whatsapp  = db.Column(db.String(50),  nullable=True)

    # Localisation
    country_code = db.Column(db.String(2), db.ForeignKey("countries.code", ondelete="SET NULL"), nullable=True, index=True)
    city         = db.Column(db.String(100), nullable=True)

    # Vague cible (indicative, non verrouillée)
    target_wave_id = db.Column(db.String(50), db.ForeignKey("waves.id", ondelete="SET NULL"), nullable=True, index=True)

    status = db.Column(
        db.Enum(RequestStatus, name="request_status"),
        nullable=False,
        default=RequestStatus.PENDING,
        index=True,
    )

    # Notes internes
    admin_notes    = db.Column(db.Text, nullable=True)
    internal_notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)   # soft delete

    # ── Relations ─────────────────────────────────────────────
    user       = db.relationship("User", back_populates="requests")
    country    = db.relationship("Country", backref=db.backref("requests", lazy="dynamic"))
    target_wave = db.relationship("Wave", backref=db.backref("target_requests", lazy="dynamic"),
                                  foreign_keys=[target_wave_id])
    items = db.relationship(
        "RequestItem",
        back_populates="request",
        cascade="all, delete-orphan",
        lazy="joined",
        order_by="RequestItem.position",
    )
    quotations = db.relationship(
        "Quotation",
        back_populates="request",
        lazy="dynamic",
    )

    # ── Helpers ───────────────────────────────────────────────
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def active_quotation(self):
        from app.models.quotation import QuotationStatus
        from app.models.quotation import Quotation
        return self.quotations.filter(
            Quotation.status.in_([QuotationStatus.SENT, QuotationStatus.ACCEPTED])
        )

    @staticmethod
    def generate_number(seq: int) -> str:
        from datetime import date
        year = date.today().year
        return f"REQ-{year}-{seq:05d}"

    def to_dict(self):
        st = REQUEST_STATUS_LABELS.get(self.status, {})
        return {
            "id":            self.id,
            "requestNumber": self.request_number,
            "userId":        self.user_id,
            "fullName":      self.full_name,
            "email":         self.email,
            "phone":         self.phone,
            "whatsapp":      self.whatsapp,
            "countryCode":   self.country_code,
            "city":          self.city,
            "targetWaveId":  self.target_wave_id,
            "status":        self.status.value if self.status else None,
            "statusLabel":   st.get("label"),
            "statusIcon":    st.get("icon"),
            "adminNotes":    self.admin_notes,
            "createdAt":     self.created_at.isoformat() if self.created_at else None,
            "updatedAt":     self.updated_at.isoformat() if self.updated_at else None,
            "items":         [item.to_dict() for item in self.items],
        }

    def __repr__(self):
        return f"<Request #{self.id} {self.request_number} [{self.status}]>"


# ============================================================
# REQUEST ITEM (1 produit dans la demande)
# ============================================================

class RequestItem(db.Model):
    __tablename__ = "request_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    request_id = db.Column(
        db.Integer,
        db.ForeignKey("requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Produit
    product_name     = db.Column(db.String(255), nullable=True)
    category         = db.Column(db.String(100), nullable=True)
    supplier_link    = db.Column(db.Text, nullable=True)
    quantity         = db.Column(db.Integer, default=1)
    color            = db.Column(db.String(100), nullable=True)
    size             = db.Column(db.String(100), nullable=True)
    target_price_cny = db.Column(db.Numeric(12, 2), nullable=True)
    notes            = db.Column(db.Text, nullable=True)
    position         = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Relations ─────────────────────────────────────────────
    request = db.relationship("Request", back_populates="items")
    images  = db.relationship(
        "RequestItemImage",
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="joined",
        order_by="RequestItemImage.position",
    )

    def to_dict(self):
        return {
            "id":              self.id,
            "requestId":       self.request_id,
            "productName":     self.product_name,
            "category":        self.category,
            "supplierLink":    self.supplier_link,
            "quantity":        self.quantity,
            "color":           self.color,
            "size":            self.size,
            "targetPriceCny":  float(self.target_price_cny) if self.target_price_cny else None,
            "notes":           self.notes,
            "position":        self.position,
            "images":          [img.to_dict() for img in self.images],
        }

    def __repr__(self):
        return f"<RequestItem #{self.id} (Request {self.request_id})>"


# ============================================================
# REQUEST ITEM IMAGE
# ============================================================

class RequestItemImage(db.Model):
    __tablename__ = "request_item_images"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    item_id = db.Column(
        db.Integer,
        db.ForeignKey("request_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    image_url            = db.Column(db.Text, nullable=False)
    cloudinary_public_id = db.Column(db.String(255), nullable=True)
    position             = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    item = db.relationship("RequestItem", back_populates="images")

    def to_dict(self):
        return {
            "id":                  self.id,
            "itemId":              self.item_id,
            "imageUrl":            self.image_url,
            "cloudinaryPublicId":  self.cloudinary_public_id,
            "position":            self.position,
        }

    def __repr__(self):
        return f"<RequestItemImage #{self.id}>"
