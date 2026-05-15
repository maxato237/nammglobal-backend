import enum
from datetime import datetime
from app import db


class SurchargeType(str, enum.Enum):
    PER_KG = "per_kg"
    FIXED  = "fixed"
    NONE   = "none"


# ─────────────────────────────────────────────────────────────
# ShippingMethod — tarif de transport scopé par pays
# ─────────────────────────────────────────────────────────────

class ShippingMethod(db.Model):
    __tablename__ = "shipping_methods"
    __table_args__ = (
        db.UniqueConstraint("country_code", "name", name="uq_shipping_country_name"),
    )

    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    country_code = db.Column(db.String(2), db.ForeignKey("countries.code", ondelete="CASCADE"), nullable=False, index=True)
    name         = db.Column(db.String(100), nullable=False)

    timeframe_days_min = db.Column(db.Integer, nullable=True)
    timeframe_days_max = db.Column(db.Integer, nullable=True)

    price_per_kg = db.Column(db.Numeric(12, 2), nullable=False)
    min_kg       = db.Column(db.Numeric(12, 2), nullable=True)
    max_kg       = db.Column(db.Numeric(12, 2), nullable=True)

    icon       = db.Column(db.String(50),  nullable=True)
    is_active  = db.Column(db.Boolean,     default=True)
    sort_order = db.Column(db.Integer,     default=0)

    country = db.relationship("Country", backref=db.backref("shipping_methods", lazy="dynamic"))

    def to_dict(self):
        return {
            "id":               self.id,
            "countryCode":      self.country_code,
            "name":             self.name,
            "timeframeDaysMin": self.timeframe_days_min,
            "timeframeDaysMax": self.timeframe_days_max,
            "pricePerKg":       float(self.price_per_kg) if self.price_per_kg else 0,
            "minKg":            float(self.min_kg) if self.min_kg else None,
            "maxKg":            float(self.max_kg) if self.max_kg else None,
            "icon":             self.icon,
            "isActive":         self.is_active,
            "sortOrder":        self.sort_order,
        }

    def __repr__(self):
        return f"<ShippingMethod #{self.id} [{self.country_code}] {self.name}>"


# ─────────────────────────────────────────────────────────────
# ServiceFeeRule — tranches de commission NAMM par pays
# ─────────────────────────────────────────────────────────────

class ServiceFeeRule(db.Model):
    __tablename__ = "service_fee_rules"

    id                = db.Column(db.Integer, primary_key=True, autoincrement=True)
    country_code      = db.Column(db.String(2), db.ForeignKey("countries.code", ondelete="CASCADE"), nullable=False, index=True)
    min_amount_fcfa   = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    max_amount_fcfa   = db.Column(db.Numeric(12, 2), nullable=True)   # NULL = illimité
    percentage        = db.Column(db.Float, nullable=False)
    label             = db.Column(db.String(255), nullable=True)

    country = db.relationship("Country", backref=db.backref("service_fee_rules", lazy="dynamic"))

    def to_dict(self):
        return {
            "id":             self.id,
            "countryCode":    self.country_code,
            "minAmountFcfa":  float(self.min_amount_fcfa) if self.min_amount_fcfa else 0,
            "maxAmountFcfa":  float(self.max_amount_fcfa) if self.max_amount_fcfa else None,
            "percentage":     self.percentage,
            "label":          self.label,
        }

    def __repr__(self):
        return f"<ServiceFeeRule #{self.id} [{self.country_code}] {self.percentage}%>"


# ─────────────────────────────────────────────────────────────
# ProductCategoryRule — surcharge par catégorie de produit par pays
# ─────────────────────────────────────────────────────────────

class ProductCategoryRule(db.Model):
    __tablename__ = "product_category_rules"

    id               = db.Column(db.Integer, primary_key=True, autoincrement=True)
    country_code     = db.Column(db.String(2), db.ForeignKey("countries.code", ondelete="CASCADE"), nullable=False, index=True)
    category_name    = db.Column(db.String(100), nullable=False)
    surcharge_per_kg = db.Column(db.Numeric(12, 2), nullable=True, default=0)
    surcharge_type   = db.Column(db.Enum(SurchargeType, name="surcharge_type"), nullable=False, default=SurchargeType.NONE)
    customs_rate_pct = db.Column(db.Float, nullable=True)
    note             = db.Column(db.Text,        nullable=True)
    icon             = db.Column(db.String(50),  nullable=True)

    country = db.relationship("Country", backref=db.backref("product_category_rules", lazy="dynamic"))

    def to_dict(self):
        return {
            "id":              self.id,
            "countryCode":     self.country_code,
            "categoryName":    self.category_name,
            "surchargePerKg":  float(self.surcharge_per_kg) if self.surcharge_per_kg else 0,
            "surchargeType":   self.surcharge_type.value if self.surcharge_type else None,
            "customsRatePct":  self.customs_rate_pct,
            "note":            self.note,
            "icon":            self.icon,
        }

    def __repr__(self):
        return f"<ProductCategoryRule #{self.id} [{self.country_code}] {self.category_name}>"


# ─────────────────────────────────────────────────────────────
# CustomsRule — règles douanières par pays
# ─────────────────────────────────────────────────────────────

class CustomsRule(db.Model):
    __tablename__ = "customs_rules"

    id                    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    country_code          = db.Column(db.String(2), db.ForeignKey("countries.code", ondelete="CASCADE"), nullable=False, index=True)
    threshold_amount_fcfa = db.Column(db.Numeric(12, 2), nullable=False)
    rate_pct              = db.Column(db.Float, nullable=False)
    note                  = db.Column(db.Text, nullable=True)

    country = db.relationship("Country", backref=db.backref("customs_rules", lazy="dynamic"))

    def to_dict(self):
        return {
            "id":                   self.id,
            "countryCode":          self.country_code,
            "thresholdAmountFcfa":  float(self.threshold_amount_fcfa),
            "ratePct":              self.rate_pct,
            "note":                 self.note,
        }

    def __repr__(self):
        return f"<CustomsRule #{self.id} [{self.country_code}] {self.rate_pct}%>"


# ─────────────────────────────────────────────────────────────
# ExchangeRate — taux CNY/FCFA pour le calculateur auto
# ─────────────────────────────────────────────────────────────

class ExchangeRate(db.Model):
    __tablename__ = "exchange_rates"

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    from_currency = db.Column(db.String(10), nullable=False)   # ex: CNY
    to_currency   = db.Column(db.String(10), nullable=False)   # ex: FCFA
    rate          = db.Column(db.Numeric(12, 6), nullable=False)
    effective_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active     = db.Column(db.Boolean, default=True, nullable=False)  # 1 seul actif par paire

    def to_dict(self):
        return {
            "id":           self.id,
            "fromCurrency": self.from_currency,
            "toCurrency":   self.to_currency,
            "rate":         float(self.rate),
            "effectiveAt":  self.effective_at.isoformat() if self.effective_at else None,
            "isActive":     self.is_active,
        }

    def __repr__(self):
        return f"<ExchangeRate {self.from_currency}→{self.to_currency} @ {self.rate}>"
