"""
Tests de permissions — vérification des accès client vs admin.
"""
import pytest


BASE_AUTH = "/api/auth"


def _register_and_login(client, phone, role="client"):
    """Helper : crée un compte puis retourne le token d'accès."""
    from tests.factories.user_factory import UserFactory
    from app.extensions import db
    from flask_jwt_extended import create_access_token
    import flask

    user = UserFactory(phone=phone, role=role)
    db.session.commit()

    with flask.current_app.app_context():
        token = create_access_token(identity=str(user.id))
    return user, token


class TestUnauthenticatedAccess:
    """Les routes protégées doivent renvoyer 401 sans token."""

    def test_me_requires_auth(self, client, db):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_logout_requires_auth(self, client, db):
        resp = client.post(f"{BASE_AUTH}/logout")
        assert resp.status_code == 401


class TestClientAccess:
    """Un client authentifié peut accéder à ses propres ressources."""

    def test_get_me_success(self, client, app, db):
        reg = client.post(f"{BASE_AUTH}/register", json={
            "name": "Client Test",
            "phone": "+237699100001",
            "password": "SecurePass1!",
        })
        token = reg.get_json()["data"]["accessToken"]

        resp = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["phone"] == "+237699100001"


class TestInvalidToken:
    """Les tokens invalides ou expirés doivent être rejetés."""

    def test_random_token_rejected(self, client, db):
        resp = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer this.is.not.valid"},
        )
        assert resp.status_code == 401

    def test_missing_bearer_prefix(self, client, db):
        resp = client.get(
            "/api/auth/me",
            headers={"Authorization": "some-random-string"},
        )
        assert resp.status_code == 401


class TestTokenBlacklist:
    """Un token révoqué (après logout) ne doit plus être accepté."""

    def test_blacklisted_token_rejected(self, client, db):
        reg = client.post(f"{BASE_AUTH}/register", json={
            "name": "Logout User",
            "phone": "+237699100010",
            "password": "SecurePass1!",
        })
        token = reg.get_json()["data"]["accessToken"]
        headers = {"Authorization": f"Bearer {token}"}

        client.post(f"{BASE_AUTH}/logout", headers=headers)

        resp = client.get("/api/auth/me", headers=headers)
        assert resp.status_code == 401


class TestInactiveUser:
    """Un compte désactivé (is_active=False) doit être bloqué."""

    def test_inactive_user_cannot_login_after_deactivation(self, client, app, db):
        from tests.factories.user_factory import UserFactory
        from app.extensions import db as _db
        from flask_jwt_extended import create_access_token

        user = UserFactory(phone="+237699100020", role="client", is_active=False)
        _db.session.commit()

        with app.app_context():
            token = create_access_token(identity=str(user.id))

        resp = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code in (401, 403, 404)
