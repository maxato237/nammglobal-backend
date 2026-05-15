import os
import requests as http_requests


class WhatsAppService:
    """Wrapper Meta Cloud API (WhatsApp Business API)."""

    BASE_URL = "https://graph.facebook.com/v19.0"

    @staticmethod
    def _headers() -> dict:
        token = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    @staticmethod
    def _phone_id() -> str:
        return os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")

    @classmethod
    def send_otp(cls, phone: str, otp_code: str) -> bool:
        """Envoie un OTP via un template WhatsApp."""
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": "otp_verification",
                "language": {"code": "fr"},
                "components": [
                    {"type": "body", "parameters": [{"type": "text", "text": otp_code}]}
                ],
            },
        }
        url = f"{cls.BASE_URL}/{cls._phone_id()}/messages"
        try:
            resp = http_requests.post(url, json=payload, headers=cls._headers(), timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    @classmethod
    def send_text(cls, phone: str, message: str) -> bool:
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": message},
        }
        url = f"{cls.BASE_URL}/{cls._phone_id()}/messages"
        try:
            resp = http_requests.post(url, json=payload, headers=cls._headers(), timeout=10)
            return resp.status_code == 200
        except Exception:
            return False
