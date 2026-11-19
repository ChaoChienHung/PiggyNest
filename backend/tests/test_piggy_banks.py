import pytest

@pytest.fixture
def auth_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={"username": "pb_user", "email": "pb_user@example.com", "password": "password"}
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "pb_user@example.com", "password": "password"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_piggy_bank(client, auth_headers):
    response = client.post(
        "/api/v1/piggy-banks",
        headers=auth_headers,
        json={"name": "Savings"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "Savings"
    assert "id" in data

def test_list_piggy_banks(client, auth_headers):
    # Create a couple of piggy banks
    r1 = client.post("/api/v1/piggy-banks", headers=auth_headers, json={"name": "Bank_1"})
    print("r1:", r1.json())
    r2 = client.post("/api/v1/piggy-banks", headers=auth_headers, json={"name": "Bank_2"})
    print("r2:", r2.json())
    
    response = client.get("/api/v1/piggy-banks", headers=auth_headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) >= 2, data
    names = [pb["name"] for pb in data]
    assert "Bank_1" in names
    assert "Bank_2" in names


def test_pin_piggy_bank_orders_pinned_first_and_scopes_to_user(client, auth_headers):
    first = client.post("/api/v1/piggy-banks", headers=auth_headers, json={"name": "First_Bank"}).json()
    second = client.post("/api/v1/piggy-banks", headers=auth_headers, json={"name": "Second_Bank"}).json()
    third = client.post("/api/v1/piggy-banks", headers=auth_headers, json={"name": "UOB_Bank"}).json()

    assert first["is_pinned"] is False
    assert [pb["name"] for pb in client.get("/api/v1/piggy-banks", headers=auth_headers).json()] == [
        "First_Bank",
        "Second_Bank",
        "UOB_Bank",
    ]

    # Pin the last bank so it jumps to the front
    pinned = client.put(f"/api/v1/piggy-banks/{third['id']}/pin", headers=auth_headers, json={"is_pinned": True})
    assert pinned.status_code == 200
    assert pinned.json()["is_pinned"] is True
    assert [pb["name"] for pb in client.get("/api/v1/piggy-banks", headers=auth_headers).json()] == [
        "UOB_Bank",
        "First_Bank",
        "Second_Bank",
    ]

    # Another user cannot pin/unpin this bank
    client.post("/api/v1/auth/register", json={
        "username": "pin_other", "email": "pin_other@example.com", "password": "password",
    })
    other_token = client.post("/api/v1/auth/login", data={
        "username": "pin_other@example.com", "password": "password",
    }).json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}
    assert client.put(
        f"/api/v1/piggy-banks/{third['id']}/pin", headers=other_headers, json={"is_pinned": False}
    ).status_code == 404

    # Unpinning restores original order
    unpinned = client.put(f"/api/v1/piggy-banks/{third['id']}/pin", headers=auth_headers, json={"is_pinned": False})
    assert unpinned.status_code == 200
    assert unpinned.json()["is_pinned"] is False
    assert [pb["name"] for pb in client.get("/api/v1/piggy-banks", headers=auth_headers).json()] == [
        "First_Bank",
        "Second_Bank",
        "UOB_Bank",
    ]
