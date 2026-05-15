from app.extensions import db
from app.models.audit import AuditLog


class AuditService:
    @staticmethod
    def log(
        entity_type: str,
        action: str,
        entity_id: int = None,
        actor=None,
        before_state: dict = None,
        after_state: dict = None,
        ip_address: str = None,
        user_agent: str = None,
    ):
        entry = AuditLog(
            actor_user_id=actor.id if actor else None,
            actor_role=actor.role if actor else None,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.session.add(entry)
        db.session.commit()
        return entry
