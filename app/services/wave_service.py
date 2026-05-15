from app.extensions import db
from app.models import Wave


class WaveService:
    @staticmethod
    def get_calendar(country_code: str = None, year: int = None):
        """Fusionne vagues + events chinois pour la vue calendrier."""
        from app.models import ChineseEvent
        from datetime import date

        q = Wave.query
        if country_code:
            q = q.filter((Wave.country_code == country_code) | (Wave.country_code.is_(None)))
        if year:
            q = q.filter(db.extract("year", Wave.deadline_date) == year)
        waves = q.order_by(Wave.deadline_date).all()

        events_q = ChineseEvent.query
        if year:
            events_q = events_q.filter_by(year=year)
        events = events_q.order_by(ChineseEvent.date_start).all()

        return {
            "waves": [w.to_dict() for w in waves],
            "chinese_events": [e.to_dict() for e in events],
        }

    @staticmethod
    def update_status(wave: Wave, new_status: str, actor=None):
        from app.services.audit_service import AuditService
        before = {"status": wave.status}
        wave.status = new_status
        db.session.commit()
        AuditService.log(
            entity_type="wave",
            action="status_change",
            entity_id=wave.id,
            actor=actor,
            before_state=before,
            after_state={"status": new_status},
        )
        return wave
