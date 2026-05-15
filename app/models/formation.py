from datetime import datetime
from app.extensions import db


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    subtitle = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    price_fcfa = db.Column(db.Numeric(12, 2), nullable=True)
    duration_weeks = db.Column(db.Integer, nullable=True)
    hero_image_public_id = db.Column(db.String(255), nullable=True)
    hero_image_url = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    modules = db.relationship("CourseModule", backref="course", lazy="dynamic", order_by="CourseModule.position")
    sessions = db.relationship("CourseSession", backref="course", lazy="dynamic")
    testimonials = db.relationship("CourseTestimonial", backref="course", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "slug": self.slug,
            "title": self.title,
            "subtitle": self.subtitle,
            "description": self.description,
            "price_fcfa": float(self.price_fcfa) if self.price_fcfa else None,
            "duration_weeks": self.duration_weeks,
            "hero_image_url": self.hero_image_url,
            "is_active": self.is_active,
        }


class CourseModule(db.Model):
    __tablename__ = "course_modules"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True)
    position = db.Column(db.Integer, nullable=False)
    icon = db.Column(db.String(50), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    content_html = db.Column(db.Text, nullable=True)
    duration_label = db.Column(db.String(50), nullable=True)
    is_preview = db.Column(db.Boolean, default=False)

    def to_dict(self, include_content=False):
        d = {
            "id": self.id,
            "course_id": self.course_id,
            "position": self.position,
            "icon": self.icon,
            "title": self.title,
            "description": self.description,
            "duration_label": self.duration_label,
            "is_preview": self.is_preview,
        }
        if include_content:
            d["content_html"] = self.content_html
        return d


class CourseSession(db.Model):
    __tablename__ = "course_sessions"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    max_seats = db.Column(db.Integer, nullable=True)
    current_seats = db.Column(db.Integer, default=0)
    whatsapp_group_link = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum("planned", "open", "full", "in_progress", "completed", "cancelled", name="course_session_status"),
        default="planned",
    )

    enrollments = db.relationship("CourseEnrollment", backref="session", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "course_id": self.course_id,
            "name": self.name,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "max_seats": self.max_seats,
            "current_seats": self.current_seats,
            "status": self.status,
        }


class CourseEnrollment(db.Model):
    __tablename__ = "course_enrollments"
    __table_args__ = (
        db.UniqueConstraint("course_session_id", "user_id", name="uq_enrollment_session_user"),
    )

    id = db.Column(db.Integer, primary_key=True)
    course_session_id = db.Column(db.Integer, db.ForeignKey("course_sessions.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    whatsapp = db.Column(db.String(30), nullable=True)
    country_code = db.Column(db.String(2), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    objective = db.Column(db.Text, nullable=True)
    payment_id = db.Column(db.Integer, db.ForeignKey("payments.id"), nullable=True)
    payment_status = db.Column(
        db.Enum("pending", "validated", "refunded", "failed", name="enrollment_payment_status"),
        default="pending",
    )
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    certificate_public_id = db.Column(db.String(255), nullable=True)
    certificate_url = db.Column(db.Text, nullable=True)
    certificate_issued_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", backref=db.backref("enrollments", lazy="dynamic"))
    progress = db.relationship("ModuleProgress", backref="enrollment", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "course_session_id": self.course_session_id,
            "user_id": self.user_id,
            "full_name": self.full_name,
            "payment_status": self.payment_status,
            "enrolled_at": self.enrolled_at.isoformat() if self.enrolled_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "certificate_url": self.certificate_url,
        }


class ModuleProgress(db.Model):
    __tablename__ = "module_progress"
    __table_args__ = (
        db.UniqueConstraint("enrollment_id", "module_id", name="uq_progress_enrollment_module"),
    )

    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey("course_enrollments.id"), nullable=False, index=True)
    module_id = db.Column(db.Integer, db.ForeignKey("course_modules.id"), nullable=False, index=True)
    status = db.Column(
        db.Enum("todo", "in_progress", "done", name="module_progress_status"),
        default="todo",
    )
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    module = db.relationship("CourseModule", backref=db.backref("progress_records", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "enrollment_id": self.enrollment_id,
            "module_id": self.module_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class CourseTestimonial(db.Model):
    __tablename__ = "course_testimonials"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    country_code = db.Column(db.String(2), nullable=True)
    session_label = db.Column(db.String(100), nullable=True)
    photo_url = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    is_published = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "country_code": self.country_code,
            "session_label": self.session_label,
            "photo_url": self.photo_url,
            "content": self.content,
            "rating": self.rating,
            "is_published": self.is_published,
        }
