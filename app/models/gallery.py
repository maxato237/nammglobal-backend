from datetime import datetime
from app import db


# ─────────────────────────────────────────────
# GALLERY ITEM
# ─────────────────────────────────────────────

class GalleryItem(db.Model):
    __tablename__ = "gallery_items"

    id                   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type                 = db.Column(db.String(50), nullable=False, default="photo")   # photo | video

    thumb_url            = db.Column(db.Text, nullable=False)
    full_url             = db.Column(db.Text, nullable=True)
    cloudinary_public_id = db.Column(db.String(255), nullable=True)

    product_name         = db.Column(db.String(255), nullable=False)
    category             = db.Column(db.String(100), nullable=True)

    # Localisation de livraison
    country_code         = db.Column(db.String(2), db.ForeignKey("countries.code", ondelete="SET NULL"), nullable=True, index=True)

    # Liens optionnels vers données internes
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    wave_id  = db.Column(db.String(50), db.ForeignKey("waves.id", ondelete="SET NULL"), nullable=True, index=True)

    description_short = db.Column(db.String(255), nullable=True)
    description_long  = db.Column(db.Text,        nullable=True)

    position     = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Relations ─────────────────────────────────────────────
    country      = db.relationship("Country", backref=db.backref("gallery_items", lazy="dynamic"))
    order        = db.relationship("Order",   backref=db.backref("gallery_items", lazy="dynamic"))
    wave         = db.relationship("Wave",    backref=db.backref("gallery_items", lazy="dynamic"))
    testimonials = db.relationship(
        "GalleryTestimonial",
        back_populates="gallery_item",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def to_dict(self, include_testimonials=False):
        data = {
            "id":                  self.id,
            "type":                self.type,
            "thumbUrl":            self.thumb_url,
            "fullUrl":             self.full_url or self.thumb_url,
            "cloudinaryPublicId":  self.cloudinary_public_id,
            "productName":         self.product_name,
            "category":            self.category,
            "countryCode":         self.country_code,
            "orderId":             self.order_id,
            "waveId":              self.wave_id,
            "descriptionShort":    self.description_short,
            "descriptionLong":     self.description_long,
            "position":            self.position,
            "isPublished":         self.is_published,
            "createdAt":           self.created_at.isoformat() if self.created_at else None,
        }
        if include_testimonials:
            data["testimonials"] = [t.to_dict() for t in self.testimonials]
        return data

    def __repr__(self):
        return f"<GalleryItem #{self.id} {self.product_name}>"


# ─────────────────────────────────────────────
# GALLERY TESTIMONIAL
# ─────────────────────────────────────────────

class GalleryTestimonial(db.Model):
    __tablename__ = "gallery_testimonials"

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gallery_item_id = db.Column(
        db.Integer,
        db.ForeignKey("gallery_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    first_name       = db.Column(db.String(100), nullable=False)
    country_code     = db.Column(db.String(2),   nullable=True)
    photo_public_id  = db.Column(db.String(255), nullable=True)
    content          = db.Column(db.Text,        nullable=False)
    rating           = db.Column(db.Integer,     nullable=True)   # 1-5
    date_label       = db.Column(db.String(50),  nullable=True)   # ex: "Mars 2026"

    is_published = db.Column(db.Boolean, default=False)
    sort_order   = db.Column(db.Integer, default=0)

    gallery_item = db.relationship("GalleryItem", back_populates="testimonials")

    def to_dict(self):
        return {
            "id":             self.id,
            "galleryItemId":  self.gallery_item_id,
            "firstName":      self.first_name,
            "countryCode":    self.country_code,
            "photoPublicId":  self.photo_public_id,
            "content":        self.content,
            "rating":         self.rating,
            "dateLabel":      self.date_label,
            "isPublished":    self.is_published,
            "sortOrder":      self.sort_order,
        }

    def __repr__(self):
        return f"<GalleryTestimonial #{self.id} {self.first_name}>"
