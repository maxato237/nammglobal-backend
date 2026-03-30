from datetime import datetime
from app import db


class Notification(db.Model):
    __tablename__ = "notifications"
    id         = db.Column(db.Integer,  primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer,  db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type       = db.Column(db.String(50),  nullable=False)
    title      = db.Column(db.String(255), nullable=False)
    message    = db.Column(db.Text,        nullable=True)
    is_read    = db.Column(db.Boolean,     default=False, index=True)
    meta_data   = db.Column(db.JSON,        nullable=True)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)
    user       = db.relationship("User", back_populates="notifications")

    def to_dict(self):
        return {"id": self.id, "userId": self.user_id, "type": self.type,
                "title": self.title, "message": self.message, "read": self.is_read,
                "meta_data": self.meta_data,
                "createdAt": self.created_at.isoformat() if self.created_at else None}
    def __repr__(self): return f"<Notification #{self.id} {self.type}>"
