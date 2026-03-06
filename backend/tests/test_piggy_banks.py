import pytest

@pytest.fixture
def auth_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "pb_user@example.com", "password": "password"}
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
