from app.extensions import db


class CommunityChannel(db.Model):
    __tablename__ = "community_channels"

    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(
        db.Enum("telegram", "whatsapp", "tiktok", name="community_platform"),
        nullable=False,
    )
    label = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    url = db.Column(db.Text, nullable=False)
    members_count = db.Column(db.Integer, default=0)
    color = db.Column(db.String(20), nullable=True)
    icon = db.Column(db.String(50), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "platform": self.platform,
            "label": self.label,
            "description": self.description,
            "url": self.url,
            "members_count": self.members_count,
            "color": self.color,
            "icon": self.icon,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
        }


class CommunityStat(db.Model):
    __tablename__ = "community_stats"

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(50), nullable=False)
    suffix = db.Column(db.String(10), nullable=True)
    label = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(50), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "value": self.value,
            "suffix": self.suffix,
            "label": self.label,
            "icon": self.icon,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
        }
