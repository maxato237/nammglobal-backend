"""
seed.py – Seed robuste (idempotent) NAMM GLOBAL
"""
from datetime import date
from app import create_app, db
from app.models import (
    Wave, GalleryItem, ServiceFeeRule,
    ShippingMethod, ProductCategoryRule, Stat
)

# ==============================
# DATA
# ==============================

WAVES = [
    {"id":"WAVE-001","name":"Vague 1","deadline":"2025-02-05","shipping":"2025-02-15","arrival":"2025-03-20","type":"Mer","notes":"Après Nouvel An Chinois"},
    {"id":"WAVE-002","name":"Vague 2","deadline":"2025-03-20","shipping":"2025-04-01","arrival":"2025-05-10","type":"Mer","notes":"Canton Fair"},
]

SERVICE_FEES = [
    {"min":0,"max":100000,"pct":15},
    {"min":100001,"max":300000,"pct":13},
    {"min":300001,"max":600000,"pct":11},
]

SHIPPING_METHODS = [
    {"name":"Avion Express","price":6500},
    {"name":"Mer Standard","price":1800},
]

# ==============================
# HELPERS
# ==============================

def upsert(model, unique_filter: dict, data: dict):
    """
    Insert or update
    """
    instance = model.query.filter_by(**unique_filter).first()

    if instance:
        for key, value in data.items():
            setattr(instance, key, value)
        return instance

    instance = model(**data)
    db.session.add(instance)
    return instance


# ==============================
# SEED
# ==============================

def seed_waves():
    print("🌊 Waves...")
    for w in WAVES:
        upsert(
            Wave,
            {"id": w["id"]},
            {
                "id": w["id"],
                "name": w["name"],
                "deadline_date": date.fromisoformat(w["deadline"]),
                "shipping_date": date.fromisoformat(w["shipping"]),
                "arrival_date": date.fromisoformat(w["arrival"]),
                "transport_type": w["type"],
                "notes": w["notes"],
            }
        )


def seed_service_fees():
    print("💼 Service fees...")
    for f in SERVICE_FEES:
        upsert(
            ServiceFeeRule,
            {"min_amount": f["min"], "max_amount": f["max"]},
            {
                "min_amount": f["min"],
                "max_amount": f["max"],
                "percentage": f["pct"],
            }
        )


def seed_shipping():
    print("🚢 Shipping...")
    for m in SHIPPING_METHODS:
        upsert(
            ShippingMethod,
            {"name": m["name"]},
            {
                "name": m["name"],
                "price_per_kg": m["price"],
                "is_active": True
            }
        )


def seed_stats():
    print("📊 Stats...")
    stats = [
        {"label":"Clients satisfaits","value":450},
        {"label":"Commandes livrées","value":1200},
    ]

    for s in stats:
        upsert(
            Stat,
            {"label": s["label"]},
            s
        )


def seed_gallery():
    print("🖼️ Gallery...")
    if GalleryItem.query.count() > 0:
        return

    items = [
        {"product":"Tissus wax","thumb":"https://..."},
    ]

    for g in items:
        db.session.add(GalleryItem(
            product_name=g["product"],
            thumb_url=g["thumb"]
        ))


# ==============================
# RUN
# ==============================

def run():
    print("\n🌱 Seed START")
    app = create_app()

    with app.app_context():
        db.create_all()

        try:
            with db.session.begin():
                seed_waves()
                seed_service_fees()
                seed_shipping()
                seed_stats()
                seed_gallery()

            print("✅ Seed SUCCESS")

        except Exception as e:
            db.session.rollback()
            print("❌ Seed FAILED:", str(e))


if __name__ == "__main__":
    run()