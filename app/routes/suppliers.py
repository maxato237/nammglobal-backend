from flask import Blueprint, request as req
from app.models import Supplier, SupplierOrder,Order
from app.services import SupplierService
from app.utils import success, created, error, not_found, admin_required

suppliers_bp = Blueprint("suppliers", __name__, url_prefix="/api/suppliers")

@suppliers_bp.route("", methods=["GET"])
@admin_required
def list_suppliers():
    blacklisted = req.args.get("blacklisted")
    q = Supplier.query
    if blacklisted == "1":  q = q.filter_by(blacklisted=True)
    elif blacklisted == "0": q = q.filter_by(blacklisted=False)
    return success([s.to_dict() for s in q.order_by(Supplier.name.asc()).all()])

@suppliers_bp.route("/<int:supplier_id>", methods=["GET"])
@admin_required
def get_supplier(supplier_id):
    s = Supplier.query.get(supplier_id)
    if not s: return not_found("Fournisseur introuvable.")
    return success(s.to_dict())

@suppliers_bp.route("", methods=["POST"])
@admin_required
def create_supplier():
    data = req.get_json(silent=True) or {}
    if not data.get("name"): return error("Le nom du fournisseur est obligatoire.")
    return created(SupplierService.create(data).to_dict(), "Fournisseur créé.")

@suppliers_bp.route("/<int:supplier_id>", methods=["PUT"])
@admin_required
def update_supplier(supplier_id):
    s = Supplier.query.get(supplier_id)
    if not s: return not_found("Fournisseur introuvable.")
    return success(SupplierService.update(s, req.get_json(silent=True) or {}).to_dict(), "Fournisseur mis à jour.")

@suppliers_bp.route("/<int:supplier_id>", methods=["DELETE"])
@admin_required
def delete_supplier(supplier_id):
    s = Supplier.query.get(supplier_id)
    if not s: return not_found("Fournisseur introuvable.")
    SupplierService.delete(s); return success(message="Fournisseur supprimé.")

# ── Commandes fournisseurs ────────────────────────────────────

@suppliers_bp.route("/orders/order/<int:order_id>", methods=["GET"])
@admin_required
def list_supplier_orders_for_order(order_id):
    order = Order.query.get(order_id)
    if not order: return not_found("Commande introuvable.")
    return success([so.to_dict() for so in order.supplier_orders])

@suppliers_bp.route("/orders", methods=["POST"])
@admin_required
def create_supplier_order():
    data = req.get_json(silent=True) or {}
    order_id = data.get("orderId")
    if not order_id: return error("orderId est requis.")
    order = Order.query.get(order_id)
    if not order: return not_found("Commande introuvable.")
    if not data.get("supplierName"): return error("supplierName est requis.")
    so = SupplierService.create_supplier_order(order, data)
    return created(so.to_dict(), "Commande fournisseur créée.")

