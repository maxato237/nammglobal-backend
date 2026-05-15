from flask import Blueprint, request
from app.extensions import db
from app.models import CommunityChannel, CommunityStat
from app.utils import success, created, not_found
from app.utils.auth_decorators import admin_required

community_bp = Blueprint("community", __name__, url_prefix="/api/v1/community")


@community_bp.route("/channels", methods=["GET"])
def list_channels():
    channels = CommunityChannel.query.filter_by(is_active=True).order_by(CommunityChannel.sort_order).all()
    return success([c.to_dict() for c in channels])


@community_bp.route("/stats", methods=["GET"])
def list_stats():
    stats = CommunityStat.query.filter_by(is_active=True).order_by(CommunityStat.sort_order).all()
    return success([s.to_dict() for s in stats])


@community_bp.route("/channels", methods=["POST"])
@admin_required
def create_channel():
    data = request.get_json(silent=True) or {}
    channel = CommunityChannel(
        platform=data.get("platform", "whatsapp"),
        label=data.get("label", ""),
        description=data.get("description"),
        url=data.get("url", ""),
        members_count=data.get("members_count", 0),
        color=data.get("color"),
        icon=data.get("icon"),
        sort_order=data.get("sort_order", 0),
        is_active=data.get("is_active", True),
    )
    db.session.add(channel)
    db.session.commit()
    return created(channel.to_dict(), "Canal créé.")


@community_bp.route("/channels/<int:channel_id>", methods=["PATCH"])
@admin_required
def update_channel(channel_id):
    channel = CommunityChannel.query.get_or_404(channel_id)
    data = request.get_json(silent=True) or {}
    for f in ("label", "description", "url", "members_count", "color", "icon", "sort_order", "is_active"):
        if f in data:
            setattr(channel, f, data[f])
    db.session.commit()
    return success(channel.to_dict(), "Canal mis à jour.")


@community_bp.route("/channels/<int:channel_id>", methods=["DELETE"])
@admin_required
def delete_channel(channel_id):
    channel = CommunityChannel.query.get_or_404(channel_id)
    db.session.delete(channel)
    db.session.commit()
    return success(message="Canal supprimé.")


@community_bp.route("/stats", methods=["POST"])
@admin_required
def create_stat():
    data = request.get_json(silent=True) or {}
    stat = CommunityStat(
        value=data.get("value", ""),
        suffix=data.get("suffix"),
        label=data.get("label", ""),
        icon=data.get("icon"),
        sort_order=data.get("sort_order", 0),
        is_active=data.get("is_active", True),
    )
    db.session.add(stat)
    db.session.commit()
    return created(stat.to_dict(), "Statistique créée.")


@community_bp.route("/stats/<int:stat_id>", methods=["PATCH"])
@admin_required
def update_stat(stat_id):
    stat = CommunityStat.query.get_or_404(stat_id)
    data = request.get_json(silent=True) or {}
    for f in ("value", "suffix", "label", "icon", "sort_order", "is_active"):
        if f in data:
            setattr(stat, f, data[f])
    db.session.commit()
    return success(stat.to_dict(), "Statistique mise à jour.")
