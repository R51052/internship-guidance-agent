from datetime import timedelta

import jwt
import pytest

from backend.config import Settings
from backend.database import utcnow


def test_health_is_public_and_demo_is_explicit(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "demo", "demo_mode": True, "llm_mode": "mock"}
    assert client.get("/health").status_code == 200


def test_public_internship_catalog_does_not_require_auth(client, app):
    from backend.scripts.seed_demo_data import seed_repository
    seed_repository(app.state.repository)
    response = client.get("/api/public/internships?limit=2")
    assert response.status_code == 200
    assert response.json()["total"] >= 2
    assert len(response.json()["internships"]) == 2


def test_persistent_mode_requires_configuration():
    with pytest.raises(RuntimeError, match="MONGODB_URI"):
        Settings().prepare()
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        Settings(mongodb_uri="mongodb://localhost", jwt_secret="short").prepare()
    with pytest.raises(RuntimeError, match="CORS"):
        Settings(demo_mode=True, cors_origins=["*"]).prepare()
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        Settings(demo_mode=True, llm_mode="openai").prepare()


def test_register_me_and_password_hash(client, app, account, headers):
    assert account["token_type"] == "bearer"
    assert "password" not in str(account).casefold()
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "student@example.com"
    stored = app.state.repository.get("users", account["user"]["id"])
    assert stored["password_hash"].startswith("$argon2id$")
    assert "Strong-passphrase1!" not in str(stored)


def test_duplicate_email_is_case_insensitive(client, account):
    response = client.post("/api/auth/register", json={"name": "Another Student", "email": "STUDENT@example.com", "password": "Something-secure1!"})
    assert response.status_code == 409


def test_login_and_logout_revokes_only_current_session(client, headers):
    assert client.post("/api/auth/login", json={"email": "student@example.com", "password": "wrong"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "missing@example.com", "password": "wrong"}).status_code == 401
    response = client.post("/api/auth/login", json={"email": "STUDENT@example.com", "password": "Strong-passphrase1!"})
    assert response.status_code == 200
    second_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    assert client.get("/api/auth/me", headers=second_headers).status_code == 200


def test_whitespace_in_password_is_preserved(client):
    payload = {"name": "Space Student", "email": "space@example.com", "password": "  passphrase  "}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/login", json={"email": payload["email"], "password": "passphrase"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]}).status_code == 200


@pytest.mark.parametrize("token", [None, "garbage", "e30.e30.invalid"])
def test_protected_endpoints_reject_bad_tokens(client, token):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    for path in ("/api/profile", "/api/recommendations", "/api/favorites", "/api/internships", "/api/auth/me"):
        assert client.get(path, headers=headers).status_code == 401


def test_expired_and_untracked_tokens_rejected(client, settings, account):
    for expiry in (-1, 20):
        token = jwt.encode({"sub": account["user"]["id"], "jti": "not-a-session", "iss": "internship-guidance",
                            "iat": utcnow() - timedelta(minutes=2), "exp": utcnow() + timedelta(minutes=expiry)},
                           settings.jwt_secret, algorithm="HS256")
        assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


@pytest.mark.parametrize("payload", [
    {"name": "A", "email": "bad", "password": "secret"},
    {"name": "Valid Name", "email": "valid@example.com", "password": "        "},
    {"name": "Valid Name", "email": "valid@example.com", "password": "abcdefgh", "admin": True},
])
def test_validation_does_not_echo_credentials(client, payload):
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422
    assert payload["password"] not in response.text
    assert all("input" not in item for item in response.json()["detail"])


def test_cors_only_allows_configured_origins(client):
    for origin, expected in (("http://localhost:5173", 200), ("http://127.0.0.1:50408", 200), ("https://untrusted.example", 400)):
        response = client.options("/api/profile", headers={"Origin": origin, "Access-Control-Request-Method": "PUT",
                                                           "Access-Control-Request-Headers": "Authorization, Content-Type"})
        assert response.status_code == expected
        if expected == 200:
            assert response.headers["access-control-allow-origin"] == origin
