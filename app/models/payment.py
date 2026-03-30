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
