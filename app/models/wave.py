import enum
from datetime import datetime, date
from app import db


class WaveStatus(str, enum.Enum):
    PLANNED    = "planned"
    OPEN       = "open"
    CLOSED     = "closed"
    IN_TRANSIT = "in_transit"
    DELIVERED  = "delivered"
    CANCELLED  = "cancelled"


class Wave(db.Model):
    __tablename__ = "waves"

    id           = db.Column(db.String(50), primary_key=True)
    name         = db.Column(db.String(100), nullable=False)

    # Scopage pays (NULL = vague globale)
    country_code = db.Column(db.String(2), db.ForeignKey("countries.code", ondelete="SET NULL"), nullable=True, index=True)

    deadline_date    = db.Column(db.Date, nullable=False)   # limite de commande
    shipping_date    = db.Column(db.Date, nullable=False)   # départ Chine
    arrival_date_min = db.Column(db.Date, nullable=False)   # fourchette arrivée min
    arrival_date_max = db.Column(db.Date, nullable=False)   # fourchette arrivée max

    transport_type   = db.Column(db.String(100), nullable=True)   # air / sea
    capacity_kg      = db.Column(db.Numeric(12, 2), nullable=True)
    current_load_kg  = db.Column(db.Numeric(12, 2), nullable=True, default=0)

    status = db.Column(
        db.Enum(WaveStatus, name="wave_status"),
        nullable=False,
        default=WaveStatus.PLANNED,
        index=True,
    )

    notes      = db.Column(db.Text,     nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Relations ─────────────────────────────────────────────
    country = db.relationship("Country", backref=db.backref("waves", lazy="dynamic"))
    orders  = db.relationship("Order", back_populates="wave", lazy="dynamic")

    # ── Helpers ───────────────────────────────────────────────
    @property
    def is_open(self) -> bool:
        return self.status == WaveStatus.OPEN and self.deadline_date >= date.today()

    @property
    def days_left(self) -> int:
        if not self.deadline_date:
            return 0
        return max((self.deadline_date - date.today()).days, 0)

    @property
    def capacity_available_kg(self):
        if self.capacity_kg is None:
            return None
        return float(self.capacity_kg) - float(self.current_load_kg or 0)

    @staticmethod
    def generate_id() -> str:
        import uuid
        return "WAVE-" + str(uuid.uuid4())[:8].upper()

    def to_dict(self):
        return {
            "id":               self.id,
            "name":             self.name,
            "countryCode":      self.country_code,
            "deadlineDate":     self.deadline_date.isoformat()    if self.deadline_date    else None,
            "shippingDate":     self.shipping_date.isoformat()    if self.shipping_date    else None,
            "arrivalDateMin":   self.arrival_date_min.isoformat() if self.arrival_date_min else None,
            "arrivalDateMax":   self.arrival_date_max.isoformat() if self.arrival_date_max else None,
            "transportType":    self.transport_type,
            "capacityKg":       float(self.capacity_kg)     if self.capacity_kg     else None,
            "currentLoadKg":    float(self.current_load_kg) if self.current_load_kg else 0,
            "capacityAvailableKg": self.capacity_available_kg,
            "status":           self.status.value if self.status else None,
            "notes":            self.notes,
            "isOpen":           self.is_open,
            "daysLeft":         self.days_left,
        }

    def __repr__(self):
        return f"<Wave {self.id} {self.name} [{self.status}]>"
