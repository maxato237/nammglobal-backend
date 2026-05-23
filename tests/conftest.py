"""
conftest.py — Fixtures partagées pour tous les tests NAMM GLOBAL.
"""
import pytest
from config import TestingConfig
from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    """App Flask en mode test (SQLite en mémoire)."""
    application = create_app(TestingConfig())
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    """Session DB avec rollback automatique après chaque test."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()

        _db.session.bind = connection  # type: ignore[attr-defined]
        yield _db

        _db.session.remove()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(app, db):
    """Client HTTP Flask pour les tests d'intégration."""
    return app.test_client()


@pytest.fixture(scope="function")
def client_user(app, db):
    """Client + token d'accès pour un utilisateur client."""
    from tests.factories.user_factory import UserFactory
    from flask_jwt_extended import create_access_token

    user = UserFactory(role="client")
    db.session.add(user)
    db.session.commit()

    with app.app_context():
        token = create_access_token(identity=str(user.id))

    return app.test_client(), user, token


@pytest.fixture(scope="function")
def client_admin(app, db):
    """Client + token d'accès pour un super_admin."""
    from tests.factories.user_factory import UserFactory
    from flask_jwt_extended import create_access_token

    admin = UserFactory(role="super_admin")
    db.session.add(admin)
    db.session.commit()

    with app.app_context():
        token = create_access_token(identity=str(admin.id))

    return app.test_client(), admin, token
