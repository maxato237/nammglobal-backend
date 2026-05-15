"""Tâche : envoie les notifications en attente via WhatsApp/email."""


def run():
    from app import create_app
    from app.extensions import db
    from app.models import Notification

    app = create_app()
    with app.app_context():
        pending = Notification.query.filter_by(is_read=False).limit(100).all()
        sent = 0
        for notif in pending:
            pass
        print(f"[send_pending_notifications] {sent} notifications envoyées.")


if __name__ == "__main__":
    run()
