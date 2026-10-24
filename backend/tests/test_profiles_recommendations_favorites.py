import pytest


def test_profile_roundtrip_and_recommendations(client, headers, profile_data):
    assert client.put("/api/profile", headers=headers, json=profile_data).status_code == 200
    stored = client.get("/api/profile", headers=headers).json()
    assert all(stored[key] == value for key, value in profile_data.items())
    ranked = client.get("/api/recommendations", headers=headers).json()
    assert ranked["recommendations"][0]["internship"]["id"] == "demo-python"
    assert ranked["recommendations"][0]["score"] == 100
    assert all(item["eligible"] for item in ranked["recommendations"])
    assert sum(ranked["weights"].values()) == 100


def test_profile_normalization_and_invalid_fields(client, headers):
    response = client.put("/api/profile", headers=headers, json={"skills": [" Python ", "python", "SQL"]})
    assert response.json()["skills"] == ["Python", "SQL"]
    for data in ({"cgpa": 11}, {"year": 0}, {"skills": [""]}, {"min_stipend": -1}, {"user_id": "other-user"}):
        assert client.put("/api/profile", headers=headers, json=data).status_code == 422


def test_search_filters_pagination_and_details(client, headers):
    response = client.get("/api/internships?q=Python&work_mode=remote&limit=1", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["internships"]) == 1
    assert response.json()["total"] >= 1
    assert all(item["work_mode"] == "remote" for item in response.json()["internships"])
    assert client.get("/api/internships?min_stipend=1000000", headers=headers).json()["total"] == 0
    assert client.get("/api/internships?limit=0", headers=headers).status_code == 422
    detail = client.get("/api/internships/demo-python", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == "demo-python"
    assert "match" in detail.json()
    assert client.get("/api/internships/not-real", headers=headers).status_code == 404


def test_empty_database_never_fabricates_results(client, app, headers):
    for item in app.state.repository.find("internships"):
        app.state.repository.delete("internships", item["id"])
    assert client.get("/api/recommendations", headers=headers).json()["recommendations"] == []
    response = client.post("/api/agent/chat", headers=headers, json={"message": "Find internships for me"})
    assert response.status_code == 200
    assert response.json()["recommendations"] == []
    assert "No eligible internships" in response.json()["message"]
    assert all(not tool["result"].get("internships") for tool in response.json()["tool_calls"])


def test_favorites_save_deduplicate_read_and_delete(client, headers):
    for _ in range(2):
        assert client.post("/api/favorites", headers=headers, json={"internship_id": "demo-python"}).status_code == 201
    result = client.get("/api/favorites", headers=headers).json()
    assert result["total"] == 1
    assert result["favorites"][0]["internship"]["id"] == "demo-python"
    assert client.delete("/api/favorites/demo-python", headers=headers).status_code == 204
    assert client.get("/api/favorites", headers=headers).json()["total"] == 0
    assert client.delete("/api/favorites/demo-python", headers=headers).status_code == 404
    assert client.post("/api/favorites", headers=headers, json={"internship_id": "fabricated"}).status_code == 404


def test_user_data_isolation(client, headers, profile_data):
    client.put("/api/profile", headers=headers, json=profile_data)
    client.post("/api/favorites/demo-python", headers=headers)
    response = client.post("/api/auth/register", json={"name": "Second Student", "email": "second@example.com", "password": "Another-strong1!"})
    second = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert client.get("/api/favorites", headers=second).json()["total"] == 0
    assert client.delete("/api/favorites/demo-python", headers=second).status_code == 404
    assert client.get("/api/profile", headers=second).json()["skills"] == []
    assert client.get("/api/profile", headers=headers).json()["skills"] == profile_data["skills"]


def test_deleted_favorite_record_is_explicit(client, app, headers):
    client.post("/api/favorites/demo-python", headers=headers)
    app.state.repository.delete("internships", "demo-python")
    favorite = client.get("/api/favorites", headers=headers).json()["favorites"][0]
    assert favorite["internship"] is None
    assert favorite["unavailable"] is True
