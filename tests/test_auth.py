"""
Tests d'intégration — authentification (register, login, logout, refresh).
"""
import pytest

BASE = "/api/auth"


class TestRegister:
    def test_register_success(self, client, db):
        resp = client.post(f"{BASE}/register", json={
            "name": "Marie Dupont",
            "phone": "+237699000001",
            "password": "SecurePass1!",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert "accessToken" in data["data"]

    def test_register_missing_fields(self, client, db):
        resp = client.post(f"{BASE}/register", json={"name": "Marie"})
        assert resp.status_code == 400

    def test_register_duplicate_phone(self, client, db):
        payload = {"name": "User A", "phone": "+237699000002", "password": "SecurePass1!"}
        client.post(f"{BASE}/register", json=payload)
        resp = client.post(f"{BASE}/register", json=payload)
        assert resp.status_code == 409

    def test_register_weak_password(self, client, db):
        resp = client.post(f"{BASE}/register", json={
            "name": "User B",
            "phone": "+237699000003",
            "password": "123",
        })
        assert resp.status_code == 400


class TestLogin:
    def test_login_success(self, client, db):
        client.post(f"{BASE}/register", json={
            "name": "Jean Martin",
            "phone": "+237699000010",
            "password": "SecurePass1!",
        })
        resp = client.post(f"{BASE}/login", json={
            "phone": "+237699000010",
            "password": "SecurePass1!",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "accessToken" in data["data"]

    def test_login_wrong_password(self, client, db):
        client.post(f"{BASE}/register", json={
            "name": "Jean Martin",
            "phone": "+237699000011",
            "password": "SecurePass1!",
        })
        resp = client.post(f"{BASE}/login", json={
            "phone": "+237699000011",
            "password": "WrongPassword!",
        })
        assert resp.status_code == 401

    def test_login_unknown_phone(self, client, db):
        resp = client.post(f"{BASE}/login", json={
            "phone": "+237699999999",
            "password": "AnyPass1!",
        })
        assert resp.status_code == 401

    def test_login_missing_credentials(self, client, db):
        resp = client.post(f"{BASE}/login", json={})
        assert resp.status_code == 400


class TestLogout:
    def test_logout_requires_auth(self, client, db):
        resp = client.post(f"{BASE}/logout")
        assert resp.status_code == 401

    def test_logout_success(self, client, db):
        reg = client.post(f"{BASE}/register", json={
            "name": "Paul Kenzo",
            "phone": "+237699000020",
            "password": "SecurePass1!",
        })
        token = reg.get_json()["data"]["accessToken"]

        resp = client.post(
            f"{BASE}/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    def test_token_unusable_after_logout(self, client, db):
        reg = client.post(f"{BASE}/register", json={
            "name": "Ali Baba",
            "phone": "+237699000021",
            "password": "SecurePass1!",
        })
        token = reg.get_json()["data"]["accessToken"]

        client.post(f"{BASE}/logout", headers={"Authorization": f"Bearer {token}"})

        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
