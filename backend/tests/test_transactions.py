import pytest

@pytest.fixture
def auth_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={"username": "tx_user", "email": "tx_user@example.com", "password": "password"}
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "tx_user@example.com", "password": "password"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def piggy_bank_id(client, auth_headers):
    response = client.post(
        "/api/v1/piggy-banks",
        headers=auth_headers,
        json={"name": "Transactions_Bank"}
    )
    return response.json()["id"]

def test_add_transaction(client, auth_headers, piggy_bank_id):
    response = client.post(
        f"/api/v1/piggy-banks/{piggy_bank_id}/transactions",
        headers=auth_headers,
        json={
            "description": "Salary",
            "amount": 2500.0,
            "category": "Income"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 2500.0
    assert data["category"] == "Income"
    assert "id" in data

def test_get_balance(client, auth_headers, piggy_bank_id):
    client.post(
        f"/api/v1/piggy-banks/{piggy_bank_id}/transactions",
        headers=auth_headers,
        json={"description": "Deps", "amount": 1000.0}
    )
    client.post(
        f"/api/v1/piggy-banks/{piggy_bank_id}/transactions",
        headers=auth_headers,
        json={"description": "Withdraw", "amount": -200.0}
    )
    
    response = client.get(
        f"/api/v1/piggy-banks/{piggy_bank_id}/balance",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["balance"] == 800.0
    assert data["transaction_count"] == 2

def test_get_transactions(client, auth_headers, piggy_bank_id):
    client.post(
        f"/api/v1/piggy-banks/{piggy_bank_id}/transactions",
        headers=auth_headers,
        json={"description": "Test Tx", "amount": 50.0}
    )
    
    response = client.get(
        f"/api/v1/piggy-banks/{piggy_bank_id}/transactions",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(tx["description"] == "Test Tx" for tx in data)

def test_transfer(client, auth_headers, piggy_bank_id):
    pb2_response = client.post(
        "/api/v1/piggy-banks",
        headers=auth_headers,
        json={"name": "Target_Bank"}
    )
    target_pb_id = pb2_response.json()["id"]

    # Add initial balance
    client.post(
        f"/api/v1/piggy-banks/{piggy_bank_id}/transactions",
        headers=auth_headers,
        json={"description": "Initial", "amount": 500.0}
    )

    # Perform transfer
    response = client.post(
        f"/api/v1/transfers",
        headers=auth_headers,
        json={
            "source_piggy_bank_id": piggy_bank_id,
            "target_piggy_bank_id": target_pb_id,
            "amount": 200.0,
            "description": "Send money"
        }
    )
    assert response.status_code == 200

    # Check balances
    bal1 = client.get(f"/api/v1/piggy-banks/{piggy_bank_id}/balance", headers=auth_headers).json()
    bal2 = client.get(f"/api/v1/piggy-banks/{target_pb_id}/balance", headers=auth_headers).json()

    assert bal1["balance"] == 300.0
    assert bal2["balance"] == 200.0
