from datetime import datetime
from app import db, bcrypt
import re


class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    full_name     = db.Column(db.String(255), nullable=False)
    phone         = db.Column(db.String(50),  nullable=True, unique=True, index=True)
    whatsapp      = db.Column(db.String(50),  nullable=True)
    email         = db.Column(db.String(255), nullable=True, unique=True, index=True)
    country       = db.Column(db.String(100), nullable=True)
    city          = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.Text,        nullable=False)
    role          = db.Column(db.String(50),  nullable=False, default="client")
    is_active     = db.Column(db.Boolean,     default=True,   nullable=False)
    created_at    = db.Column(db.DateTime,    default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime,    default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Relations ─────────────────────────────────────────────
    requests      = db.relationship("Request",      back_populates="user", lazy="dynamic")
    notifications = db.relationship("Notification", back_populates="user", lazy="dynamic")

    # ── Password ──────────────────────────────────────────────
    def set_password(self, plain: str):
        self.password_hash = bcrypt.generate_password_hash(plain).decode("utf-8")

    def check_password(self, plain: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, plain)

    # ── Helpers ───────────────────────────────────────────────
    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def avatar(self) -> str:
        parts = (self.full_name or "?").strip().split()
        return "".join(p[0].upper() for p in parts[:2])

    @property
    def is_profile_complete(self) -> bool:
        return bool(self.full_name and self.phone and self.country and self.city)

    def to_dict(self):
        return {
            "id":              self.id,
            "fullName":        self.full_name,
            "phone":           self.phone,
            "whatsapp":        self.whatsapp,
            "email":           self.email,
            "country":         self.country,
            "city":            self.city,
            "role":            self.role,
            "avatar":          self.avatar,
            "profileComplete": self.is_profile_complete,
            "createdAt":       self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User #{self.id} {self.full_name} [{self.role}]>"
