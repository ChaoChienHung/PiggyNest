from io import BytesIO

from openpyxl import load_workbook
from app.models.transaction import Transaction


def headers_for(client, username):
    email = f"{username}@example.com"
    assert client.post("/api/v1/auth/register", json={
        "username": username, "email": email, "password": "password"
    }).status_code == 200
    login = client.post("/api/v1/auth/login", data={"username": email, "password": "password"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def upload(client, headers, data):
    return client.post("/api/v1/backup/import", headers=headers, files={
        "file": ("backup.xlsx", data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    })


def test_export_import_round_trip_and_transfer_pair(client):
    source = headers_for(client, "backup_source")
    target = headers_for(client, "backup_target")
    first = client.post("/api/v1/piggy-banks", headers=source, json={"name": "Savings", "currency": "SGD"}).json()["id"]
    second = client.post("/api/v1/piggy-banks", headers=source, json={"name": "Travel", "currency": "USD"}).json()["id"]
    assert client.post("/api/v1/categories", headers=source, json={"name": "Salary"}).status_code == 201
    client.post(f"/api/v1/piggy-banks/{first}/transactions", headers=source, json={
        "amount": 150, "type": "income", "description": "=not a formula", "category": "Salary"
    })
    transfer = client.post("/api/v1/transfers", headers=source, json={
        "source_piggy_bank_id": first, "target_piggy_bank_id": second, "amount": 40,
        "description": "trip",
    })
    assert transfer.status_code == 200

    exported = client.get("/api/v1/backup/export", headers=source)
    assert exported.status_code == 200
    workbook = load_workbook(BytesIO(exported.content), data_only=False)
    assert workbook.sheetnames == ["Piggy Banks", "Transactions", "Categories"]
    rows = list(workbook["Transactions"].values)[1:]
    assert len(rows) == 3
    assert rows[1][0] != rows[2][0]
    assert rows[0][5] == "=not a formula"
    assert workbook["Transactions"]["F2"].data_type == "s"
    assert rows[1][7] == rows[2][7] and rows[1][7]

    imported = upload(client, target, exported.content)
    assert imported.status_code == 200, imported.text
    assert imported.json() == {"piggy_banks_imported": 2, "transactions_imported": 3, "categories_imported": 1}
    assert [item["name"] for item in client.get("/api/v1/categories", headers=target).json()] == ["Salary"]
    banks = {bank["name"]: bank for bank in client.get("/api/v1/piggy-banks", headers=target).json()}
    assert {name: bank["currency"] for name, bank in banks.items()} == {"Savings": "SGD", "Travel": "USD"}
    assert client.get(f"/api/v1/piggy-banks/{banks['Savings']['id']}/balance", headers=target).json()["balance"] == 110
    assert client.get(f"/api/v1/piggy-banks/{banks['Travel']['id']}/balance", headers=target).json()["balance"] == 40
    imported_legs = [
        tx for bank in banks.values()
        for tx in client.get(f"/api/v1/piggy-banks/{bank['id']}/transactions", headers=target).json()
        if tx["type"] == "transfer"
    ]
    assert len(imported_legs) == 2
    assert imported_legs[0]["id"] != imported_legs[1]["id"]
    assert imported_legs[0]["transaction_id"] == imported_legs[1]["transaction_id"]

    # Import is add-only and rejects the whole file on a name collision.
    duplicate = upload(client, target, exported.content)
    assert duplicate.status_code == 400
    assert len(client.get("/api/v1/piggy-banks", headers=target).json()) == 2

    # Deleting either linked leg removes both sides of the transfer.
    assert client.delete(f"/api/v1/transactions/{imported_legs[0]['id']}", headers=target).status_code == 200
    assert client.get(f"/api/v1/piggy-banks/{banks['Savings']['id']}/balance", headers=target).json()["balance"] == 150
    assert client.get(f"/api/v1/piggy-banks/{banks['Travel']['id']}/balance", headers=target).json()["balance"] == 0


def test_import_rejects_broken_transfer_atomically(client):
    source = headers_for(client, "broken_source")
    target = headers_for(client, "broken_target")
    a = client.post("/api/v1/piggy-banks", headers=source, json={"name": "A"}).json()["id"]
    b = client.post("/api/v1/piggy-banks", headers=source, json={"name": "B"}).json()["id"]
    client.post("/api/v1/transfers", headers=source, json={
        "source_piggy_bank_id": a, "target_piggy_bank_id": b, "amount": 12,
    })
    workbook = load_workbook(BytesIO(client.get("/api/v1/backup/export", headers=source).content))
    workbook["Transactions"]["C3"] = 13
    output = BytesIO()
    workbook.save(output)
    result = upload(client, target, output.getvalue())
    assert result.status_code == 400
    assert client.get("/api/v1/piggy-banks", headers=target).json() == []


def test_export_pairs_unambiguous_older_transfers(client, db):
    source = headers_for(client, "older_source")
    a = client.post("/api/v1/piggy-banks", headers=source, json={"name": "Old_A"}).json()["id"]
    b = client.post("/api/v1/piggy-banks", headers=source, json={"name": "Old_B"}).json()["id"]
    client.post("/api/v1/transfers", headers=source, json={
        "source_piggy_bank_id": a, "target_piggy_bank_id": b,
        "amount": 25, "description": "historical",
    })
    db.query(Transaction).filter(Transaction.piggy_bank_id.in_([a, b])).update(
        {Transaction.transfer_group_id: None}, synchronize_session=False
    )
    db.commit()
    workbook = load_workbook(BytesIO(client.get("/api/v1/backup/export", headers=source).content))
    rows = list(workbook["Transactions"].values)[1:]
    assert rows[0][7] and rows[0][7] == rows[1][7]
