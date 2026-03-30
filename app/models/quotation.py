"""
Devis (Quotation)

Workflow :
draft → sent → accepted | rejected | expired

- Un Quotation est lié à une Request
- Peut contenir plusieurs coûts additionnels (QuotationCost)
- Peut générer une Order après acceptation
"""

import enum
from datetime import datetime, date
from decimal import Decimal
from app import db


# ─────────────────────────────────────────────
# ENUM
# ─────────────────────────────────────────────

class QuotationStatus(str, enum.Enum):
    DRAFT    = "draft"
    SENT     = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED  = "expired"


# ─────────────────────────────────────────────
# MODEL QUOTATION
# ─────────────────────────────────────────────

class Quotation(db.Model):
    __tablename__ = "quotations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    request_id = db.Column(
        db.Integer,
        db.ForeignKey("requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    status = db.Column(
        db.Enum(QuotationStatus, name="quotation_status"),
        default=QuotationStatus.DRAFT,
        nullable=False,
        index=True
    )

    currency = db.Column(db.String(10), nullable=False, default="FCFA")

    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    valid_until = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # ── coûts détaillés ──
    quantity       = db.Column(db.Integer, nullable=False, default=1)
    product_cost   = db.Column(db.Numeric(12, 2), default=0)
    shipping_cost  = db.Column(db.Numeric(12, 2), default=0)
    service_fee    = db.Column(db.Numeric(12, 2), default=0)
    customs_fee    = db.Column(db.Numeric(12, 2), default=0)
    other_fee      = db.Column(db.Numeric(12, 2), default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # ─────────────────────────────────────────
    # RELATIONS
    # ─────────────────────────────────────────

    request = db.relationship(
        "Request",
        back_populates="quotations"
    )

    costs = db.relationship(
        "QuotationCost",
        back_populates="quotation",
        cascade="all, delete-orphan",
        lazy="select"
    )

    orders = db.relationship(
        "Order",
        back_populates="quotation",
        lazy="select"  # ⚠️ PAS dynamic → évite bugs JSON + debug
    )

    # ─────────────────────────────────────────
    # BUSINESS LOGIC
    # ─────────────────────────────────────────

    def recompute_total(self):
        """Recalcule le montant total du devis."""
        costs_total = sum(
            (c.amount or Decimal("0")) for c in self.costs
        )

        self.total_amount = (
            (self.product_cost or Decimal("0")) +
            (self.shipping_cost or Decimal("0")) +
            (self.service_fee or Decimal("0")) +
            (self.customs_fee or Decimal("0")) +
            (self.other_fee or Decimal("0")) +
            costs_total
        )

    @property
    def is_expired(self) -> bool:
        if self.valid_until and self.valid_until < date.today():
            return True
        return False

    # ─────────────────────────────────────────
    # SERIALIZATION
    # ─────────────────────────────────────────

    def to_dict(self, include_costs=True):
        data = {
            "id": self.id,
            "requestId": self.request_id,
            "status": self.status.value if self.status else None,
            "currency": self.currency,

            "totalAmount": float(self.total_amount or 0),

            "productCost": float(self.product_cost or 0),
            "shippingCost": float(self.shipping_cost or 0),
            "serviceFee": float(self.service_fee or 0),
            "customsFee": float(self.customs_fee or 0),
            "otherFee": float(self.other_fee or 0),

            "quantity": self.quantity,

            "validUntil": self.valid_until.isoformat() if self.valid_until else None,
            "notes": self.notes,

            "isExpired": self.is_expired,

            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_costs:
            data["costs"] = [c.to_dict() for c in self.costs]

        return data

    def __repr__(self):
        return f"<Quotation #{self.id} request={self.request_id} status={self.status}>"



# ─────────────────────────────────────────────
# MODEL QUOTATION COST
# ─────────────────────────────────────────────

class QuotationCost(db.Model):
    __tablename__ = "quotation_costs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    quotation_id = db.Column(
        db.Integer,
        db.ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    type = db.Column(db.String(50), nullable=True)
    label = db.Column(db.String(255), nullable=False)

    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relation inverse
    quotation = db.relationship(
        "Quotation",
        back_populates="costs"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "quotationId": self.quotation_id,
            "type": self.type,
            "label": self.label,
            "amount": float(self.amount or 0),
        }

    def __repr__(self):
        return f"<QuotationCost #{self.id} {self.label}={self.amount}>"