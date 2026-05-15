from datetime import datetime
from app import db


class Stat(db.Model):
    """KPIs affichés sur les pages publiques (gérés depuis l'admin)."""
    __tablename__ = "stats"

    id  = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    key = db.Column(db.String(100), nullable=False, unique=True, index=True)   # identifiant stable ex: 'orders_delivered'

    value  = db.Column(db.Integer,     nullable=False, default=0)
    suffix = db.Column(db.String(10),  nullable=True)    # ex: '+', 'k', '%'
    label  = db.Column(db.String(255), nullable=False)
    icon   = db.Column(db.String(50),  nullable=True)

    # Page sur laquelle la stat s'affiche
    page = db.Column(
        db.Enum("homepage", "community", "about", name="stat_page"),
        nullable=False,
        default="homepage",
        index=True,
    )

    sort_order = db.Column(db.Integer, default=0)
    is_active  = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":        self.id,
            "key":       self.key,
            "value":     self.value,
            "suffix":    self.suffix,
            "label":     self.label,
            "icon":      self.icon,
            "page":      self.page,
            "sortOrder": self.sort_order,
            "isActive":  self.is_active,
        }

    def __repr__(self):
        return f"<Stat {self.key}={self.value}>"
