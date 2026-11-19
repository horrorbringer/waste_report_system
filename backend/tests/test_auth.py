from fastapi.testclient import TestClient


def test_register_and_login_flow(client: TestClient):
    # Register new resident
    res = client.post(
        "/api/auth/register",
        json={
            "full_name": "Alice Resident",
            "email": "alice@example.com",
            "password": "Password123",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["role"] == "resident"
    assert "access_token" in data

    # Duplicate email fails with 409
    dup = client.post(
        "/api/auth/register",
        json={
            "full_name": "Alice Duplicate",
            "email": "ALICE@example.com",
            "password": "Password123",
        },
    )
    assert dup.status_code == 409

    # Login succeeds with valid credentials
    login = client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "Password123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    # /me returns authenticated profile
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["full_name"] == "Alice Resident"


def test_login_invalid_credentials(client: TestClient, seed_users_and_categories: dict):
    res = client.post(
        "/api/auth/login",
        json={"email": "resident1@test.local", "password": "WrongPassword"},
    )
    assert res.status_code == 401


def test_me_requires_auth(client: TestClient):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
