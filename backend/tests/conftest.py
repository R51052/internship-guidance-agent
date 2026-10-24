import pytest
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import create_app


@pytest.fixture
def settings():
    return Settings(demo_mode=True, jwt_secret="test-only-secret-with-at-least-32-characters", llm_mode="mock")


@pytest.fixture
def app(settings):
    return create_app(settings)


@pytest.fixture
def client(app):
    with TestClient(app) as value:
        yield value


@pytest.fixture
def account(client):
    response = client.post("/api/auth/register", json={"name": "Test Student", "email": "student@example.com", "password": "Strong-passphrase1!"})
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def headers(account):
    return {"Authorization": f"Bearer {account['access_token']}"}


@pytest.fixture
def profile_data():
    return {"full_name": "Test Student", "degree": "B.Tech", "year": 3, "cgpa": 8.2,
            "skills": ["Python", "FastAPI", "MongoDB"], "interests": ["Backend Development"],
            "preferred_locations": ["Bengaluru"], "preferred_work_mode": "remote", "min_stipend": 18000,
            "max_duration_months": 3}
