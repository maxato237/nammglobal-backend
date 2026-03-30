from flask import Blueprint, request as req
from app.models import Quotation, QuotationStatus, Request
from app.services import QuotationService, PricingService
from app.utils import (
    success, created, error, not_found, forbidden,
    login_required, admin_required, current_user
)

quotations_bp = Blueprint("quotations", __name__, url_prefix="/api/quotations")


# ═══════════════════════════════════════════════
# CLIENT
# ═══════════════════════════════════════════════

@quotations_bp.route("/request/<int:request_id>", methods=["GET"])
@login_required
def get_quotation_for_request(request_id):
    user = current_user()

    r = Request.query.get(request_id)
    if not r:
        return not_found("Demande introuvable.")

    if r.user_id != user.id:
        return forbidden()

    q = r.active_quotation  # ⚠️ doit exister côté Request
    if not q:
        return not_found("Aucun devis disponible.")

    return success(q.to_dict(include_costs=True))


@quotations_bp.route("/<int:quotation_id>/accept", methods=["POST"])
@login_required
def accept_quotation(quotation_id):
    user = current_user()

    q = Quotation.query.get(quotation_id)
    if not q:
        return not_found("Devis introuvable.")

    if q.request.user_id != user.id:
        return forbidden()

    # 🔒 sécurité métier
    if q.status != QuotationStatus.SENT:
        return error("Ce devis ne peut pas être accepté dans son état actuel.")

    if q.is_expired:
        return error("Ce devis est expiré.")

    try:
        q = QuotationService.accept(q)
        return success(q.to_dict(), "Devis accepté.")
    except ValueError as e:
        return error(str(e))


@quotations_bp.route("/<int:quotation_id>/reject", methods=["POST"])
@login_required
def reject_quotation(quotation_id):
    user = current_user()

    q = Quotation.query.get(quotation_id)
    if not q:
        return not_found("Devis introuvable.")

    if q.request.user_id != user.id:
        return forbidden()

    if q.status != QuotationStatus.SENT:
        return error("Ce devis ne peut pas être refusé.")

    try:
        q = QuotationService.reject(q)
        return success(q.to_dict(), "Devis refusé.")
    except ValueError as e:
        return error(str(e))


# ═══════════════════════════════════════════════
# ADMIN
# ═══════════════════════════════════════════════

@quotations_bp.route("/admin/request/<int:request_id>", methods=["POST"])
@admin_required
def create_quotation(request_id):

    r = Request.query.get(request_id)
    if not r:
        return not_found("Demande introuvable.")

    data = req.get_json(silent=True) or {}

    # 🔒 validation minimale stricte
    required_fields = ["productCost", "shippingCost"]
    for field in required_fields:
        if data.get(field) is None:
            return error(f"{field} est requis.")

    try:
        q = QuotationService.create_draft(r, data)
        return created(q.to_dict(include_costs=True), "Devis créé.")
    except Exception as e:
        return error(str(e))


@quotations_bp.route("/admin/<int:quotation_id>", methods=["PUT"])
@admin_required
def update_quotation(quotation_id):

    q = Quotation.query.get(quotation_id)
    if not q:
        return not_found("Devis introuvable.")

    if q.status != QuotationStatus.DRAFT:
        return error("Modification impossible : devis non brouillon.")

    try:
        q = QuotationService.update_draft(
            q,
            req.get_json(silent=True) or {}
        )
        return success(q.to_dict(include_costs=True), "Devis mis à jour.")
    except ValueError as e:
        return error(str(e))


@quotations_bp.route("/admin/<int:quotation_id>/send", methods=["POST"])
@admin_required
def send_quotation(quotation_id):

    q = Quotation.query.get(quotation_id)
    if not q:
        return not_found("Devis introuvable.")

    if q.status != QuotationStatus.DRAFT:
        return error("Seul un brouillon peut être envoyé.")

    try:
        q = QuotationService.send_to_client(q)
        return success(q.to_dict(include_costs=True), "Devis envoyé.")
    except ValueError as e:
        return error(str(e))


# ═══════════════════════════════════════════════
# PRICING ENGINE
# ═══════════════════════════════════════════════

@quotations_bp.route("/admin/compute", methods=["POST"])
@admin_required
def compute_quote_line():

    data = req.get_json(silent=True) or {}

    try:
        result = PricingService.compute_quote_line(
            product_cost=float(data.get("productCost", 0)),
            weight_kg=float(data.get("weightKg", 0)),
            quantity=int(data.get("quantity", 1)),
            shipping_method_id=int(data.get("shippingMethodId", 0)),
            category=data.get("category"),
        )

        return success(result)

    except Exception as e:
        return error(str(e))