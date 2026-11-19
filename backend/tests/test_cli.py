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


# ---------------------------------------------------------------------------
# Transport selection & remote safety
# ---------------------------------------------------------------------------

def test_remote_cli_does_not_inspect_unrelated_local_database(monkeypatch, capsys):
    monkeypatch.setenv("PIGGYNEST_API_URL", "https://piggynest.example/api/v1/")
    cli = load_cli()
    assert cli.BASE_URL == "https://piggynest.example/api/v1"
    cli.inspect_db()
    assert "local-only" in capsys.readouterr().out


def test_cli_falls_back_to_inprocess_api_when_local_server_is_down(monkeypatch, client):
    cli = make_inprocess_cli(monkeypatch, client, email="cli_user@example.com")
    login_cli(monkeypatch, cli, email="cli_user@example.com")
    assert cli._transport_mode == "inprocess"

    created = cli.api_post("/piggy-banks", json_data={"name": "Cash", "currency": "NTD"})
    assert created["name"] == "Cash"
    banks = cli.api_get("/piggy-banks")
    assert [b["name"] for b in banks] == ["Cash"]


def test_cli_uses_http_when_remote_api_url_is_set(monkeypatch):
    monkeypatch.setenv("PIGGYNEST_API_URL", "https://piggynest.example/api/v1/")
    cli = load_cli()
    monkeypatch.setattr(cli, "is_local_server_running", lambda: False)
    monkeypatch.setattr(
        cli,
        "load_inprocess_client",
        lambda: (_ for _ in ()).throw(AssertionError("remote CLI must not fall back to local in-process app")),
    )
    try:
        cli.get_client()
        assert cli._transport_mode == "http"
    finally:
        cli.close_client()


def test_cli_prefers_http_when_local_server_is_running(monkeypatch):
    monkeypatch.delenv("PIGGYNEST_API_URL", raising=False)
    cli = load_cli()
    monkeypatch.setattr(cli, "is_local_server_running", lambda: True)
    monkeypatch.setattr(
        cli,
        "load_inprocess_client",
        lambda: (_ for _ in ()).throw(AssertionError("should use running local HTTP server")),
    )
    try:
        cli.get_client()
        assert cli._transport_mode == "http"
    finally:
        cli.close_client()


# ---------------------------------------------------------------------------
# Date format parsing & mocked edit unit tests
# ---------------------------------------------------------------------------

def test_cli_edits_normal_transaction_by_id(monkeypatch):
    cli = load_cli()
    answers = iter(["42", "-18", "expense", "New note", "Transport", "2025-03-01"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    seen = {}

    def get(endpoint):
        seen["get"] = endpoint
        return {
            "id": 42, "transaction_id": "entry:42", "type": "expense",
            "amount": -12, "description": "Old", "category": "Meal", "date": "2025-02-01T00:00:00",
        }

    def put(endpoint, json_data):
        seen["put"] = (endpoint, json_data)
        return {"id": 42}

    monkeypatch.setattr(cli, "api_get", get)
    monkeypatch.setattr(cli, "api_put", put)

    cli.edit_transaction()

    assert seen["get"] == "/transactions/42"
    assert seen["put"] == ("/transactions/42", {
        "amount": -18, "type": "expense", "description": "New note",
        "category": "Transport", "date": "2025-03-01T00:00:00",
    })


def test_cli_edits_piggybank_transfer_without_changing_direction(monkeypatch):
    cli = load_cli()
    answers = iter(["7", "-40", "Corrected note", "2025-03-01"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    monkeypatch.setattr(cli, "api_get", lambda _: {
        "id": 7, "transaction_id": "shared-id", "type": "transfer", "amount": -25,
        "description": "Transfer to Target: Old note", "category": "Transfer Out",
        "date": "2025-02-01T00:00:00",
    })
    seen = {}
    monkeypatch.setattr(cli, "api_put", lambda endpoint, json_data: seen.update({
        "endpoint": endpoint, "payload": json_data,
    }) or {"id": 7})

    cli.edit_transaction()

    assert seen == {"endpoint": "/transactions/7", "payload": {
        "amount": -40, "description": "Corrected note", "date": "2025-03-01T00:00:00",
    }}


def test_cli_uses_account_date_format_for_prompts_and_parsing(monkeypatch):
    cli = load_cli()
    monkeypatch.setattr(cli, "api_post", lambda endpoint, json_data=None, data=None: {"date_format": "DD/MM/YYYY"})
    cli.load_preferences()
    assert cli.date_format == "DD/MM/YYYY"
    assert cli.format_date("2025-02-01T00:00:00") == "01/02/2025"
    assert cli.parse_date("04/03/2025") == "2025-03-04T00:00:00"

    prompts = []
    answers = iter(["42", "", "", "", "", "04/03/2025"])
    monkeypatch.setattr("builtins.input", lambda prompt: prompts.append(prompt) or next(answers))
    monkeypatch.setattr(cli, "api_get", lambda _: {
        "id": 42, "transaction_id": "entry:42", "type": "expense", "amount": -12,
        "description": "Old", "category": "Meal", "date": "2025-02-01T00:00:00",
    })
    seen = {}
    monkeypatch.setattr(cli, "api_put", lambda endpoint, json_data: seen.update(payload=json_data) or {"id": 42})
    cli.edit_transaction()
    assert "New date DD/MM/YYYY (01/02/2025): " in prompts
    assert seen["payload"] == {"date": "2025-03-04T00:00:00"}


def test_cli_rejects_dates_in_another_format(monkeypatch, capsys):
    cli = load_cli()
    cli.date_format = "MM/DD/YYYY"
    for text in ("2025-03-04", "31/12/2025", "02/30/2025"):
        try:
            cli.parse_date(text)
        except ValueError as exc:
            assert "MM/DD/YYYY" in str(exc)
        else:
            raise AssertionError(text)

    answers = iter(["42", "", "", "", "", "2025-03-04"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    monkeypatch.setattr(cli, "api_get", lambda _: {
        "id": 42, "transaction_id": "entry:42", "type": "expense", "amount": -12,
        "description": "Old", "category": "Meal", "date": "2025-02-01T00:00:00",
    })
    monkeypatch.setattr(cli, "api_put", lambda *_: (_ for _ in ()).throw(AssertionError("must not save")))
    cli.edit_transaction()
    assert "MM/DD/YYYY" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# End-to-end CLI flows against the in-process FastAPI app
# ---------------------------------------------------------------------------

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

    answers = iter(["Wallet", "SGD"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.create_piggybank()
    assert "created successfully" in capsys.readouterr().out

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


def test_cli_add_transaction_with_category_menu_and_types(monkeypatch, client, capsys):
    cli = make_inprocess_cli(monkeypatch, client)
    login_cli(monkeypatch, cli)
    pb = cli.api_post("/piggy-banks", json_data={"name": "Daily", "currency": "SGD"})
    pb_id = pb["id"]

    # Add expense while creating a new category 'Meal' inline
    answers = iter([str(pb_id), "7.6", "expense", "n", "Meal", "Red Ginger", "2026-11-19"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.add_transaction()
    out = capsys.readouterr().out
    assert "Added category: Meal" in out
    assert "Transaction recorded successfully" in out

    # Add income picking existing category by name (case-insensitive)
    cli.api_post("/categories", json_data={"name": "Salary"})
    answers = iter([str(pb_id), "20", "income", "salary", "Allowance", "2026-11-19"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.add_transaction()

    # Add bank transfer_out (positive input normalized to negative) and skip category
    answers = iter([str(pb_id), "5", "transfer_out", "", "Sent to friend", "2026-11-19"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.add_transaction()

    # Add bank transfer_in (negative input normalized to positive) picking category by number
    answers = iter([str(pb_id), "-10", "transfer_in", "1", "Refund", "2026-11-19"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.add_transaction()

    txs = cli.api_get(f"/piggy-banks/{pb_id}/transactions")
    by_desc = {tx["description"]: tx for tx in txs}
    assert by_desc["Red Ginger"]["amount"] == -7.6
    assert by_desc["Red Ginger"]["category"] == "Meal"
    assert by_desc["Allowance"]["amount"] == 20.0
    assert by_desc["Allowance"]["category"] == "Salary"
    assert by_desc["Sent to friend"]["amount"] == -5.0
    assert by_desc["Sent to friend"]["type"] == "transfer_out"
    assert by_desc["Refund"]["amount"] == 10.0
    assert by_desc["Refund"]["type"] == "transfer_in"

    bal = cli.api_get(f"/piggy-banks/{pb_id}/balance")
    assert bal["balance"] == 17.4


def test_cli_add_transaction_handles_invalid_inputs_gracefully(monkeypatch, client, capsys):
    cli = make_inprocess_cli(monkeypatch, client)
    login_cli(monkeypatch, cli)
    pb = cli.api_post("/piggy-banks", json_data={"name": "Daily", "currency": "SGD"})

    answers = iter([str(pb["id"]), "not-a-number"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.add_transaction()
    assert "Input Error" in capsys.readouterr().out
    assert cli.api_get(f"/piggy-banks/{pb['id']}/transactions") == []


def test_cli_list_transactions_respects_limit(monkeypatch, client, capsys):
    cli = make_inprocess_cli(monkeypatch, client)
    login_cli(monkeypatch, cli)
    pb = cli.api_post("/piggy-banks", json_data={"name": "Daily", "currency": "SGD"})
    pb_id = pb["id"]
    for idx in range(3):
        cli.api_post(
            f"/piggy-banks/{pb_id}/transactions",
            json_data={
                "amount": -(idx + 1),
                "type": "expense",
                "category": "Food",
                "description": f"Item {idx + 1}",
                "date": f"2026-11-0{idx + 1}T00:00:00",
            },
        )

    # Request only 2 most recent rows
    answers = iter([str(pb_id), "2"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.list_transactions()
    out = capsys.readouterr().out
    assert "Item 3" in out
    assert "Item 2" in out
    assert "Item 1" not in out
    assert "Showing 2 of 3 transactions." in out

    # Request all rows
    answers = iter([str(pb_id), "all"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.list_transactions()
    out = capsys.readouterr().out
    assert "Item 1" in out
    assert "Showing 3 of 3 transactions." in out


def test_cli_delete_transaction_normal_and_piggybank_transfer(monkeypatch, client, capsys):
    cli = make_inprocess_cli(monkeypatch, client)
    login_cli(monkeypatch, cli)
    pb_a = cli.api_post("/piggy-banks", json_data={"name": "BankA", "currency": "SGD"})
    pb_b = cli.api_post("/piggy-banks", json_data={"name": "BankB", "currency": "SGD"})

    tx = cli.api_post(
        f"/piggy-banks/{pb_a['id']}/transactions",
        json_data={"amount": -7.6, "type": "expense", "category": "Food", "description": "Red Ginger"},
    )

    # Cancel delete
    answers = iter([str(tx["id"]), "n"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.delete_transaction()
    assert "Delete cancelled." in capsys.readouterr().out
    assert len(cli.api_get(f"/piggy-banks/{pb_a['id']}/transactions")) == 1

    # Confirm delete
    answers = iter([str(tx["id"]), "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.delete_transaction()
    assert "Transaction deleted successfully" in capsys.readouterr().out
    assert cli.api_get(f"/piggy-banks/{pb_a['id']}/transactions") == []

    # PiggyBank transfer deletion removes both linked legs atomically
    transfer = cli.api_post(
        "/transfers",
        json_data={
            "source_piggy_bank_id": pb_a["id"],
            "target_piggy_bank_id": pb_b["id"],
            "amount": 15,
            "description": "Top up",
        },
    )
    answers = iter([str(transfer["entry_ids"][0]), "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.delete_transaction()
    out = capsys.readouterr().out
    assert "both linked transactions" in out
    assert "Transaction deleted successfully" in out
    assert cli.api_get(f"/piggy-banks/{pb_a['id']}/transactions") == []
    assert cli.api_get(f"/piggy-banks/{pb_b['id']}/transactions") == []


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
    cli_a = make_inprocess_cli(monkeypatch, client, email="alice@example.com")
    login_cli(monkeypatch, cli_a, email="alice@example.com")
    pb_a = cli_a.api_post("/piggy-banks", json_data={"name": "AliceBank", "currency": "NTD"})
    tx_a = cli_a.api_post(
        f"/piggy-banks/{pb_a['id']}/transactions",
        json_data={"amount": -100, "type": "expense", "description": "Private"},
    )

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


def test_cli_register_and_net_worth_conversion(monkeypatch, client, capsys):
    monkeypatch.delenv("PIGGYNEST_API_URL", raising=False)
    cli = load_cli()
    monkeypatch.setattr(cli, "is_local_server_running", lambda: False)
    monkeypatch.setattr(cli, "load_inprocess_client", lambda: client)

    answers = iter(["newbie", "newbie@example.com", "Password123!"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert cli.register() is True
    assert "registered" in capsys.readouterr().out

    login_cli(monkeypatch, cli, email="newbie@example.com")
    pb_ntd = cli.api_post("/piggy-banks", json_data={"name": "TW", "currency": "NTD"})
    pb_sgd = cli.api_post("/piggy-banks", json_data={"name": "SG", "currency": "SGD"})
    cli.api_post(f"/piggy-banks/{pb_ntd['id']}/transactions", json_data={"amount": 100, "type": "income", "description": "Init"})
    cli.api_post(f"/piggy-banks/{pb_sgd['id']}/transactions", json_data={"amount": 10, "type": "income", "description": "Init"})

    # Default rate for new user is 1 SGD = 24.00 NTD -> 100 + 10*24 = 340.00 NTD
    cli.list_piggybanks()
    out = capsys.readouterr().out
    assert "Total Net Worth (NTD): 340.00" in out


def test_cli_transfer_same_and_cross_currency_and_edit_counterpart(monkeypatch, client, capsys):
    cli = make_inprocess_cli(monkeypatch, client)
    login_cli(monkeypatch, cli)
    pb_sgd = cli.api_post("/piggy-banks", json_data={"name": "SG", "currency": "SGD"})
    pb_ntd = cli.api_post("/piggy-banks", json_data={"name": "TW", "currency": "NTD"})

    # Cross-currency transfer SG -> TW: send 10 SGD, receive 240 NTD
    answers = iter([str(pb_sgd["id"]), str(pb_ntd["id"]), "10", "240", "FX move", "2026-11-19"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.transfer_between_piggybanks()
    out = capsys.readouterr().out
    assert "Implied rate: 1 SGD = 24.0000 NTD" in out
    assert "Transfer recorded!" in out

    sg_txs = cli.api_get(f"/piggy-banks/{pb_sgd['id']}/transactions")
    tw_txs = cli.api_get(f"/piggy-banks/{pb_ntd['id']}/transactions")
    assert sg_txs[0]["amount"] == -10.0
    assert tw_txs[0]["amount"] == 240.0

    # Edit cross-currency transfer via CLI (update both leg amount and counterpart_amount)
    answers = iter([str(sg_txs[0]["id"]), "-12", "276", "Updated FX", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.edit_transaction()
    assert "Update successful" in capsys.readouterr().out

    sg_txs = cli.api_get(f"/piggy-banks/{pb_sgd['id']}/transactions")
    tw_txs = cli.api_get(f"/piggy-banks/{pb_ntd['id']}/transactions")
    assert sg_txs[0]["amount"] == -12.0
    assert tw_txs[0]["amount"] == 276.0


def test_cli_manage_categories_add_rename_delete(monkeypatch, client, capsys):
    cli = make_inprocess_cli(monkeypatch, client)
    login_cli(monkeypatch, cli)

    # Add
    answers = iter(["1", "Coffee"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.manage_categories()
    cats = cli.api_get("/categories")
    assert [c["name"] for c in cats] == ["Coffee"]
    cat_id = cats[0]["id"]

    # Rename
    answers = iter(["2", str(cat_id), "Drinks"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.manage_categories()
    assert [c["name"] for c in cli.api_get("/categories")] == ["Drinks"]

    # Delete
    answers = iter(["3", str(cat_id)])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.manage_categories()
    assert cli.api_get("/categories") == []


def test_cli_reports_excludes_piggybank_transfers_and_exports_charts(monkeypatch, client, capsys, tmp_path):
    cli = make_inprocess_cli(monkeypatch, client)
    login_cli(monkeypatch, cli)
    pb_a = cli.api_post("/piggy-banks", json_data={"name": "Cash", "currency": "NTD"})
    pb_b = cli.api_post("/piggy-banks", json_data={"name": "Bank", "currency": "NTD"})

    cli.api_post(
        f"/piggy-banks/{pb_a['id']}/transactions",
        json_data={"amount": 1000, "type": "income", "category": "Salary", "description": "Pay", "date": "2026-11-01T00:00:00"},
    )
    cli.api_post(
        f"/piggy-banks/{pb_a['id']}/transactions",
        json_data={"amount": -250, "type": "expense", "category": "Meal", "description": "Lunch", "date": "2026-11-05T00:00:00"},
    )
    # PiggyBank transfer of 300 should NOT count as income or spending in reports/cashflow
    cli.api_post(
        "/transfers",
        json_data={
            "source_piggy_bank_id": pb_a["id"],
            "target_piggy_bank_id": pb_b["id"],
            "amount": 300,
            "description": "Save",
            "date": "2026-11-10T00:00:00",
        },
    )

    # Monthly report across all banks
    answers = iter(["", "monthly", "", "", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.view_reports()
    out = capsys.readouterr().out
    assert "2026/11" in out
    assert "1000.00" in out
    assert "250.00" in out
    assert "+750.00" in out

    # Export all 3 PNG charts into tmp_path
    answers = iter(["", "all", "", "", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    paths = cli.export_charts(output_dir=str(tmp_path))
    assert len(paths) == 3
    names = sorted(Path(p).name for p in paths)
    assert names[0].startswith("balance_combined_")
    assert names[1].startswith("cashflow_combined_")
    assert names[2].startswith("categories_combined_")
    for p in paths:
        assert Path(p).exists()
        assert Path(p).stat().st_size > 1000


def test_cli_settings_preferences_rates_and_excel_backup_roundtrip(monkeypatch, client, capsys, tmp_path):
    cli = make_inprocess_cli(monkeypatch, client, email="src@example.com")
    login_cli(monkeypatch, cli, email="src@example.com")
    pb = cli.api_post("/piggy-banks", json_data={"name": "Travel", "currency": "SGD"})
    cli.api_post(
        f"/piggy-banks/{pb['id']}/transactions",
        json_data={"amount": -12.5, "type": "expense", "category": "Meal", "description": "Laksa", "date": "2026-11-19T00:00:00"},
    )

    # Update display preferences
    answers = iter(["2", "DD/MM/YYYY", "SGD", "50", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.settings_and_backup()
    assert cli.date_format == "DD/MM/YYYY"
    assert cli.display_currency == "SGD"
    assert cli.transactions_per_page == 50
    assert cli.net_worth_hidden is True

    # Update SGD -> NTD rate
    answers = iter(["3", "SGD", "25.5"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.settings_and_backup()
    assert "1 SGD = 25.5 NTD" in capsys.readouterr().out

    # Export Excel backup
    backup_file = tmp_path / "cli_backup.xlsx"
    answers = iter(["4", str(backup_file)])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.settings_and_backup()
    assert backup_file.exists() and backup_file.stat().st_size > 0

    # Import into a fresh user account
    cli2 = make_inprocess_cli(monkeypatch, client, email="dst@example.com")
    login_cli(monkeypatch, cli2, email="dst@example.com")
    answers = iter(["5", str(backup_file)])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli2.settings_and_backup()
    banks = cli2.api_get("/piggy-banks")
    assert [b["name"] for b in banks] == ["Travel"]
    txs = cli2.api_get(f"/piggy-banks/{banks[0]['id']}/transactions")
    assert len(txs) == 1 and txs[0]["description"] == "Laksa"
