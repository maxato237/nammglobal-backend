import random
import uuid
from datetime import datetime, timedelta
from app.extensions import db, bcrypt
from app.models.auth_token import PasswordResetToken


class OTPService:
    OTP_EXPIRY_MINUTES = 10
    RESET_TOKEN_EXPIRY_MINUTES = 30
    MAX_ATTEMPTS = 3

    @staticmethod
    def generate_otp() -> str:
        return str(random.randint(100000, 999999))

    @staticmethod
    def create_reset_request(user_id: int, channel: str, ip: str, user_agent: str) -> tuple[str, PasswordResetToken]:
        otp = OTPService.generate_otp()
        otp_hash = bcrypt.generate_password_hash(otp).decode("utf-8")
        token = PasswordResetToken(
            user_id=user_id,
            otp_code_hash=otp_hash,
            channel=channel,
            expires_at=datetime.utcnow() + timedelta(minutes=OTPService.OTP_EXPIRY_MINUTES),
            ip_address=ip,
            user_agent=user_agent,
        )
        db.session.add(token)
        db.session.commit()
        return otp, token

    @staticmethod
    def verify_otp(token: PasswordResetToken, otp_code: str) -> bool:
        if token.is_expired():
            return False
        if token.attempts >= OTPService.MAX_ATTEMPTS:
            return False
        token.attempts += 1
        valid = bcrypt.check_password_hash(token.otp_code_hash, otp_code)
        if valid:
            token.reset_token = str(uuid.uuid4())
            token.expires_at = datetime.utcnow() + timedelta(minutes=OTPService.RESET_TOKEN_EXPIRY_MINUTES)
        db.session.commit()
        return valid

    @staticmethod
    def consume_reset_token(reset_token: str) -> PasswordResetToken | None:
        token = PasswordResetToken.query.filter_by(reset_token=reset_token).first()
        if not token or token.is_expired() or token.reset_token_used_at:
            return None
        token.reset_token_used_at = datetime.utcnow()
        db.session.commit()
        return token
