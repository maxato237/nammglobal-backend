from datetime import datetime
from app.extensions import db


class ChineseEvent(db.Model):
    __tablename__ = "chinese_events"
    __table_args__ = (
        db.Index("ix_chinese_events_year_date", "year", "date_start"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(
        db.Enum(
            "new_year", "golden_week", "mid_autumn", "qingming",
            "dragon_boat", "factory_off", "custom",
            name="chinese_event_type",
        ),
        nullable=False,
    )
    date_start = db.Column(db.Date, nullable=False)
    date_end = db.Column(db.Date, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    severity = db.Column(
        db.Enum("low", "medium", "high", name="chinese_event_severity"),
        default="medium",
    )
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(20), nullable=True)
    icon = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "date_start": self.date_start.isoformat() if self.date_start else None,
            "date_end": self.date_end.isoformat() if self.date_end else None,
            "year": self.year,
            "severity": self.severity,
            "description": self.description,
            "color": self.color,
            "icon": self.icon,
        }
