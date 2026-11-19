import importlib.util
from pathlib import Path


def load_cli():
    path = Path(__file__).resolve().parents[2] / "cli.py"
    spec = importlib.util.spec_from_file_location("piggynest_cli_suite", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_inprocess_cli(monkeypatch, client, email="cli@example.com", password="Password123!"):
    monkeypatch.delenv("PIGGYNEST_API_URL", raising=False)
    cli = load_cli()
    monkeypatch.setattr(cli, "is_local_server_running", lambda: False)
    monkeypatch.setattr(cli, "load_inprocess_client", lambda: client)

    reg = client.post(
        "/api/v1/auth/register",
        json={"username": email.split("@")[0], "email": email, "password": password},
    )
    assert reg.status_code == 200
    return cli


def login_cli(monkeypatch, cli, email="cli@example.com", password="Password123!"):
    answers = iter([email, password])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert cli.login() is True


def test_cli_login_rejects_wrong_password(monkeypatch, client, capsys):
    cli = make_inprocess_cli(monkeypatch, client)
    answers = iter(["cli@example.com", "WrongPassword!"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    assert cli.login() is False
    assert cli.token is None
    assert "Login failed" in capsys.readouterr().out


def test_cli_piggybank_create_list_and_delete_flow(monkeypatch, client, capsys):
    cli = make_inprocess_cli(monkeypatch, client)
    login_cli(monkeypatch, cli)

    # Create a PiggyBank
    answers = iter(["Wallet", "SGD"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.create_piggybank()
    assert "created successfully" in capsys.readouterr().out

    # List PiggyBanks
    banks = cli.list_piggybanks()
    out = capsys.readouterr().out
    assert len(banks) == 1
    pb_id = banks[0]["id"]
    assert f"ID [{pb_id}] | Name: Wallet | Currency: SGD | Balance: 0.0" in out

    # Cancel deletion with 'n'
    answers = iter([str(pb_id), "n"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.delete_piggybank()
    assert len(cli.api_get("/piggy-banks")) == 1

    # Confirm deletion with 'y'
    answers = iter([str(pb_id), "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.delete_piggybank()
    assert "Deleted successfully" in capsys.readouterr().out
    assert cli.api_get("/piggy-banks") == []


def test_cli_add_transaction_negates_expense_and_keeps_income_positive(monkeypatch, client, capsys):
    cli = make_inprocess_cli(monkeypatch, client)
    login_cli(monkeypatch, cli)
    pb = cli.api_post("/piggy-banks", json_data={"name": "Daily", "currency": "SGD"})
    pb_id = pb["id"]

    # Positive input for expense should be stored as negative
    answers = iter([str(pb_id), "7.6", "expense", "Red Ginger", "2026-11-19"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.add_transaction()
    assert "Transaction recorded successfully" in capsys.readouterr().out

    # Income should remain positive
    answers = iter([str(pb_id), "20", "income", "Allowance", "2026-11-19"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.add_transaction()
    assert "Transaction recorded successfully" in capsys.readouterr().out

    txs = cli.api_get(f"/piggy-banks/{pb_id}/transactions")
    amounts_by_desc = {tx["description"]: tx["amount"] for tx in txs}
    assert amounts_by_desc == {"Red Ginger": -7.6, "Allowance": 20.0}

    bal = cli.api_get(f"/piggy-banks/{pb_id}/balance")
    assert bal["balance"] == 12.4


def test_cli_add_transaction_handles_invalid_inputs_gracefully(monkeypatch, client, capsys):
    cli = make_inprocess_cli(monkeypatch, client)
    login_cli(monkeypatch, cli)
    pb = cli.api_post("/piggy-banks", json_data={"name": "Daily", "currency": "SGD"})

    answers = iter([str(pb["id"]), "not-a-number"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.add_transaction()
    assert "Input Error" in capsys.readouterr().out
    assert cli.api_get(f"/piggy-banks/{pb['id']}/transactions") == []


def test_cli_edit_transaction_end_to_end_and_clear_fields(monkeypatch, client, capsys):
    cli = make_inprocess_cli(monkeypatch, client)
    login_cli(monkeypatch, cli)
    pb = cli.api_post("/piggy-banks", json_data={"name": "Daily", "currency": "SGD"})
    tx = cli.api_post(
        f"/piggy-banks/{pb['id']}/transactions",
        json_data={
            "amount": -7.6,
            "type": "expense",
            "description": "Red Ginger",
            "date": "2026-11-19T00:00:00",
        },
    )
    tx_id = tx["id"]

    # Set category to Meal and update amount
    answers = iter([str(tx_id), "-8.5", "", "", "Meal", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.edit_transaction()
    assert "Update successful" in capsys.readouterr().out

    updated = cli.api_get(f"/transactions/{tx_id}")
    assert updated["amount"] == -8.5
    assert updated["category"] == "Meal"
    assert updated["description"] == "Red Ginger"

    # Pressing Enter on every prompt cancels without modifying
    answers = iter([str(tx_id), "", "", "", "", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.edit_transaction()
    assert "No changes detected" in capsys.readouterr().out

    # Clearing note and category with '-'
    answers = iter([str(tx_id), "", "", "-", "-", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.edit_transaction()
    cleared = cli.api_get(f"/transactions/{tx_id}")
    assert cleared["description"] is None
    assert cleared["category"] is None


def test_cli_edit_transaction_enforces_user_isolation(monkeypatch, client, capsys):
    # User A creates a transaction
    cli_a = make_inprocess_cli(monkeypatch, client, email="alice@example.com")
    login_cli(monkeypatch, cli_a, email="alice@example.com")
    pb_a = cli_a.api_post("/piggy-banks", json_data={"name": "AliceBank", "currency": "NTD"})
    tx_a = cli_a.api_post(
        f"/piggy-banks/{pb_a['id']}/transactions",
        json_data={"amount": -100, "type": "expense", "description": "Private"},
    )

    # User B tries to edit User A's transaction via CLI
    cli_b = make_inprocess_cli(monkeypatch, client, email="bob_iso@example.com")
    login_cli(monkeypatch, cli_b, email="bob_iso@example.com")
    answers = iter([str(tx_a["id"])])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli_b.edit_transaction()
    assert "not found or not owned" in capsys.readouterr().out


def test_cli_main_loop_displays_inprocess_mode_and_exits_cleanly(monkeypatch, client, capsys):
    cli = make_inprocess_cli(monkeypatch, client)
    answers = iter(["1", "cli@example.com", "Password123!", "1", "q"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    cli.main_loop()
    out = capsys.readouterr().out
    assert "Mode: Local in-process API (no server required)" in out
    assert "Login successful" in out
    assert "Goodbye!" in out
    assert cli._client is None
