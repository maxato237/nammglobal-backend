import hmac
import hashlib


def constant_time_compare(val1: str, val2: str) -> bool:
    """Comparaison en temps constant pour éviter les timing attacks."""
    return hmac.compare_digest(
        val1.encode("utf-8") if isinstance(val1, str) else val1,
        val2.encode("utf-8") if isinstance(val2, str) else val2,
    )


def hash_token(raw_token: str) -> str:
    """Hash SHA-256 d'un token (pour RefreshToken)."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def verify_flutterwave_signature(payload_str: str, secret_hash: str, received_hash: str) -> bool:
    """Vérifie la signature Flutterwave via comparaison en temps constant."""
    return constant_time_compare(received_hash, secret_hash)
