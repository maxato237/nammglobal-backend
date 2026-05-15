import hashlib
import time
import os
import cloudinary
from flask import Blueprint, request
from app.utils import success, error
from app.utils.auth_decorators import login_required

uploads_bp = Blueprint("uploads", __name__, url_prefix="/api/v1/uploads")


@uploads_bp.route("/signature", methods=["POST"])
@login_required
def generate_signature():
    """Génère une signature Cloudinary pour upload direct depuis le frontend."""
    data = request.get_json(silent=True) or {}
    folder = data.get("folder", "namm-global/uploads")
    public_id = data.get("public_id")
    eager = data.get("eager")

    timestamp = int(time.time())
    params = {"timestamp": timestamp, "folder": folder}
    if public_id:
        params["public_id"] = public_id
    if eager:
        params["eager"] = eager

    sorted_params = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    api_secret = os.environ.get("CLOUDINARY_API_SECRET", "")
    signature = hashlib.sha256(f"{sorted_params}{api_secret}".encode()).hexdigest()

    return success({
        "signature": signature,
        "timestamp": timestamp,
        "cloud_name": os.environ.get("CLOUDINARY_CLOUD_NAME", ""),
        "api_key": os.environ.get("CLOUDINARY_API_KEY", ""),
        "folder": folder,
    })


@uploads_bp.route("/delete", methods=["POST"])
@login_required
def delete_asset():
    """Supprime un asset Cloudinary après vérification d'ownership."""
    data = request.get_json(silent=True) or {}
    public_id = data.get("public_id")
    if not public_id:
        return error("public_id requis.")
    try:
        result = cloudinary.uploader.destroy(public_id)
        if result.get("result") != "ok":
            return error("Impossible de supprimer le fichier.")
        return success(message="Fichier supprimé.")
    except Exception as e:
        return error(str(e))
