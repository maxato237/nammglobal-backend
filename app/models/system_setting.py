from datetime import datetime
from app.extensions import db


class SystemSetting(db.Model):
    __tablename__ = "system_settings"

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=True)
    value_type = db.Column(
        db.Enum("string", "int", "bool", "json", name="setting_value_type"),
        default="string",
    )
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True, index=True)
    is_public = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    updated_by = db.relationship("User", backref=db.backref("setting_updates", lazy="dynamic"))

    def get_typed_value(self):
        """Retourne la valeur castée selon value_type."""
        if self.value is None:
            return None
        if self.value_type == "int":
            return int(self.value)
        if self.value_type == "bool":
            return self.value.lower() in ("true", "1", "yes")
        if self.value_type == "json":
            import json
            return json.loads(self.value)
        return self.value

    def to_dict(self):
        return {
            "key": self.key,
            "value": self.get_typed_value(),
            "value_type": self.value_type,
            "description": self.description,
            "category": self.category,
            "is_public": self.is_public,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
