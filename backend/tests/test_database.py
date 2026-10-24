import os
from datetime import date
from uuid import uuid4

import pytest
from bson import ObjectId

from backend.database import ConflictError, MemoryRepository, MongoRepository, serialize, utcnow
from backend.scripts.seed_demo_data import seed_repository
from backend.scripts.validate_database import validate_repository


def test_memory_repository_isolation_conflict_and_readback():
    repo = MemoryRepository()
    document = {"id": "user-1", "email": "first@example.com", "nested": {"value": 1}}
    repo.insert("users", document)
    document["nested"]["value"] = 99
    read = repo.get("users", "user-1")
    assert read["nested"]["value"] == 1
    read["nested"]["value"] = 200
    assert repo.get("users", "user-1")["nested"]["value"] == 1
    with pytest.raises(ConflictError):
        repo.insert("users", {"id": "user-2", "email": "first@example.com"})
    repo.upsert("profiles", "user-1", {"skills": ["Python"]})
    assert repo.one("profiles", {"id": "user-1"})["skills"] == ["Python"]
    assert repo.delete("profiles", "user-1") is True
    assert repo.get("profiles", "user-1") is None


def test_safe_serialization_objectid_and_dates():
    identifier = ObjectId()
    document = {"_id": identifier, "deadline": date(2026, 10, 23), "nested": [{"created": utcnow()}]}
    result = serialize(document)
    assert result["id"] == str(identifier)
    assert result["deadline"] == "2026-10-23"
    assert isinstance(result["nested"][0]["created"], str)
    assert document["_id"] is identifier


def test_seed_idempotency_and_database_validation():
    repo = MemoryRepository()
    assert seed_repository(repo) == 10
    assert seed_repository(repo) == 0
    assert validate_repository(repo)["valid"] is True
    assert all(item["is_demo"] and item["apply_url"] is None for item in repo.find("internships"))
    repo.upsert("favorites", "orphan", {"user_id": "not-real", "internship_id": "not-real"})
    report = validate_repository(repo)
    assert report["valid"] is False
    assert report["errors"][0]["error"] == "Orphaned favorite"


@pytest.mark.skipif(not os.getenv("MONGODB_TEST_URI"), reason="MONGODB_TEST_URI not configured; offline repository covered separately")
def test_real_mongodb_repository_contract():
    # Uses a unique disposable database; never touches the configured application database.
    repo = MongoRepository(os.environ["MONGODB_TEST_URI"], "internship_test_" + uuid4().hex)
    try:
        repo.insert("users", {"id": "one", "email": "test@example.com"})
        assert repo.get("users", "one")["email"] == "test@example.com"
        with pytest.raises(ConflictError):
            repo.insert("users", {"id": "two", "email": "test@example.com"})
        seed_repository(repo)
        assert validate_repository(repo)["valid"] is True
        assert repo.delete("users", "one") is True
    finally:
        repo.client.drop_database(repo.db.name)
        repo.close()
