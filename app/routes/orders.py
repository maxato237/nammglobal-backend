from flask import Blueprint, request as req
from app.models import Order, OrderStatus, Request
from app.services import OrderService, PaymentService
from app.utils import success, created, error, not_found, forbidden, login_required, admin_required, current_user

orders_bp = Blueprint("orders", __name__, url_prefix="/api/orders")

# ═══════ CLIENT ═══════════════════════════════════════════════

@orders_bp.route("", methods=["GET"])
@login_required
def list_my_orders():
    user    = current_user()
    status  = req.args.get("status")
    wave_id = req.args.get("wave")
    orders  = OrderService.get_for_user(user.id, status=status, wave_id=wave_id)
    return success([o.to_dict() for o in orders])

@orders_bp.route("/<int:order_id>", methods=["GET"])
@login_required
def get_order(order_id):
    user  = current_user()
    order = Order.query.get(order_id)
    if not order: return not_found("Commande introuvable.")
    if order.request.user_id != user.id: return forbidden()
    return success(order.to_dict(include_payments=True))

@orders_bp.route("/confirm-payment", methods=["POST"])
@login_required
def confirm_payment():
    """
    Client confirme son paiement Flutterwave → crée la commande.
    Body: { quotationId, flwRef, amount, method }
    """
    user = current_user()
    data = req.get_json(silent=True) or {}
    quotation_id = data.get("quotationId")
    flw_ref      = (data.get("flwRef") or "").strip()
    amount       = float(data.get("amount", 0))
    method       = (data.get("method") or "").strip()

    if not quotation_id or not flw_ref:
        return error("quotationId et flwRef sont obligatoires.")

    from app.models import Quotation
    q = Quotation.query.get(quotation_id)
    if not q: return not_found("Devis introuvable.")
    if q.request.user_id != user.id: return forbidden()

    try:
        order = PaymentService.verify_and_confirm(quotation_id, flw_ref, amount, method)
        return created(order.to_dict(), "Commande confirmée !")
    except ValueError as e:
        return error(str(e))

# ═══════ ADMIN ════════════════════════════════════════════════

@orders_bp.route("/admin/all", methods=["GET"])
@admin_required
def admin_list_orders():
    status  = req.args.get("status")
    wave_id = req.args.get("wave")
    orders  = OrderService.get_all(status=status, wave_id=wave_id)
    return success([o.to_dict(include_payments=True) for o in orders])

@orders_bp.route("/admin/<int:order_id>", methods=["GET"])
@admin_required
def admin_get_order(order_id):
    order = Order.query.get(order_id)
    if not order: return not_found("Commande introuvable.")
    return success(order.to_dict(include_tracking=True, include_payments=True))

@orders_bp.route("/admin/<int:order_id>/status", methods=["PATCH"])
@admin_required
def admin_update_status(order_id):
    order = Order.query.get(order_id)
    if not order: return not_found("Commande introuvable.")
    data       = req.get_json(silent=True) or {}
    new_status = (data.get("status") or "").strip()
    title      = (data.get("title") or "").strip()
    description= (data.get("description") or "").strip() or None
    location   = (data.get("location") or "").strip() or None

    if not new_status or not title:
        return error("status et title sont obligatoires.")
    try:
        status_enum = OrderStatus(new_status)
    except ValueError:
        return error(f"Statut invalide : {new_status}")

    order = OrderService.update_status(order, status_enum, title, description, location)
    return success(order.to_dict(), "Statut mis à jour.")

@orders_bp.route("/admin/<int:order_id>/tracking-number", methods=["PATCH"])
@admin_required
def set_tracking_number(order_id):
    order = Order.query.get(order_id)
    if not order: return not_found("Commande introuvable.")
    data = req.get_json(silent=True) or {}
    tn   = (data.get("trackingNumber") or "").strip()
    if not tn: return error("trackingNumber est requis.")
    order = OrderService.set_tracking_number(order, tn)
    return success(order.to_dict(), "Numéro de suivi mis à jour.")

@orders_bp.route("/webhook/flutterwave", methods=["POST"])
def flutterwave_webhook():
    """Webhook Flutterwave — pas d'auth JWT, vérification via secret key."""
    from flask import current_app
    secret      = current_app.config.get("FLUTTERWAVE_SECRET_KEY", "")
    flw_sig     = req.headers.get("verif-hash", "")
    if secret and flw_sig != secret:
        return error("Signature invalide.", 401)
    ok, msg, order = PaymentService.handle_flw_webhook(req.get_json(silent=True) or {})
    return success({"orderId": order.id if order else None}, msg) if ok else error(msg)
