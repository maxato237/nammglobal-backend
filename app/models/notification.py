from datetime import datetime
from app import db


# ─────────────────────────────────────────────
# NOTIFICATION
# ─────────────────────────────────────────────

class Notification(db.Model):
    __tablename__ = "notifications"

    id      = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    type     = db.Column(db.String(50),  nullable=False)   # request_quoted | payment_validated | order_shipped…
    title    = db.Column(db.String(255), nullable=False)
    body     = db.Column(db.Text,        nullable=True)
    link_url = db.Column(db.Text,        nullable=True)

    meta = db.Column(db.JSON, nullable=True)

    channel = db.Column(
        db.Enum("in_app", "email", "whatsapp", name="notification_channel"),
        nullable=False,
        default="in_app",
    )

    is_read    = db.Column(db.Boolean,  default=False, nullable=False, index=True)
    read_at    = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="notifications")

    def to_dict(self):
        return {
            "id":        self.id,
            "userId":    self.user_id,
            "type":      self.type,
            "title":     self.title,
            "body":      self.body,
            "linkUrl":   self.link_url,
            "meta":      self.meta,
            "channel":   self.channel,
            "isRead":    self.is_read,
            "readAt":    self.read_at.isoformat()    if self.read_at    else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Notification #{self.id} {self.type} user={self.user_id}>"


# ─────────────────────────────────────────────
# NOTIFICATION PREFERENCE — préférences canaux par user
# ─────────────────────────────────────────────

class NotificationPreference(db.Model):
    __tablename__ = "notification_preferences"

    # PK = user_id (relation One-to-One avec User)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    email_enabled    = db.Column(db.Boolean, default=True,  nullable=False)
    whatsapp_enabled = db.Column(db.Boolean, default=True,  nullable=False)
    in_app_enabled   = db.Column(db.Boolean, default=True,  nullable=False)

    # Types désactivés individuellement (JSON list, ex: ["order_shipped", "request_quoted"])
    types_disabled   = db.Column(db.JSON, nullable=True, default=list)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # One-to-one via backref sur User
    user = db.relationship(
        "User",
        backref=db.backref("notification_preference", uselist=False, lazy="joined"),
    )

    def to_dict(self):
        return {
            "userId":          self.user_id,
            "emailEnabled":    self.email_enabled,
            "whatsappEnabled": self.whatsapp_enabled,
            "inAppEnabled":    self.in_app_enabled,
            "typesDisabled":   self.types_disabled or [],
            "updatedAt":       self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<NotificationPreference user={self.user_id}>"
