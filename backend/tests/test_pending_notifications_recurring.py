import pytest

from app.domain.recurring import advance_date


def _register_and_login(client, username: str, email: str, password: str = "password123"):
    client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    res = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_a(client):
    headers = _register_and_login(client, "alice_pnr", "alice_pnr@example.com")
    pb = client.post("/api/v1/piggy-banks", headers=headers, json={"name": "CardBank", "currency": "NTD"}).json()
    return headers, pb


@pytest.fixture
def user_b(client):
    headers = _register_and_login(client, "bob_pnr", "bob_pnr@example.com")
    pb = client.post("/api/v1/piggy-banks", headers=headers, json={"name": "BobBank", "currency": "USD"}).json()
    return headers, pb


def test_advance_date_handles_month_end_and_leap_year():
    assert advance_date("2026-01-31", "monthly", 1, anchor_day=31) == "2026-02-28"
    assert advance_date("2026-02-28", "monthly", 1, anchor_day=31) == "2026-03-31"
    assert advance_date("2024-02-29", "yearly", 1, anchor_day=29) == "2025-02-28"
    assert advance_date("2026-11-01", "weekly", 2) == "2026-11-15"
    assert advance_date("2026-11-01", "daily", 5) == "2026-11-06"


def test_pending_transaction_lifecycle_and_notifications(client, user_a, user_b):
    headers_a, pb_a = user_a
    headers_b, _ = user_b

    # Stage a delayed credit-card charge with no decided date yet
    create_res = client.post(
        "/api/v1/pending-transactions",
        headers=headers_a,
        json={
            "piggy_bank_id": pb_a["id"],
            "amount": -1250.5,
            "type": "expense",
            "category": "Shopping",
            "description": "Online order (delayed billing)",
        },
    )
    assert create_res.status_code == 200, create_res.text
    pending = create_res.json()
    assert pending["status"] == "pending"
    assert pending["expected_date"] is None
    assert pending["piggy_bank_name"] == "CardBank"

    # Pending items must NOT affect PiggyBank balance before confirmation
    bal = client.get(f"/api/v1/piggy-banks/{pb_a['id']}/balance", headers=headers_a).json()
    assert bal["balance"] == 0.0
    assert bal["transaction_count"] == 0

    # Cross-user isolation
    assert client.get("/api/v1/pending-transactions", headers=headers_b).json() == []
    assert client.put(
        f"/api/v1/pending-transactions/{pending['id']}",
        headers=headers_b,
        json={"description": "Hacked"},
    ).status_code == 404
    assert client.post(
        f"/api/v1/pending-transactions/{pending['id']}/confirm",
        headers=headers_b,
        json={},
    ).status_code == 404
    assert client.delete(
        f"/api/v1/pending-transactions/{pending['id']}",
        headers=headers_b,
    ).status_code == 404

    # Edit pending item before confirmation
    edit_res = client.put(
        f"/api/v1/pending-transactions/{pending['id']}",
        headers=headers_a,
        json={"amount": -1300.0, "expected_date": "2026-11-25"},
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["amount"] == -1300.0
    assert edit_res.json()["expected_date"] == "2026-11-25"

    # Confirm with final settlement date
    confirm_res = client.post(
        f"/api/v1/pending-transactions/{pending['id']}/confirm",
        headers=headers_a,
        json={"date": "2026-11-26T00:00:00", "amount": -1299.0},
    )
    assert confirm_res.status_code == 200, confirm_res.text
    tx = confirm_res.json()
    assert tx["amount"] == -1299.0
    assert tx["date"].startswith("2026-11-26")

    # Balance now reflects the confirmed transaction
    bal_after = client.get(f"/api/v1/piggy-banks/{pb_a['id']}/balance", headers=headers_a).json()
    assert bal_after["balance"] == -1299.0
    assert bal_after["transaction_count"] == 1

    # Pending list is now empty; double-confirming is rejected
    assert client.get("/api/v1/pending-transactions", headers=headers_a).json() == []
    assert client.post(
        f"/api/v1/pending-transactions/{pending['id']}/confirm",
        headers=headers_a,
        json={},
    ).status_code == 400

    # Two in-app notifications exist (created + confirmed)
    notif_list = client.get("/api/v1/notifications", headers=headers_a).json()
    assert notif_list["unread_count"] == 2
    assert len(notif_list["items"]) == 2
    assert client.get("/api/v1/notifications", headers=headers_b).json()["items"] == []

    # Mark one read, then mark all read, then delete
    first_id = notif_list["items"][0]["id"]
    assert client.put(f"/api/v1/notifications/{first_id}/read", headers=headers_b).status_code == 404
    read_res = client.put(f"/api/v1/notifications/{first_id}/read", headers=headers_a)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True
    assert client.get("/api/v1/notifications", headers=headers_a).json()["unread_count"] == 1

    read_all = client.post("/api/v1/notifications/read-all", headers=headers_a)
    assert read_all.status_code == 200
    assert read_all.json()["updated_count"] == 1
    assert client.get("/api/v1/notifications", headers=headers_a).json()["unread_count"] == 0

    del_res = client.delete(f"/api/v1/notifications/{first_id}", headers=headers_a)
    assert del_res.status_code == 200
    assert len(client.get("/api/v1/notifications", headers=headers_a).json()["items"]) == 1


def test_recurring_rule_idempotent_runs_pause_stop_and_history_preservation(client, user_a, user_b):
    headers_a, pb_a = user_a
    headers_b, _ = user_b

    # Create an initial transaction on 2026-01-15 and attach a monthly rule
    tx_res = client.post(
        f"/api/v1/piggy-banks/{pb_a['id']}/transactions",
        headers=headers_a,
        json={
            "amount": -500.0,
            "type": "expense",
            "category": "Software",
            "description": "Cloud Plan",
            "date": "2026-01-15T00:00:00",
        },
    )
    assert tx_res.status_code == 200
    initial_tx = tx_res.json()

    # Attach rule starting 2026-01-15 with end_date 2026-04-15 (using future-safe as_of testing)
    rule_res = client.post(
        "/api/v1/recurring",
        headers=headers_a,
        json={
            "piggy_bank_id": pb_a["id"],
            "amount": -500.0,
            "type": "expense",
            "category": "Software",
            "description": "Cloud Plan",
            "frequency": "monthly",
            "interval": 1,
            "start_date": "2026-01-15",
            "end_date": "2026-04-15",
            "initial_transaction_id": initial_tx["id"],
        },
    )
    assert rule_res.status_code == 200, rule_res.text
    rule = rule_res.json()
    # Because today is 2026-11-20 in the test environment or later, Jan..Apr are all <= today
    # so Feb, Mar, Apr should have been posted automatically (total 4 occurrences: Jan + Feb + Mar + Apr)
    # and the rule should now be 'stopped' because end_date 2026-04-15 was reached!
    txs = client.get(f"/api/v1/piggy-banks/{pb_a['id']}/transactions", headers=headers_a).json()
    assert len(txs) == 4
    assert sorted(tx["date"][:10] for tx in txs) == [
        "2026-01-15",
        "2026-02-15",
        "2026-03-15",
        "2026-04-15",
    ]
    assert all(tx["recurring_rule_id"] == rule["id"] for tx in txs)
    assert rule["status"] == "stopped"
    assert rule["execution_count"] == 4

    # Re-running due rules must be strictly idempotent (0 duplicates!)
    rerun = client.post("/api/v1/recurring/run-due", headers=headers_a, json={"as_of": "2026-12-31"})
    assert rerun.status_code == 200
    assert rerun.json()["posted_count"] == 0
    assert len(client.get(f"/api/v1/piggy-banks/{pb_a['id']}/transactions", headers=headers_a).json()) == 4

    # Create a future rule (2099-01-01) so we can test pause, stop, and explicit as_of
    future_rule = client.post(
        "/api/v1/recurring",
        headers=headers_a,
        json={
            "piggy_bank_id": pb_a["id"],
            "amount": -200.0,
            "type": "expense",
            "category": "Utilities",
            "description": "Future Mobile Plan",
            "frequency": "monthly",
            "interval": 1,
            "start_date": "2099-01-01",
        },
    ).json()
    assert future_rule["status"] == "active"
    assert future_rule["execution_count"] == 0

    # Cross-user isolation on recurring rules
    assert client.put(
        f"/api/v1/recurring/{future_rule['id']}",
        headers=headers_b,
        json={"status": "paused"},
    ).status_code == 404
    assert client.delete(f"/api/v1/recurring/{future_rule['id']}", headers=headers_b).status_code == 404

    # Run as of 2099-02-01 -> posts Jan and Feb (2 transactions)
    run1 = client.post("/api/v1/recurring/run-due", headers=headers_a, json={"as_of": "2099-02-01"}).json()
    assert run1["posted_count"] == 2

    # Idempotent rerun as of 2099-02-01 -> posts 0
    run2 = client.post("/api/v1/recurring/run-due", headers=headers_a, json={"as_of": "2099-02-01"}).json()
    assert run2["posted_count"] == 0

    # Pause the rule -> running as of 2099-05-01 must post 0 while keeping the 2 historical entries
    paused = client.put(
        f"/api/v1/recurring/{future_rule['id']}",
        headers=headers_a,
        json={"status": "paused"},
    )
    assert paused.status_code == 200
    assert paused.json()["status"] == "paused"
    run3 = client.post("/api/v1/recurring/run-due", headers=headers_a, json={"as_of": "2099-05-01"}).json()
    assert run3["posted_count"] == 0

    # Delete the rule -> historical transactions remain intact with recurring_rule_id cleared
    del_rule = client.delete(f"/api/v1/recurring/{future_rule['id']}", headers=headers_a)
    assert del_rule.status_code == 200
    all_txs = client.get(f"/api/v1/piggy-banks/{pb_a['id']}/transactions", headers=headers_a).json()
    future_txs = [tx for tx in all_txs if tx["description"] == "Future Mobile Plan"]
    assert len(future_txs) == 2
    assert all(tx["recurring_rule_id"] is None for tx in future_txs)
