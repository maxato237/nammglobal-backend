"""Tâche : expire les devis dont valid_until est dépassé."""
from datetime import datetime


def run():
    from app import create_app
    from app.extensions import db
    from app.models import Quotation

    app = create_app()
    with app.app_context():
        now = datetime.utcnow().date()
        expired = Quotation.query.filter(
            Quotation.status == "sent",
            Quotation.valid_until < now,
        ).all()
        for q in expired:
            q.status = "expired"
        db.session.commit()
        print(f"[close_expired_quotations] {len(expired)} devis expirés.")


if __name__ == "__main__":
    run()
