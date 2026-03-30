from datetime import datetime
from app import db


class Stat(db.Model):
    """Statistiques affichées sur la page d'accueil (gérées par l'admin)."""
    __tablename__ = "stats"
    id         = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    value      = db.Column(db.Integer,     nullable=False, default=0)
    suffix     = db.Column(db.String(10),  nullable=True)
    label      = db.Column(db.String(255), nullable=False)
    icon       = db.Column(db.String(50),  nullable=True)
    is_active  = db.Column(db.Boolean,     default=True)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "value": self.value, "suffix": self.suffix,
                "label": self.label, "icon": self.icon, "isActive": self.is_active}
    def __repr__(self): return f"<Stat {self.label}={self.value}>"
