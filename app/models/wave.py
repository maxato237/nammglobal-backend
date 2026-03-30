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
