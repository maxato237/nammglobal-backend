from .auth          import auth_bp
from .requests      import requests_bp
from .quotations    import quotations_bp
from .orders        import orders_bp
from .waves         import waves_bp
from .suppliers     import suppliers_bp
from .gallery       import gallery_bp
from .pricing       import pricing_bp
from .notifications import notifications_bp
from .stats         import stats_bp
from .users         import users_bp

all_blueprints = [
    auth_bp, requests_bp, quotations_bp, orders_bp,
    waves_bp, suppliers_bp, gallery_bp, pricing_bp,
    notifications_bp, stats_bp, users_bp,
]
