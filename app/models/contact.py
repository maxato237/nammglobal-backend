from datetime import datetime
from app.extensions import db


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    whatsapp = db.Column(db.String(30), nullable=True)
    country_code = db.Column(db.String(2), nullable=True)
    subject = db.Column(
        db.Enum("info", "order_issue", "partnership", "complaint", "other", name="contact_subject"),
        nullable=False,
    )
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)
    company_name = db.Column(db.String(255), nullable=True)
    message = db.Column(db.Text, nullable=False)
    attachment_url = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum("new", "read", "in_progress", "resolved", name="contact_status"),
        default="new",
    )
    assigned_admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("contact_messages", lazy="dynamic"))
    assigned_admin = db.relationship("User", foreign_keys=[assigned_admin_id])
    replies = db.relationship("ContactReply", backref="message", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "whatsapp": self.whatsapp,
            "country_code": self.country_code,
            "subject": self.subject,
            "order_id": self.order_id,
            "company_name": self.company_name,
            "message": self.message,
            "status": self.status,
            "assigned_admin_id": self.assigned_admin_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class ContactReply(db.Model):
    __tablename__ = "contact_replies"

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("contact_messages.id"), nullable=False, index=True)
    admin_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_via = db.Column(
        db.Enum("email", "whatsapp", "internal", name="contact_reply_channel"),
        default="internal",
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship("User", backref=db.backref("contact_replies", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "message_id": self.message_id,
            "admin_user_id": self.admin_user_id,
            "content": self.content,
            "sent_via": self.sent_via,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
