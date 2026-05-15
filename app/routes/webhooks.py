from flask import Blueprint, request
from app.utils import success, error
from app.utils.security import constant_time_compare

webhooks_bp = Blueprint("webhooks", __name__, url_prefix="/api/v1/webhooks")


@webhooks_bp.route("/flutterwave", methods=["POST"])
def flutterwave_webhook():
    """Réception des notifications Flutterwave avec vérification de signature."""
    import os
    from app.extensions import db
    from app.models.payment import WebhookLog

    secret_hash = os.environ.get("FLUTTERWAVE_SECRET_HASH", "")
    signature = request.headers.get("verif-hash", "")
    payload = request.get_json(silent=True) or {}

    sig_valid = bool(secret_hash) and constant_time_compare(signature, secret_hash)

    log = WebhookLog(
        provider="flutterwave",
        event_type=payload.get("event", "unknown"),
        payload=payload,
        signature=signature,
        signature_valid=sig_valid,
        ip_address=request.remote_addr,
    )
    db.session.add(log)
    db.session.commit()

    if not sig_valid:
        return error("Signature invalide.", 401)

    from app.services.payment_service import PaymentService
    try:
        PaymentService.handle_webhook(payload, log.id)
    except Exception as e:
        return error(str(e), 500)

    return success(message="Webhook traité.")
