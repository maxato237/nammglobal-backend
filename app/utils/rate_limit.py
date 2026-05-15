"""
Helpers pour Flask-Limiter. L'extension est initialisée dans extensions.py
dès que Flask-Limiter est installé.

Usage dans une route :
    from app.utils.rate_limit import limiter
    @bp.route("/login", methods=["POST"])
    @limiter.limit("10 per minute")
    def login(): ...
"""
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])
except ImportError:
    class _NoopLimiter:
        def limit(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

        def init_app(self, app):
            pass

    limiter = _NoopLimiter()
