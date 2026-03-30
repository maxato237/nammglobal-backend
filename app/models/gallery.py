from datetime import datetime
from app import db


class GalleryItem(db.Model):
    __tablename__ = "gallery_items"
    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type         = db.Column(db.String(50),  nullable=False, default="photo")
    thumb_url    = db.Column(db.Text,        nullable=False)
    full_url     = db.Column(db.Text,        nullable=True)
    product_name = db.Column(db.String(255), nullable=False)
    category     = db.Column(db.String(100), nullable=True)
    order_date   = db.Column(db.Date,        nullable=True)
    arrival_date = db.Column(db.Date,        nullable=True)
    weight       = db.Column(db.Float,       nullable=True)
    client_name  = db.Column(db.String(255), nullable=True)
    client_city  = db.Column(db.String(100), nullable=True)
    comment      = db.Column(db.Text,        nullable=True)
    rating       = db.Column(db.Integer,     nullable=True, default=5)
    order_id     = db.Column(db.Integer,     db.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    is_published = db.Column(db.Boolean,     default=True)
    created_at   = db.Column(db.DateTime,    default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "type": self.type, "thumbUrl": self.thumb_url,
                "fullUrl": self.full_url or self.thumb_url,
                "product": self.product_name, "category": self.category,
                "orderDate": self.order_date.isoformat() if self.order_date else None,
                "arrivalDate": self.arrival_date.isoformat() if self.arrival_date else None,
                "weight": self.weight,
                "client": self.client_name,
                "clientCity": self.client_city,
                "comment": self.comment, "rating": self.rating,
                "orderId": self.order_id, "isPublished": self.is_published,
                "createdAt": self.created_at.isoformat() if self.created_at else None}
    def __repr__(self): return f"<GalleryItem #{self.id} {self.product_name}>"
