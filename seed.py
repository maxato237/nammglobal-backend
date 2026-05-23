"""
seed.py – Seed robuste (idempotent) NAMM GLOBAL
"""
from datetime import date
from app import create_app, db
from app.models import (
    Country, Wave, GalleryItem, ServiceFeeRule,
    ShippingMethod, ProductCategoryRule, Stat
)

# ==============================
# DATA
# ==============================

COUNTRIES = [
    {"code": "CM", "name_fr": "Cameroun",              "name_en": "Cameroon",          "dial_code": "+237", "currency": "FCFA", "flag_emoji": "🇨🇲", "is_served": True,  "sort_order": 1},
    {"code": "CI", "name_fr": "Côte d'Ivoire",         "name_en": "Ivory Coast",        "dial_code": "+225", "currency": "FCFA", "flag_emoji": "🇨🇮", "is_served": True,  "sort_order": 2},
    {"code": "SN", "name_fr": "Sénégal",               "name_en": "Senegal",            "dial_code": "+221", "currency": "FCFA", "flag_emoji": "🇸🇳", "is_served": True,  "sort_order": 3},
    {"code": "GA", "name_fr": "Gabon",                 "name_en": "Gabon",              "dial_code": "+241", "currency": "FCFA", "flag_emoji": "🇬🇦", "is_served": True,  "sort_order": 4},
    {"code": "CG", "name_fr": "Congo-Brazzaville",     "name_en": "Republic of Congo",  "dial_code": "+242", "currency": "FCFA", "flag_emoji": "🇨🇬", "is_served": True,  "sort_order": 5},
    {"code": "GH", "name_fr": "Ghana",                 "name_en": "Ghana",              "dial_code": "+233", "currency": "GHS",  "flag_emoji": "🇬🇭", "is_served": True,  "sort_order": 6},
    {"code": "NG", "name_fr": "Nigeria",               "name_en": "Nigeria",            "dial_code": "+234", "currency": "NGN",  "flag_emoji": "🇳🇬", "is_served": True,  "sort_order": 7},
    {"code": "ML", "name_fr": "Mali",                  "name_en": "Mali",               "dial_code": "+223", "currency": "FCFA", "flag_emoji": "🇲🇱", "is_served": True,  "sort_order": 8},
    {"code": "BF", "name_fr": "Burkina Faso",          "name_en": "Burkina Faso",       "dial_code": "+226", "currency": "FCFA", "flag_emoji": "🇧🇫", "is_served": True,  "sort_order": 9},
    {"code": "CD", "name_fr": "Congo-Kinshasa",        "name_en": "DR Congo",           "dial_code": "+243", "currency": "CDF",  "flag_emoji": "🇨🇩", "is_served": True,  "sort_order": 10},
    {"code": "BJ", "name_fr": "Bénin",                 "name_en": "Benin",              "dial_code": "+229", "currency": "FCFA", "flag_emoji": "🇧🇯", "is_served": True,  "sort_order": 11},
    {"code": "TG", "name_fr": "Togo",                  "name_en": "Togo",               "dial_code": "+228", "currency": "FCFA", "flag_emoji": "🇹🇬", "is_served": True,  "sort_order": 12},
]

WAVES = [
    {"id": "WAVE-001", "name": "Vague 1", "deadline": "2025-02-05", "shipping": "2025-02-15", "arrival_min": "2025-03-10", "arrival_max": "2025-03-25", "type": "Mer", "notes": "Après Nouvel An Chinois"},
    {"id": "WAVE-002", "name": "Vague 2", "deadline": "2025-03-20", "shipping": "2025-04-01", "arrival_min": "2025-04-25", "arrival_max": "2025-05-15", "type": "Mer", "notes": "Canton Fair"},
]

SERVICE_FEES = [
    {"min": 0,      "max": 100000,  "pct": 15, "country": "CM"},
    {"min": 100001, "max": 300000,  "pct": 13, "country": "CM"},
    {"min": 300001, "max": None,    "pct": 11, "country": "CM"},
]

SHIPPING_METHODS = [
    {"name": "Avion Express", "price": 6500, "country": "CM"},
    {"name": "Mer Standard",  "price": 1800, "country": "CM"},
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

def seed_countries():
    print("🌍 Countries...")
    for c in COUNTRIES:
        upsert(Country, {"code": c["code"]}, c)


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
                "arrival_date_min": date.fromisoformat(w["arrival_min"]),
                "arrival_date_max": date.fromisoformat(w["arrival_max"]),
                "transport_type": w["type"],
                "notes": w["notes"],
            }
        )


def seed_service_fees():
    print("💼 Service fees...")
    for f in SERVICE_FEES:
        upsert(
            ServiceFeeRule,
            {"country_code": f["country"], "min_amount_fcfa": f["min"]},
            {
                "country_code": f["country"],
                "min_amount_fcfa": f["min"],
                "max_amount_fcfa": f["max"],
                "percentage": f["pct"],
            }
        )


def seed_shipping():
    print("🚢 Shipping...")
    for m in SHIPPING_METHODS:
        upsert(
            ShippingMethod,
            {"country_code": m["country"], "name": m["name"]},
            {
                "country_code": m["country"],
                "name": m["name"],
                "price_per_kg": m["price"],
                "is_active": True,
            }
        )


def seed_stats():
    print("📊 Stats...")
    stats = [
        {"key": "clients_satisfaits", "label": "Clients satisfaits", "value": 450,  "suffix": "+", "page": "homepage", "sort_order": 1},
        {"key": "commandes_livrees",  "label": "Commandes livrées",  "value": 1200, "suffix": "+", "page": "homepage", "sort_order": 2},
    ]

    for s in stats:
        upsert(Stat, {"key": s["key"]}, s)


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

SEEDERS = {
    "countries":    seed_countries,
    "waves":        seed_waves,
    "service_fees": seed_service_fees,
    "shipping":     seed_shipping,
    "stats":        seed_stats,
    "gallery":      seed_gallery,
}


def run(targets: list[str] | None = None):
    """
    targets=None  → exécute tous les seeders dans l'ordre
    targets=[...] → exécute uniquement les seeders listés
    """
    print("\n🌱 Seed START")
    app = create_app()

    with app.app_context():
        db.create_all()

        funcs = (
            [SEEDERS[t] for t in targets if t in SEEDERS]
            if targets
            else list(SEEDERS.values())
        )

        try:
            with db.session.begin():
                for fn in funcs:
                    fn()

            print("✅ Seed SUCCESS")

        except Exception as e:
            db.session.rollback()
            print("❌ Seed FAILED:", str(e))


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]  # ex: python seed.py countries waves
    run(targets=args if args else None)