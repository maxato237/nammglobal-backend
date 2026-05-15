import enum
from datetime import datetime
from app import db, bcrypt


class UserRole(str, enum.Enum):
    CLIENT      = "client"
    OPERATOR    = "operator"
    SUPER_ADMIN = "super_admin"


class OtpChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    EMAIL    = "email"


class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    full_name     = db.Column(db.String(255), nullable=False)
    phone         = db.Column(db.String(50),  nullable=True, unique=True, index=True)
    whatsapp      = db.Column(db.String(50),  nullable=True, index=True)
    email         = db.Column(db.String(255), nullable=True, unique=True, index=True)

    # Localisation — country_code FK vers countries.code
    country_code  = db.Column(db.String(2), db.ForeignKey("countries.code", ondelete="SET NULL"), nullable=True, index=True)
    city          = db.Column(db.String(100), nullable=True)

    password_hash = db.Column(db.Text, nullable=False)

    role = db.Column(
        db.Enum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.CLIENT,
    )

    # Vérification
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    phone_verified = db.Column(db.Boolean, default=False, nullable=False)

    is_active  = db.Column(db.Boolean, default=True, nullable=False)

    # Sécurité / brute-force
    last_login_at          = db.Column(db.DateTime, nullable=True)
    failed_login_attempts  = db.Column(db.Integer,  default=0, nullable=False)
    locked_until           = db.Column(db.DateTime, nullable=True)

    # Préférences OTP
    preferred_otp_channel = db.Column(
        db.Enum(OtpChannel, name="otp_channel"),
        nullable=False,
        default=OtpChannel.WHATSAPP,
    )

    # Avatar Cloudinary
    avatar_public_id = db.Column(db.String(255), nullable=True)
    avatar_url       = db.Column(db.Text,        nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)   # soft delete

    # ── Relations ─────────────────────────────────────────────
    country        = db.relationship("Country", foreign_keys=[country_code], backref=db.backref("users", lazy="dynamic"))
    requests       = db.relationship("Request",      back_populates="user",  lazy="dynamic")
    notifications  = db.relationship("Notification", back_populates="user",  lazy="dynamic")
    reset_tokens   = db.relationship("PasswordResetToken", backref="user",   lazy="dynamic")
    refresh_tokens = db.relationship("RefreshToken",       backref="user",   lazy="dynamic")
    audit_logs     = db.relationship("AuditLog",           backref="actor",  lazy="dynamic",
                                     foreign_keys="AuditLog.actor_user_id")
    setting_updates = db.relationship("SystemSetting", backref="updated_by", lazy="dynamic",
                                      foreign_keys="SystemSetting.updated_by_user_id")

    # ── Password ──────────────────────────────────────────────
    def set_password(self, plain: str):
        self.password_hash = bcrypt.generate_password_hash(plain).decode("utf-8")

    def check_password(self, plain: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, plain)

    # ── Helpers ───────────────────────────────────────────────
    @property
    def is_admin(self) -> bool:
        return self.role in (UserRole.OPERATOR, UserRole.SUPER_ADMIN)

    @property
    def is_locked(self) -> bool:
        return self.locked_until is not None and self.locked_until > datetime.utcnow()

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def initials(self) -> str:
        parts = (self.full_name or "?").strip().split()
        return "".join(p[0].upper() for p in parts[:2])

    @property
    def is_profile_complete(self) -> bool:
        return bool(self.full_name and self.phone and self.country_code and self.city)

    def to_dict(self):
        return {
            "id":                   self.id,
            "fullName":             self.full_name,
            "phone":                self.phone,
            "whatsapp":             self.whatsapp,
            "email":                self.email,
            "countryCode":          self.country_code,
            "city":                 self.city,
            "role":                 self.role.value if self.role else None,
            "emailVerified":        self.email_verified,
            "phoneVerified":        self.phone_verified,
            "isActive":             self.is_active,
            "isLocked":             self.is_locked,
            "preferredOtpChannel":  self.preferred_otp_channel.value if self.preferred_otp_channel else None,
            "avatarUrl":            self.avatar_url,
            "initials":             self.initials,
            "profileComplete":      self.is_profile_complete,
            "lastLoginAt":          self.last_login_at.isoformat() if self.last_login_at else None,
            "createdAt":            self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User #{self.id} {self.full_name} [{self.role}]>"
