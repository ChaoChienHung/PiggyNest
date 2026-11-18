def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "securepassword"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

    # Test duplicate registration
    response_dup = client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "securepassword"}
    )
    assert response_dup.status_code == 400

def test_login_user(client):
    # First register
    client.post(
        "/api/v1/auth/register",
        json={"username": "loginuser", "email": "login@example.com", "password": "mypassword"}
    )
    
    # Then login
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "login@example.com", "password": "mypassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_test_token(client):
    # Register and login
    client.post(
        "/api/v1/auth/register",
        json={"username": "tokenuser", "email": "token@example.com", "password": "mypassword"}
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "token@example.com", "password": "mypassword"}
    )
    token = login_response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/auth/test-token", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "token@example.com"


def test_algorithm_name_is_not_a_valid_signing_key(client):
    from datetime import datetime, timedelta
    from jose import jwt

    user = client.post("/api/v1/auth/register", json={
        "username": "forgery_user", "email": "forgery@example.com", "password": "password",
    }).json()
    forged = jwt.encode({
        "sub": str(user["id"]), "exp": datetime.utcnow() + timedelta(minutes=5),
    }, "HS256", algorithm="HS256")
    response = client.post("/api/v1/auth/test-token", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_transactions_per_page_setting_is_per_user(client):
    def login(name):
        client.post("/api/v1/auth/register", json={
            "username": name, "email": f"{name}@example.com", "password": "password"})
        token = client.post("/api/v1/auth/login", data={
            "username": f"{name}@example.com", "password": "password"}).json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    first, second = login("page_size_a"), login("page_size_b")
    assert client.post("/api/v1/auth/test-token", headers=first).json()["transactions_per_page"] == 20
    for value in (10, 50, 0):
        updated = client.put("/api/v1/auth/me", headers=first, json={"transactions_per_page": value})
        assert updated.status_code == 200 and updated.json()["transactions_per_page"] == value
    assert client.put("/api/v1/auth/me", headers=first, json={"transactions_per_page": 7}).status_code == 422
    assert client.post("/api/v1/auth/test-token", headers=first).json()["transactions_per_page"] == 0
    assert client.post("/api/v1/auth/test-token", headers=second).json()["transactions_per_page"] == 20


def test_date_format_setting_is_per_user_and_keeps_stored_dates(client):
    def login(name):
        client.post("/api/v1/auth/register", json={
            "username": name, "email": f"{name}@example.com", "password": "password"})
        token = client.post("/api/v1/auth/login", data={
            "username": f"{name}@example.com", "password": "password"}).json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    first, second = login("date_format_a"), login("date_format_b")
    assert client.post("/api/v1/auth/test-token", headers=first).json()["date_format"] == "YYYY-MM-DD"
    bank = client.post("/api/v1/piggy-banks", headers=first, json={"name": "Dates"}).json()["id"]
    tx = client.post(f"/api/v1/piggy-banks/{bank}/transactions", headers=first, json={
        "amount": -5, "type": "expense", "date": "2026-03-04T00:00:00"}).json()

    for value in ("DD/MM/YYYY", "MM/DD/YYYY"):
        updated = client.put("/api/v1/auth/me", headers=first, json={"date_format": value})
        assert updated.status_code == 200 and updated.json()["date_format"] == value
    assert client.put("/api/v1/auth/me", headers=first, json={"date_format": "YY.MM.DD"}).status_code == 422
    assert client.post("/api/v1/auth/test-token", headers=second).json()["date_format"] == "YYYY-MM-DD"
    # The setting only changes how clients present dates; stored values stay ISO.
    stored = client.get(f"/api/v1/transactions/{tx['id']}", headers=first).json()
    assert stored["date"].startswith("2026-03-04")
