"""Tâche : ferme les vagues dont la deadline est dépassée."""
from datetime import date


def run():
    from app import create_app
    from app.extensions import db
    from app.models import Wave

    app = create_app()
    with app.app_context():
        today = date.today()
        expired = Wave.query.filter(
            Wave.status == "open",
            Wave.deadline_date < today,
        ).all()
        for w in expired:
            w.status = "closed"
        db.session.commit()
        print(f"[close_expired_waves] {len(expired)} vagues fermées.")


if __name__ == "__main__":
    run()
