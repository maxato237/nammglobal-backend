import os
import logging
from twilio.rest import Client

logger = logging.getLogger(__name__)


class SmsService:
    """Wrapper Twilio SMS API."""

    @staticmethod
    def _client() -> Client:
        return Client(
            os.environ.get("TWILIO_ACCOUNT_SID", ""),
            os.environ.get("TWILIO_AUTH_TOKEN", ""),
        )

    @classmethod
    def send_otp(cls, phone: str, otp_code: str) -> bool:
        message = f"Votre code de vérification NAMM GLOBAL : {otp_code}. Valable 10 minutes."
        return cls.send_text(phone, message)

    @classmethod
    def send_text(cls, phone: str, message: str) -> bool:
        try:
            msg = cls._client().messages.create(
                body=message,
                from_=os.environ.get("TWILIO_FROM_NUMBER", ""),
                to=+237654837863,
            )
            return msg.sid is not None
        except Exception as e:
            logger.error("Twilio send_text failed: %s", e)
            return False
