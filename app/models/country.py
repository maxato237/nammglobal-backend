from app.extensions import db


class Country(db.Model):
    __tablename__ = "countries"

    code = db.Column(db.String(2), primary_key=True)
    name_fr = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)
    dial_code = db.Column(db.String(10), nullable=True)
    currency = db.Column(db.String(10), nullable=True)
    flag_emoji = db.Column(db.String(10), nullable=True)
    is_served = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "code": self.code,
            "name_fr": self.name_fr,
            "name_en": self.name_en,
            "dial_code": self.dial_code,
            "currency": self.currency,
            "flag_emoji": self.flag_emoji,
            "is_served": self.is_served,
            "sort_order": self.sort_order,
        }
