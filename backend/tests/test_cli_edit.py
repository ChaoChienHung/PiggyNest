import importlib.util
from pathlib import Path


def load_cli():
    path = Path(__file__).resolve().parents[2] / "cli.py"
    spec = importlib.util.spec_from_file_location("piggynest_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_edits_normal_transaction_by_id(monkeypatch):
    cli = load_cli()
    answers = iter(["42", "-18", "expense", "New note", "Transport", "2025-03-01"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    seen = {}
    def get(endpoint):
        seen["get"] = endpoint
        return {"id": 42, "transaction_id": "entry:42", "type": "expense",
                "amount": -12, "description": "Old", "category": "Meal", "date": "2025-02-01T00:00:00"}
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


def test_remote_cli_does_not_inspect_unrelated_local_database(monkeypatch, capsys):
    monkeypatch.setenv("PIGGYNEST_API_URL", "https://piggynest.example/api/v1/")
    cli = load_cli()
    assert cli.BASE_URL == "https://piggynest.example/api/v1"
    cli.inspect_db()
    assert "local-only" in capsys.readouterr().out
