"""Tâche : purge les tokens JWT révoqués expirés de la blacklist."""
from datetime import datetime


def run():
    from app import create_app
    from app.extensions import db
    from app.models.auth_token import TokenBlacklist

    app = create_app()
    with app.app_context():
        now = datetime.utcnow()
        deleted = TokenBlacklist.query.filter(TokenBlacklist.expires_at < now).delete()
        db.session.commit()
        print(f"[purge_blacklisted_tokens] {deleted} tokens purgés.")


if __name__ == "__main__":
    run()
