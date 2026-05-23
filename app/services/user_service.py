from datetime import datetime

from app.extensions import db
from app.models import User
from app.services.audit_service import AuditService


class UserService:
    @staticmethod
    def get_me(user_id: int) -> User:
        return User.query.get_or_404(user_id)

    @staticmethod
    def update_profile(user: User, data: dict, actor: User = None) -> User:
        allowed = ("full_name", "phone", "whatsapp", "email", "city", "country_code", "preferred_otp_channel")
        before = {k: getattr(user, k) for k in allowed}

        for field in allowed:
            if field in data:
                setattr(user, field, data[field])

        user.updated_at = datetime.utcnow()
        db.session.commit()

        AuditService.log(
            entity_type="User",
            action="update_profile",
            entity_id=user.id,
            actor=actor or user,
            before_state=before,
            after_state={k: getattr(user, k) for k in allowed},
        )
        return user

    @staticmethod
    def upload_avatar(user: User, public_id: str, url: str, actor: User = None) -> User:
        before = {"avatar_public_id": user.avatar_public_id, "avatar_url": user.avatar_url}
        user.avatar_public_id = public_id
        user.avatar_url = url
        user.updated_at = datetime.utcnow()
        db.session.commit()

        AuditService.log(
            entity_type="User",
            action="upload_avatar",
            entity_id=user.id,
            actor=actor or user,
            before_state=before,
            after_state={"avatar_public_id": public_id, "avatar_url": url},
        )
        return user

    @staticmethod
    def list_users_admin(page: int = 1, per_page: int = 20, role: str = None,
                         is_active: bool = None, search: str = None):
        query = User.query.filter(User.deleted_at.is_(None))

        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if search:
            like = f"%{search}%"
            query = query.filter(
                db.or_(
                    User.full_name.ilike(like),
                    User.email.ilike(like),
                    User.phone.ilike(like),
                )
            )

        return query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def change_role(user: User, new_role: str, actor: User) -> User:
        before_role = user.role
        user.role = new_role
        user.updated_at = datetime.utcnow()
        db.session.commit()

        AuditService.log(
            entity_type="User",
            action="change_role",
            entity_id=user.id,
            actor=actor,
            before_state={"role": before_role},
            after_state={"role": new_role},
        )
        return user

    @staticmethod
    def lock_user(user: User, locked_until: datetime, actor: User) -> User:
        before = {"locked_until": str(user.locked_until), "is_active": user.is_active}
        user.locked_until = locked_until
        user.updated_at = datetime.utcnow()
        db.session.commit()

        AuditService.log(
            entity_type="User",
            action="lock_user",
            entity_id=user.id,
            actor=actor,
            before_state=before,
            after_state={"locked_until": str(locked_until)},
        )
        return user

    @staticmethod
    def soft_delete_user(user: User, actor: User) -> User:
        user.deleted_at = datetime.utcnow()
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.session.commit()

        AuditService.log(
            entity_type="User",
            action="soft_delete",
            entity_id=user.id,
            actor=actor,
            before_state={"deleted_at": None, "is_active": True},
            after_state={"deleted_at": str(user.deleted_at), "is_active": False},
        )
        return user
