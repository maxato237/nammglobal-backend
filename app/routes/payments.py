from flask import Blueprint, request
from app.utils import success, error, not_found
from app.utils.auth_decorators import login_required, admin_required, current_user
from app.models import Payment
from app.extensions import db

payments_bp = Blueprint("payments", __name__, url_prefix="/api/v1/payments")


@payments_bp.route("/init", methods=["POST"])
@login_required
def init_payment():
    """Initie un paiement Flutterwave — délégué au payment_service."""
    from app.services.payment_service import PaymentService
    data = request.get_json(silent=True) or {}
    order_id = data.get("order_id")
    method = data.get("method")
    if not order_id or not method:
        return error("order_id et method sont requis.")
    try:
        result = PaymentService.init(order_id, method, current_user(), data)
        return success(result, "Paiement initié.")
    except Exception as e:
        return error(str(e))


@payments_bp.route("/<int:payment_id>", methods=["GET"])
@login_required
def get_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    return success(payment.to_dict())


@payments_bp.route("/order/<int:order_id>", methods=["GET"])
@login_required
def payments_by_order(order_id):
    payments = Payment.query.filter_by(order_id=order_id).order_by(Payment.created_at.desc()).all()
    return success([p.to_dict() for p in payments])


@payments_bp.route("/<int:payment_id>/verify", methods=["POST"])
@login_required
def verify_payment(payment_id):
    from app.services.payment_service import PaymentService
    try:
        result = PaymentService.verify(payment_id)
        return success(result, "Paiement vérifié.")
    except Exception as e:
        return error(str(e))


@payments_bp.route("/<int:payment_id>/refund", methods=["POST"])
@admin_required
def refund_payment(payment_id):
    from app.services.payment_service import PaymentService
    data = request.get_json(silent=True) or {}
    try:
        result = PaymentService.refund(payment_id, data.get("reason"), current_user())
        return success(result, "Remboursement effectué.")
    except Exception as e:
        return error(str(e))


@payments_bp.route("", methods=["GET"])
@admin_required
def list_payments():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status = request.args.get("status")
    q = Payment.query
    if status:
        q = q.filter_by(status=status)
    paginated = q.order_by(Payment.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return success({
        "items": [p.to_dict() for p in paginated.items],
        "total": paginated.total,
        "page": paginated.page,
        "pages": paginated.pages,
    })
