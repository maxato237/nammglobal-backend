"""
UserFactory — génère des instances User pour les tests.
"""
import factory
from factory.alchemy import SQLAlchemyModelFactory

from app.extensions import db, bcrypt
from app.models import User


def _default_hash():
    return bcrypt.generate_password_hash("TestPass123!").decode("utf-8")


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "flush"

    full_name     = factory.Sequence(lambda n: f"Test User {n}")
    phone         = factory.Sequence(lambda n: f"+23769000{n:04d}")
    whatsapp      = factory.LazyAttribute(lambda obj: obj.phone)
    email         = factory.Sequence(lambda n: f"user{n}@test.nammglobal.com")
    role          = "client"
    is_active     = True
    email_verified = False
    phone_verified = False
    # hash pré-calculé pour éviter le flush avec password_hash=None
    password_hash = factory.LazyFunction(_default_hash)
