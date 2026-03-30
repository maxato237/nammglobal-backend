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
