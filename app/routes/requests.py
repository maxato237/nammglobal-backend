import os

import cloudinary
from flask import Blueprint, current_app, request as req
from app.models import Request, RequestStatus
from app.models.request import RequestItemImage
from app.services import RequestService
from app.utils import success, created, error, not_found, forbidden, login_required, admin_required, current_user

requests_bp = Blueprint("requests", __name__, url_prefix="/api/requests")


# ─── Helpers ──────────────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 2 MB
MIME_TYPES = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
}


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_upload(file, subfolder: str) -> str | None:
    if not file or file.filename == '':
        return None
    if not allowed_file(file.filename):
        return None

    # Vérification taille
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)

    if size > MAX_FILE_SIZE:
        return None

    try:
        result = cloudinary.uploader.upload(
            file,
            folder=subfolder,
            resource_type="image",
            transformation=[
                {"width": 500, "height": 500, "crop": "limit"},
                {"quality": "auto"},
                {"fetch_format": "auto"}
            ]
        )
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"]
        }
    except Exception as e:
        current_app.logger.error(f"Cloudinary upload error: {e}")
        return None

def delete_from_cloudinary(public_id):
    try:
        cloudinary.uploader.destroy(public_id)
    except Exception as e:
        current_app.logger.error(f"Cloudinary delete error: {e}")


# ═══════ CLIENT ═══════════════════════════════════════════════

@requests_bp.route("", methods=["GET"])
@login_required
def list_my_requests():
    user   = current_user()
    status = req.args.get("status")
    items  = RequestService.get_for_user(user.id, status=status)
    return success([r.to_dict() for r in items])


@requests_bp.route("", methods=["POST"])
@login_required
def create_request():
    user = current_user()

    data = req.form.to_dict()
    images = req.files.getlist('images')

    # ───── Validation ─────
    if not data.get("notes") and not images:
        return error("Décrivez le produit ou ajoutez au moins une image.")

    try:
        quantity = int(data.get("quantity", 1))
        if quantity < 1:
            raise ValueError()
    except ValueError:
        return error("La quantité doit être un entier positif.")

    data["quantity"] = quantity

    # ───── Création request ─────
    r = RequestService.create(user, data)

    uploaded_public_ids = []
    request_images = []

    try:
        # ───── Upload images ─────
        for img in images:
            result = save_upload(
                img,
                subfolder=f"NAMM_FILES/REQUESTS/USER_{user.id}"
            )

            if not result:
                raise Exception(
                    f"Erreur upload {img.filename}. "
                    f"Max {MAX_FILE_SIZE // (1024 * 1024)}MB"
                )

            uploaded_public_ids.append(result["public_id"])

            request_images.append(
                RequestItemImage(
                    request_id=r.id,
                    image_url=result["url"],
                    public_id=result["public_id"]
                )
            )

        # ───── DB commit ─────
        if request_images:
            from app import db
            db.session.add_all(request_images)

        from app import db
        db.session.commit()

    except Exception as e:
        # 🔥 rollback DB
        from app import db
        db.session.rollback()

        # 🔥 cleanup cloudinary
        for public_id in uploaded_public_ids:
            delete_from_cloudinary(public_id)

        return error(str(e))

    return created(
        r.to_dict(include_images=True),
        "Demande envoyée avec succès."
    )

@requests_bp.route("/<int:request_id>", methods=["GET"])
@login_required
def get_request(request_id):
    user = current_user()
    r    = Request.query.get(request_id)
    if not r:
        return not_found("Demande introuvable.")
    if r.user_id != user.id:
        return forbidden()
    return success(r.to_dict(include_images=True))


@requests_bp.route("/<int:request_id>/cancel", methods=["POST"])
@login_required
def cancel_request(request_id):
    user = current_user()
    r    = Request.query.get(request_id)
    if not r:
        return not_found("Demande introuvable.")
    if r.user_id != user.id:
        return forbidden()
    if r.status not in (RequestStatus.PENDING, RequestStatus.PROCESSING):
        return error("Cette demande ne peut plus être annulée.")
    r = RequestService.cancel(r)
    return success(r.to_dict(), "Demande annulée.")


# ═══════ ADMIN ════════════════════════════════════════════════

@requests_bp.route("/admin/all", methods=["GET"])
@admin_required
def admin_list_requests():
    # wave_id retiré : Request n'a pas de colonne wave_id
    status = req.args.get("status")
    items  = RequestService.get_all(status=status)
    return success([r.to_dict(include_images=True) for r in items])


@requests_bp.route("/admin/<int:request_id>", methods=["GET"])
@admin_required
def admin_get_request(request_id):
    r = Request.query.get(request_id)
    if not r:
        return not_found("Demande introuvable.")
    return success(r.to_dict(include_images=True))


@requests_bp.route("/admin/<int:request_id>/status", methods=["PATCH"])
@admin_required
def admin_update_status(request_id):
    r = Request.query.get(request_id)
    if not r:
        return not_found("Demande introuvable.")
    data       = req.get_json(silent=True) or {}
    new_status = data.get("status", "")
    try:
        status_enum = RequestStatus(new_status)
    except ValueError:
        valid = [s.value for s in RequestStatus]
        return error(f"Statut invalide : '{new_status}'. Valeurs acceptées : {valid}")
    r = RequestService.update_status(r, status_enum)
    return success(r.to_dict(), "Statut mis à jour.")