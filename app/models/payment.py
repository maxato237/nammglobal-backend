import enum
from datetime import datetime
from app import db


class PaymentStatus(str, enum.Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    COMPLETED  = "completed"
    FAILED     = "failed"
    REFUNDED   = "refunded"


class PaymentMethod(str, enum.Enum):
    MTN_MOMO      = "mtn_momo"
    ORANGE_MONEY  = "orange_money"
    WAVE          = "wave"
    AIRTEL        = "airtel"
    MOOV          = "moov"
    CARD          = "card"
    BANK_TRANSFER = "bank_transfer"


# ─────────────────────────────────────────────
# PAYMENT
# ─────────────────────────────────────────────

class Payment(db.Model):
    __tablename__ = "payments"

    id       = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id  = db.Column(db.Integer, db.ForeignKey("users.id",  ondelete="SET NULL"), nullable=True,  index=True)

    amount_fcfa = db.Column(db.Numeric(12, 2), nullable=False)
    currency    = db.Column(db.String(10), nullable=False, default="FCFA")

    method = db.Column(
        db.Enum(PaymentMethod, name="payment_method"),
        nullable=True,
    )

    status = db.Column(
        db.Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.PENDING,
        nullable=False,
    )

    # Idempotence côté serveur — généré à /payments/init, réutilisable au retry
    internal_ref = db.Column(db.String(100), nullable=True, unique=True)

    # Références Flutterwave
    provider_ref              = db.Column(db.String(255), nullable=True)
    flutterwave_tx_id         = db.Column(db.String(255), nullable=True)
    flutterwave_charge_response = db.Column(db.JSON,      nullable=True)

    failure_reason = db.Column(db.Text,     nullable=True)
    paid_at        = db.Column(db.DateTime, nullable=True)
    refunded_at    = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Relations ─────────────────────────────────────────────
    order = db.relationship("Order", back_populates="payments")
    user  = db.relationship("User",  backref=db.backref("payments", lazy="dynamic"), foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id":            self.id,
            "orderId":       self.order_id,
            "userId":        self.user_id,
            "amountFcfa":    float(self.amount_fcfa) if self.amount_fcfa else 0,
            "currency":      self.currency,
            "method":        self.method.value  if self.method  else None,
            "status":        self.status.value  if self.status  else None,
            "internalRef":   self.internal_ref,
            "providerRef":   self.provider_ref,
            "failureReason": self.failure_reason,
            "paidAt":        self.paid_at.isoformat()    if self.paid_at    else None,
            "refundedAt":    self.refunded_at.isoformat() if self.refunded_at else None,
            "createdAt":     self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Payment #{self.id} {self.status} {self.amount_fcfa} FCFA>"


# ─────────────────────────────────────────────
# WEBHOOK LOG — toutes les notifs Flutterwave
# ─────────────────────────────────────────────

class WebhookLog(db.Model):
    __tablename__ = "webhook_logs"

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    provider        = db.Column(db.String(50),  nullable=False, default="flutterwave")
    event_type      = db.Column(db.String(100), nullable=True)
    payload         = db.Column(db.JSON,        nullable=False)
    signature       = db.Column(db.Text,        nullable=True)
    signature_valid = db.Column(db.Boolean,     nullable=True)
    processed       = db.Column(db.Boolean,     default=False, nullable=False)
    processed_at    = db.Column(db.DateTime,    nullable=True)
    ip_address      = db.Column(db.String(45),  nullable=True)
    created_at      = db.Column(db.DateTime,    default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id":             self.id,
            "provider":       self.provider,
            "eventType":      self.event_type,
            "signatureValid": self.signature_valid,
            "processed":      self.processed,
            "processedAt":    self.processed_at.isoformat() if self.processed_at else None,
            "ipAddress":      self.ip_address,
            "createdAt":      self.created_at.isoformat()   if self.created_at   else None,
        }

    def __repr__(self):
        return f"<WebhookLog #{self.id} [{self.provider}] {self.event_type} processed={self.processed}>"
