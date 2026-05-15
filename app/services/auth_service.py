from app.extensions import db, bcrypt
from app.models import User
from app.models.auth_token import RefreshToken, TokenBlacklist
from datetime import datetime, timedelta
import hashlib


class AuthService:
    @staticmethod
    def register(data: dict) -> User:
        user = User(
            full_name=data["full_name"],
            phone=data["phone"],
            email=data.get("email"),
            whatsapp=data.get("whatsapp"),
            city=data.get("city"),
            role="client",
        )
        user.set_password(data["password"])
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def blacklist_token(jti: str, expires_at: datetime):
        entry = TokenBlacklist(jti=jti, expires_at=expires_at)
        db.session.merge(entry)
        db.session.commit()

    @staticmethod
    def is_token_blacklisted(jti: str) -> bool:
        return TokenBlacklist.query.get(jti) is not None

    @staticmethod
    def save_refresh_token(user_id: int, raw_token: str, device_label: str, ip: str, expires_at: datetime):
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        rt = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            device_label=device_label,
            ip_address=ip,
            expires_at=expires_at,
        )
        db.session.add(rt)
        db.session.commit()
        return rt

    @staticmethod
    def revoke_refresh_token(token_hash: str):
        rt = RefreshToken.query.filter_by(token_hash=token_hash).first()
        if rt:
            rt.revoked_at = datetime.utcnow()
            db.session.commit()

    @staticmethod
    def get_active_sessions(user_id: int):
        now = datetime.utcnow()
        return RefreshToken.query.filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        ).all()
