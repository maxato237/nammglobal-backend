# ── Blueprints existants ──────────────────────────────────────────────────────
from .auth          import auth_bp
from .users         import users_bp
from .requests      import requests_bp
from .quotations    import quotations_bp
from .orders        import orders_bp
from .waves         import waves_bp
from .suppliers     import suppliers_bp
from .gallery       import gallery_bp
from .pricing       import pricing_bp
from .notifications import notifications_bp
from .stats         import stats_bp

# ── Nouveaux blueprints v2 ────────────────────────────────────────────────────
from .countries      import countries_bp
from .chinese_events import chinese_events_bp
from .payments       import payments_bp
from .webhooks       import webhooks_bp
from .formation      import formation_bp
from .community      import community_bp
from .contact        import contact_bp
from .settings       import settings_bp
from .uploads        import uploads_bp
from .dashboard      import dashboard_bp
from .admin          import admin_bp

all_blueprints = [
    # Existants
    auth_bp, users_bp, requests_bp, quotations_bp, orders_bp,
    waves_bp, suppliers_bp, gallery_bp, pricing_bp,
    notifications_bp, stats_bp,
    # Nouveaux v2
    countries_bp, chinese_events_bp, payments_bp, webhooks_bp,
    formation_bp, community_bp, contact_bp, settings_bp,
    uploads_bp, dashboard_bp, admin_bp,
]
