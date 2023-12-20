from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Make sure to replace these values with actual data for your test cases
valid_jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjIwLCJ1c2VybmFtZSI6ImFzaWxiZWsiLCJleHAiOjE2OTMyMjM1NjZ9.NqtEx4QX79b6PAjQFfCKN7mcXrnl9GwIOoluVYGHe4c"


def test_create_profile():
    response = client.post("/users", json={
        "username": "testuser1",
        "phone_number": "423432",
        "name": "Test User",
        "avatar": "avatar.png",
        "preferences": "",
        "history": ''
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_create_profile_existing_username():
    client.post("/users", json={
        "username": "asilbeknew",
        "phone_number": "9900022222",
        "name": "Test User",
        "avatar": "avatar.png",
        "preferences": "{}",
        "history": "{}"
    })  # First registration
    response = client.post("/users", json={
        "username": "asilbeknew",
        "phone_number": "09876543213123123123123122323232133",
        "name": "Another User",
        "avatar": "another_avatar.png",
        "preferences": "{}",
        "history": "{}"
    })
    assert response.status_code == 400
    assert response.json()["status"] == "error"


def test_get_profile():
    response = client.get(
        "/users", headers={"Authorization": f"Bearer {valid_jwt_token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_update_profile():
    response = client.put("/users", json={
        "name": "Updated Name"
    }, headers={"Authorization": f"Bearer {valid_jwt_token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_delete_profile():
    response = client.delete(
        "/users", headers={"Authorization": f"Bearer {valid_jwt_token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
