import pytest
from app.models.transaction import Transaction
from app.domain.transfer_repair import mark_external_transfer

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


def test_amounts_use_exact_cents(client, auth_headers, piggy_bank_id, db):
    endpoint = f"/api/v1/piggy-banks/{piggy_bank_id}/transactions"
    for amount in (0.1, 0.2):
        assert client.post(endpoint, headers=auth_headers, json={"amount": amount, "type": "income", "category": "Change"}).status_code == 200
    assert client.get(f"/api/v1/piggy-banks/{piggy_bank_id}/balance", headers=auth_headers).json()["balance"] == 0.3
    summary = client.get("/api/v1/statistics?timeframe=all", headers=auth_headers).json()
    assert summary[0]["income"] == summary[0]["category_incomes"]["Change"] == 0.3
    assert sorted(tx.amount_minor for tx in db.query(Transaction).all()) == [10, 20]
    assert client.post(endpoint, headers=auth_headers, json={"amount": 0.001}).status_code == 422

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


def test_deleting_either_transfer_entry_removes_both(client, auth_headers, piggy_bank_id):
    target = client.post("/api/v1/piggy-banks", headers=auth_headers, json={"name": "Target"}).json()["id"]
    response = client.post("/api/v1/transfers", headers=auth_headers, json={
        "source_piggy_bank_id": piggy_bank_id, "target_piggy_bank_id": target,
        "amount": 25, "description": "Move",
    })
    assert response.status_code == 200
    transfer = response.json()
    assert transfer["transaction_id"]
    assert len(set(transfer["entry_ids"])) == 2
    for bank_id, entry_id in zip((piggy_bank_id, target), transfer["entry_ids"]):
        entries = client.get(f"/api/v1/piggy-banks/{bank_id}/transactions", headers=auth_headers).json()
        assert [(entry["id"], entry["transaction_id"]) for entry in entries] == [
            (entry_id, transfer["transaction_id"])
        ]
    assert client.delete(f"/api/v1/transactions/{transfer['entry_ids'][1]}", headers=auth_headers).status_code == 200
    for bank_id in (piggy_bank_id, target):
        assert client.get(f"/api/v1/piggy-banks/{bank_id}/transactions", headers=auth_headers).json() == []


def test_deleting_bank_removes_transfer_from_other_bank(client, auth_headers, piggy_bank_id):
    target = client.post("/api/v1/piggy-banks", headers=auth_headers, json={"name": "Target"}).json()["id"]
    client.post("/api/v1/transfers", headers=auth_headers, json={
        "source_piggy_bank_id": piggy_bank_id, "target_piggy_bank_id": target, "amount": 25,
    })
    assert client.delete(f"/api/v1/piggy-banks/{piggy_bank_id}", headers=auth_headers).status_code == 200
    assert client.get(f"/api/v1/piggy-banks/{target}/transactions", headers=auth_headers).json() == []


def test_transfer_cannot_be_created_as_single_entry_or_across_currencies(client, auth_headers, piggy_bank_id):
    single = client.post(f"/api/v1/piggy-banks/{piggy_bank_id}/transactions", headers=auth_headers,
                         json={"amount": 10, "type": "transfer"})
    assert single.status_code == 422
    eur = client.post("/api/v1/piggy-banks", headers=auth_headers,
                      json={"name": "Euro", "currency": "EUR"}).json()["id"]
    cross_currency = client.post("/api/v1/transfers", headers=auth_headers, json={
        "source_piggy_bank_id": piggy_bank_id, "target_piggy_bank_id": eur, "amount": 10,
    })
    assert cross_currency.status_code == 400
    assert client.get(f"/api/v1/piggy-banks/{piggy_bank_id}/transactions", headers=auth_headers).json() == []


def test_transfer_not_counted_as_spending(client, auth_headers, piggy_bank_id):
    target = client.post("/api/v1/piggy-banks", headers=auth_headers, json={"name": "Target"}).json()["id"]
    client.post("/api/v1/transfers", headers=auth_headers, json={
        "source_piggy_bank_id": piggy_bank_id, "target_piggy_bank_id": target, "amount": 25,
    })
    stats = client.get("/api/v1/statistics/", headers=auth_headers).json()
    assert all(row["expense"] == 0 and row["income"] == 0 for row in stats)


def test_unresolved_legacy_transfer_cannot_leave_an_orphan(client, db, auth_headers, piggy_bank_id):
    target = client.post("/api/v1/piggy-banks", headers=auth_headers, json={"name": "Target"}).json()["id"]
    result = client.post("/api/v1/transfers", headers=auth_headers, json={
        "source_piggy_bank_id": piggy_bank_id, "target_piggy_bank_id": target, "amount": 25,
    }).json()
    for entry_id in result["entry_ids"]:
        db.get(Transaction, entry_id).transfer_group_id = None
    db.get(Transaction, result["entry_ids"][0]).description = "old unmatched description"
    db.commit()

    assert client.delete(f"/api/v1/transactions/{result['entry_ids'][0]}", headers=auth_headers).status_code == 409
    assert client.delete(f"/api/v1/piggy-banks/{piggy_bank_id}", headers=auth_headers).status_code == 409
    for bank_id in (piggy_bank_id, target):
        assert len(client.get(f"/api/v1/piggy-banks/{bank_id}/transactions", headers=auth_headers).json()) == 1
    assert mark_external_transfer(db, result["entry_ids"][0]) == "transfer_out"
    assert mark_external_transfer(db, result["entry_ids"][1]) == "transfer_in"
    db.commit()
    assert client.delete(f"/api/v1/piggy-banks/{piggy_bank_id}", headers=auth_headers).status_code == 200
    assert len(client.get(f"/api/v1/piggy-banks/{target}/transactions", headers=auth_headers).json()) == 1


def test_external_transfer_is_one_entry_with_own_id(client, auth_headers, piggy_bank_id):
    result = client.post(f"/api/v1/piggy-banks/{piggy_bank_id}/transactions", headers=auth_headers,
                         json={"type": "transfer_out", "amount": -25, "description": "To another person"})
    assert result.status_code == 200
    entry = result.json()
    assert entry["transaction_id"] == f"entry:{entry['id']}"
    stats = client.get("/api/v1/statistics/", headers=auth_headers).json()
    assert sum(row["expense"] for row in stats) == 25
    assert client.delete(f"/api/v1/transactions/{entry['id']}", headers=auth_headers).status_code == 200
    assert client.get(f"/api/v1/piggy-banks/{piggy_bank_id}/transactions", headers=auth_headers).json() == []


def test_edit_transaction_by_id_changes_amount_category_note_and_date(client, auth_headers, piggy_bank_id):
    created = client.post(f"/api/v1/piggy-banks/{piggy_bank_id}/transactions", headers=auth_headers,
                          json={"type": "expense", "amount": -12, "category": "Meal", "description": "Old"}).json()
    tx_id = created["id"]
    assert client.get(f"/api/v1/transactions/{tx_id}", headers=auth_headers).json()["id"] == tx_id
    updated = client.put(f"/api/v1/transactions/{tx_id}", headers=auth_headers, json={
        "amount": -18, "category": "Transport", "description": "New note", "date": "2025-03-01T00:00:00",
    })
    assert updated.status_code == 200
    assert {key: updated.json()[key] for key in ("id", "amount", "category", "description")} == {
        "id": tx_id, "amount": -18, "category": "Transport", "description": "New note",
    }
    assert updated.json()["date"].startswith("2025-03-01")
    assert client.get(f"/api/v1/piggy-banks/{piggy_bank_id}/balance", headers=auth_headers).json()["balance"] == -18
    cleared = client.put(f"/api/v1/transactions/{tx_id}", headers=auth_headers,
                         json={"category": None, "description": None})
    assert cleared.status_code == 200
    assert cleared.json()["category"] is None and cleared.json()["description"] is None


def test_edit_piggybank_transfer_updates_both_entries(client, auth_headers, piggy_bank_id):
    target = client.post("/api/v1/piggy-banks", headers=auth_headers, json={"name": "Target"}).json()["id"]
    created = client.post("/api/v1/transfers", headers=auth_headers, json={
        "source_piggy_bank_id": piggy_bank_id, "target_piggy_bank_id": target,
        "amount": 25, "description": "Old note",
    }).json()
    debit_id, credit_id = created["entry_ids"]
    updated = client.put(f"/api/v1/transactions/{debit_id}", headers=auth_headers, json={
        "amount": -40, "description": "Corrected note", "date": "2025-03-01T00:00:00",
    })
    assert updated.status_code == 200
    debit = client.get(f"/api/v1/transactions/{debit_id}", headers=auth_headers).json()
    credit = client.get(f"/api/v1/transactions/{credit_id}", headers=auth_headers).json()
    assert (debit["amount"], credit["amount"]) == (-40, 40)
    assert debit["transaction_id"] == credit["transaction_id"] == created["transaction_id"]
    assert debit["description"] == "Transfer to Target: Corrected note"
    assert credit["description"] == "Transfer from Transactions_Bank: Corrected note"
    assert debit["date"] == credit["date"]
    assert debit["date"].startswith("2025-03-01")
    assert client.get(f"/api/v1/piggy-banks/{piggy_bank_id}/balance", headers=auth_headers).json()["balance"] == -40
    assert client.get(f"/api/v1/piggy-banks/{target}/balance", headers=auth_headers).json()["balance"] == 40
    assert client.put(f"/api/v1/transactions/{credit_id}", headers=auth_headers,
                      json={"amount": 50}).status_code == 200
    assert client.get(f"/api/v1/transactions/{debit_id}", headers=auth_headers).json()["amount"] == -50
    assert client.get(f"/api/v1/transactions/{credit_id}", headers=auth_headers).json()["amount"] == 50
    assert client.put(f"/api/v1/transactions/{credit_id}", headers=auth_headers,
                      json={"amount": -50}).status_code == 400
    assert client.put(f"/api/v1/transactions/{debit_id}", headers=auth_headers,
                      json={"category": "Meal"}).status_code == 400


def test_edit_transaction_is_scoped_to_owner(client, auth_headers, piggy_bank_id):
    tx_id = client.post(f"/api/v1/piggy-banks/{piggy_bank_id}/transactions", headers=auth_headers,
                        json={"amount": -5}).json()["id"]
    client.post("/api/v1/auth/register", json={
        "username": "another_user", "email": "another@example.com", "password": "password",
    })
    token = client.post("/api/v1/auth/login", data={
        "username": "another@example.com", "password": "password",
    }).json()["access_token"]
    other = {"Authorization": f"Bearer {token}"}
    assert client.get(f"/api/v1/transactions/{tx_id}", headers=other).status_code == 404
    assert client.put(f"/api/v1/transactions/{tx_id}", headers=other, json={"amount": -50}).status_code == 404
    assert client.get(f"/api/v1/transactions/{tx_id}", headers=auth_headers).json()["amount"] == -5
