from io import BytesIO

from openpyxl import load_workbook

from app.domain.category_names import canonical_category, consolidate_categories
from app.models.category import Category
from app.models.transaction import Transaction
from tests.test_backup import headers_for, upload


def test_canonical_category_maps_only_old_spellings():
    assert canonical_category("Other") == "Others"
    assert canonical_category("transfer") == "Others"
    assert canonical_category("Withdraw") == "Withdrawals"
    assert canonical_category("Withdrawal") == "Withdrawals"
    assert canonical_category("Transfer In") == "Transfer In"
    assert canonical_category("Meal") == "Meal"
    assert canonical_category(None) is None


def test_bank_transfer_and_category_api_use_canonical_names(client):
    headers = headers_for(client, "canonical_api")
    bank = client.post("/api/v1/piggy-banks", headers=headers, json={"name": "Main"}).json()["id"]
    created = client.post(f"/api/v1/piggy-banks/{bank}/transactions", headers=headers, json={
        "type": "transfer_out", "amount": -20, "category": "Transfer", "description": "Rent",
    })
    assert created.status_code == 200, created.text
    assert created.json()["category"] == "Others"
    edited = client.put(f"/api/v1/transactions/{created.json()['id']}", headers=headers,
                        json={"category": "Withdraw"})
    assert edited.json()["category"] == "Withdrawals"

    assert client.post("/api/v1/categories", headers=headers, json={"name": "Others"}).status_code == 201
    assert client.post("/api/v1/categories", headers=headers, json={"name": "Other"}).status_code == 400
    meal = client.post("/api/v1/categories", headers=headers, json={"name": "Meal"}).json()
    renamed = client.put(f"/api/v1/categories/{meal['id']}", headers=headers,
                         json={"name": "Meal", "new_name": "Other"})
    assert renamed.status_code == 400


def test_piggybank_transfer_keeps_directional_labels(client):
    headers = headers_for(client, "canonical_pb_transfer")
    a = client.post("/api/v1/piggy-banks", headers=headers, json={"name": "PB_A"}).json()["id"]
    b = client.post("/api/v1/piggy-banks", headers=headers, json={"name": "PB_B"}).json()["id"]
    assert client.post("/api/v1/transfers", headers=headers, json={
        "source_piggy_bank_id": a, "target_piggy_bank_id": b, "amount": 5,
    }).status_code == 200
    legs = client.get(f"/api/v1/piggy-banks/{a}/transactions", headers=headers).json()
    legs += client.get(f"/api/v1/piggy-banks/{b}/transactions", headers=headers).json()
    assert sorted(leg["category"] for leg in legs) == ["Transfer In", "Transfer Out"]


def test_import_maps_old_category_spellings(client):
    source = headers_for(client, "canonical_import_source")
    target = headers_for(client, "canonical_import_target")
    a = client.post("/api/v1/piggy-banks", headers=source, json={"name": "Import_A"}).json()["id"]
    b = client.post("/api/v1/piggy-banks", headers=source, json={"name": "Import_B"}).json()["id"]
    client.post(f"/api/v1/piggy-banks/{a}/transactions", headers=source, json={
        "type": "transfer_in", "amount": 30, "category": "Others", "description": "Refund",
    })
    client.post("/api/v1/transfers", headers=source, json={
        "source_piggy_bank_id": a, "target_piggy_bank_id": b, "amount": 10,
    })
    client.post("/api/v1/categories", headers=source, json={"name": "Others"})
    workbook = load_workbook(BytesIO(client.get("/api/v1/backup/export", headers=source).content))
    # Simulate an older backup that still uses retired spellings.
    workbook["Transactions"]["E2"] = "Transfer"
    workbook["Categories"].append(("Other",))
    workbook["Categories"].append(("Withdraw",))
    output = BytesIO()
    workbook.save(output)

    result = upload(client, target, output.getvalue())
    assert result.status_code == 200, result.text
    names = [c["name"] for c in client.get("/api/v1/categories", headers=target).json()]
    assert names == ["Others", "Withdrawals"]
    banks = client.get("/api/v1/piggy-banks", headers=target).json()
    entries = [tx for bank in banks
               for tx in client.get(f"/api/v1/piggy-banks/{bank['id']}/transactions", headers=target).json()]
    bank_transfer = next(tx for tx in entries if tx["type"] == "transfer_in")
    assert bank_transfer["category"] == "Others"
    pair = [tx for tx in entries if tx["type"] == "transfer"]
    assert len(pair) == 2 and pair[0]["transaction_id"] == pair[1]["transaction_id"]
    assert sorted(tx["category"] for tx in pair) == ["Transfer In", "Transfer Out"]


def test_consolidation_rewrites_only_categories_and_is_idempotent(client, db):
    headers = headers_for(client, "canonical_consolidate")
    a = client.post("/api/v1/piggy-banks", headers=headers, json={"name": "Old_Main"}).json()["id"]
    b = client.post("/api/v1/piggy-banks", headers=headers, json={"name": "Old_Other"}).json()["id"]
    bank_transfer = client.post(f"/api/v1/piggy-banks/{a}/transactions", headers=headers, json={
        "type": "transfer_out", "amount": -7, "description": "Mother",
    }).json()["id"]
    client.post("/api/v1/transfers", headers=headers, json={
        "source_piggy_bank_id": a, "target_piggy_bank_id": b, "amount": 3,
    })
    owner = client.get("/api/v1/piggy-banks", headers=headers).json()[0]["user_id"]
    # Seed legacy spellings directly, as older data and imports did.
    db.query(Transaction).filter(Transaction.id == bank_transfer).update({Transaction.category: "Withdrawal"})
    db.add_all([Category(user_id=owner, name=n) for n in ("Other", "Others", "Withdraw", "Withdrawal", "Transfer")])
    db.commit()
    before = {tx.id: (tx.amount_minor, tx.date, tx.type, tx.description, tx.transfer_group_id)
              for tx in db.query(Transaction).filter(Transaction.piggy_bank_id.in_([a, b]))}

    changes = consolidate_categories(db)
    db.commit()
    assert [(c["before"], c["after"]) for c in changes["transactions"]] == [("Withdrawal", "Withdrawals")]
    names = sorted(c.name for c in db.query(Category).filter(Category.user_id == owner))
    assert names == ["Others", "Withdrawals"]
    after = {tx.id: (tx.amount_minor, tx.date, tx.type, tx.description, tx.transfer_group_id)
             for tx in db.query(Transaction).filter(Transaction.piggy_bank_id.in_([a, b]))}
    assert after == before
    transfer_labels = sorted(tx.category for tx in db.query(Transaction).filter(Transaction.type == "transfer",
                                                                               Transaction.piggy_bank_id.in_([a, b])))
    assert transfer_labels == ["Transfer In", "Transfer Out"]

    again = consolidate_categories(db)
    assert again == {"transactions": [], "categories": []}
