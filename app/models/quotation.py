"""
Devis (Quotation) — déconsolidable par produit.

Workflow :
  draft → sent → accepted | partially_accepted | rejected | expired

- Un Quotation est lié à une Request
- Contient des QuotationItem (1 par RequestItem) pour la déconsolidation
- Peut contenir des QuotationCost (frais globaux : assurance, manutention…)
- Chaque révision est archivée dans QuotationRevision
"""

import enum
from datetime import datetime, date
from decimal import Decimal
from app import db


# ─────────────────────────────────────────────
# ENUM
# ─────────────────────────────────────────────

class QuotationStatus(str, enum.Enum):
    DRAFT              = "draft"
    SENT               = "sent"
    ACCEPTED           = "accepted"
    PARTIALLY_ACCEPTED = "partially_accepted"
    REJECTED           = "rejected"
    EXPIRED            = "expired"


# ─────────────────────────────────────────────
# QUOTATION
# ─────────────────────────────────────────────

class Quotation(db.Model):
    __tablename__ = "quotations"

    id               = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quotation_number = db.Column(db.String(30), unique=True, nullable=True, index=True)  # DEV-2026-00001

    request_id = db.Column(
        db.Integer,
        db.ForeignKey("requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Snapshot pays au moment de l'envoi
    country_code = db.Column(db.String(2), db.ForeignKey("countries.code", ondelete="SET NULL"), nullable=True, index=True)

    status = db.Column(
        db.Enum(QuotationStatus, name="quotation_status"),
        default=QuotationStatus.DRAFT,
        nullable=False,
        index=True,
    )

    currency = db.Column(db.String(10), nullable=False, default="FCFA")

    # Snapshot du taux de change utilisé pour le calcul
    exchange_rate_cny_fcfa = db.Column(db.Numeric(12, 6), nullable=True)

    # Coûts détaillés en FCFA
    total_products_cost_fcfa  = db.Column(db.Numeric(12, 2), default=0)
    total_shipping_cost_fcfa  = db.Column(db.Numeric(12, 2), default=0)
    total_service_fee_fcfa    = db.Column(db.Numeric(12, 2), default=0)
    total_customs_fee_fcfa    = db.Column(db.Numeric(12, 2), default=0)
    total_other_fee_fcfa      = db.Column(db.Numeric(12, 2), default=0)
    total_amount_fcfa         = db.Column(db.Numeric(12, 2), default=0)

    # Tranche de commission appliquée (snapshot)
    applied_service_fee_tier_pct = db.Column(db.Float, nullable=True)

    valid_until  = db.Column(db.Date,     nullable=True)
    sent_at      = db.Column(db.DateTime, nullable=True)
    accepted_at  = db.Column(db.DateTime, nullable=True)

    admin_notes  = db.Column(db.Text, nullable=True)
    client_notes = db.Column(db.Text, nullable=True)

    # PDF Cloudinary
    pdf_public_id = db.Column(db.String(255), nullable=True)
    pdf_url       = db.Column(db.Text,        nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Relations ─────────────────────────────────────────────
    request = db.relationship("Request", back_populates="quotations")
    country = db.relationship("Country", backref=db.backref("quotations", lazy="dynamic"))

    items = db.relationship(
        "QuotationItem",
        back_populates="quotation",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="QuotationItem.id",
    )
    costs = db.relationship(
        "QuotationCost",
        back_populates="quotation",
        cascade="all, delete-orphan",
        lazy="select",
    )
    orders = db.relationship(
        "Order",
        back_populates="quotation",
        lazy="select",
    )
    revisions = db.relationship(
        "QuotationRevision",
        back_populates="quotation",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="QuotationRevision.revision_number",
    )

    # ── Business ──────────────────────────────────────────────
    def recompute_total(self):
        costs_total = sum((c.amount_fcfa or Decimal("0")) for c in self.costs)
        self.total_amount_fcfa = (
            (self.total_products_cost_fcfa or Decimal("0")) +
            (self.total_shipping_cost_fcfa or Decimal("0")) +
            (self.total_service_fee_fcfa   or Decimal("0")) +
            (self.total_customs_fee_fcfa   or Decimal("0")) +
            (self.total_other_fee_fcfa     or Decimal("0")) +
            costs_total
        )

    @property
    def is_expired(self) -> bool:
        return bool(self.valid_until and self.valid_until < date.today())

    @staticmethod
    def generate_number(seq: int) -> str:
        year = date.today().year
        return f"DEV-{year}-{seq:05d}"

    def to_dict(self, include_items=True, include_costs=True):
        data = {
            "id":                       self.id,
            "quotationNumber":          self.quotation_number,
            "requestId":                self.request_id,
            "countryCode":              self.country_code,
            "status":                   self.status.value if self.status else None,
            "currency":                 self.currency,
            "exchangeRateCnyFcfa":      float(self.exchange_rate_cny_fcfa) if self.exchange_rate_cny_fcfa else None,
            "totalProductsCostFcfa":    float(self.total_products_cost_fcfa or 0),
            "totalShippingCostFcfa":    float(self.total_shipping_cost_fcfa or 0),
            "totalServiceFeeFcfa":      float(self.total_service_fee_fcfa   or 0),
            "totalCustomsFeeFcfa":      float(self.total_customs_fee_fcfa   or 0),
            "totalOtherFeeFcfa":        float(self.total_other_fee_fcfa     or 0),
            "totalAmountFcfa":          float(self.total_amount_fcfa        or 0),
            "appliedServiceFeeTierPct": self.applied_service_fee_tier_pct,
            "validUntil":               self.valid_until.isoformat() if self.valid_until else None,
            "sentAt":                   self.sent_at.isoformat()     if self.sent_at     else None,
            "acceptedAt":               self.accepted_at.isoformat() if self.accepted_at else None,
            "clientNotes":              self.client_notes,
            "pdfUrl":                   self.pdf_url,
            "isExpired":                self.is_expired,
            "createdAt":                self.created_at.isoformat()  if self.created_at  else None,
            "updatedAt":                self.updated_at.isoformat()  if self.updated_at  else None,
        }
        if include_items:
            data["items"] = [i.to_dict() for i in self.items]
        if include_costs:
            data["costs"] = [c.to_dict() for c in self.costs]
        return data

    def __repr__(self):
        return f"<Quotation #{self.id} {self.quotation_number} status={self.status}>"


# ─────────────────────────────────────────────
# QUOTATION ITEM — 1 ligne par produit (déconsolidation)
# ─────────────────────────────────────────────

class QuotationItem(db.Model):
    __tablename__ = "quotation_items"

    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quotation_id = db.Column(
        db.Integer,
        db.ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    request_item_id = db.Column(
        db.Integer,
        db.ForeignKey("request_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    product_name = db.Column(db.String(255), nullable=False)
    quantity     = db.Column(db.Integer,     nullable=False, default=1)
    weight_kg    = db.Column(db.Numeric(12, 2), nullable=True)
    category     = db.Column(db.String(100), nullable=True)

    # Coûts unitaires
    unit_cost_cny            = db.Column(db.Numeric(12, 2), nullable=True)
    unit_cost_fcfa           = db.Column(db.Numeric(12, 2), nullable=True)
    shipping_per_unit_fcfa   = db.Column(db.Numeric(12, 2), nullable=True)
    customs_per_unit_fcfa    = db.Column(db.Numeric(12, 2), nullable=True)
    subtotal_fcfa            = db.Column(db.Numeric(12, 2), nullable=True)

    # Déconsolidation
    is_accepted = db.Column(db.Boolean, default=False, nullable=False)
    accepted_at = db.Column(db.DateTime, nullable=True)

    # ── Relations ─────────────────────────────────────────────
    quotation    = db.relationship("Quotation", back_populates="items")
    request_item = db.relationship("RequestItem", backref=db.backref("quotation_items", lazy="dynamic"))

    def to_dict(self):
        return {
            "id":                    self.id,
            "quotationId":           self.quotation_id,
            "requestItemId":         self.request_item_id,
            "productName":           self.product_name,
            "quantity":              self.quantity,
            "weightKg":              float(self.weight_kg)             if self.weight_kg             else None,
            "category":              self.category,
            "unitCostCny":           float(self.unit_cost_cny)         if self.unit_cost_cny         else None,
            "unitCostFcfa":          float(self.unit_cost_fcfa)        if self.unit_cost_fcfa        else None,
            "shippingPerUnitFcfa":   float(self.shipping_per_unit_fcfa)if self.shipping_per_unit_fcfa else None,
            "customsPerUnitFcfa":    float(self.customs_per_unit_fcfa) if self.customs_per_unit_fcfa else None,
            "subtotalFcfa":          float(self.subtotal_fcfa)         if self.subtotal_fcfa         else None,
            "isAccepted":            self.is_accepted,
            "acceptedAt":            self.accepted_at.isoformat()      if self.accepted_at           else None,
        }

    def __repr__(self):
        return f"<QuotationItem #{self.id} {self.product_name} accepted={self.is_accepted}>"


# ─────────────────────────────────────────────
# QUOTATION COST — frais globaux (assurance, manutention…)
# ─────────────────────────────────────────────

class QuotationCost(db.Model):
    __tablename__ = "quotation_costs"

    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quotation_id = db.Column(
        db.Integer,
        db.ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type        = db.Column(db.String(50),  nullable=True)
    label       = db.Column(db.String(255), nullable=False)
    amount_fcfa = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    quotation = db.relationship("Quotation", back_populates="costs")

    def to_dict(self):
        return {
            "id":          self.id,
            "quotationId": self.quotation_id,
            "type":        self.type,
            "label":       self.label,
            "amountFcfa":  float(self.amount_fcfa or 0),
        }

    def __repr__(self):
        return f"<QuotationCost #{self.id} {self.label}={self.amount_fcfa}>"


# ─────────────────────────────────────────────
# QUOTATION REVISION — historique pour traçabilité déconsolidation
# ─────────────────────────────────────────────

class QuotationRevision(db.Model):
    __tablename__ = "quotation_revisions"

    id               = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quotation_id     = db.Column(
        db.Integer,
        db.ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    revision_number  = db.Column(db.Integer, nullable=False)
    snapshot         = db.Column(db.JSON,    nullable=False)   # état complet figé
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason           = db.Column(db.String(255), nullable=True)  # ex: 'partial_acceptance'
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Relations ─────────────────────────────────────────────
    quotation    = db.relationship("Quotation", back_populates="revisions")
    created_by   = db.relationship("User", backref=db.backref("quotation_revisions", lazy="dynamic"),
                                   foreign_keys=[created_by_user_id])

    def to_dict(self):
        return {
            "id":               self.id,
            "quotationId":      self.quotation_id,
            "revisionNumber":   self.revision_number,
            "snapshot":         self.snapshot,
            "createdByUserId":  self.created_by_user_id,
            "reason":           self.reason,
            "createdAt":        self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<QuotationRevision #{self.id} v{self.revision_number} quotation={self.quotation_id}>"
