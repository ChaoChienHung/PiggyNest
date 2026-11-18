"""Identify unambiguous transfer pairs created before shared IDs existed."""
from collections import defaultdict


def legacy_transfer_pairs(transactions, banks):
    names = {bank.id: bank.name for bank in banks}
    old = [tx for tx in transactions if tx.type == "transfer" and not tx.transfer_group_id]
    credits_by_amount_and_date = defaultdict(list)
    for tx in old:
        if tx.amount > 0 and tx.category == "Transfer In":
            credits_by_amount_and_date[(tx.amount, tx.date)].append(tx)
    candidates = {}
    for debit in old:
        if debit.amount >= 0 or debit.category != "Transfer Out":
            continue
        matches = [credit for credit in credits_by_amount_and_date[(-debit.amount, debit.date)] if (
            credit.piggy_bank_id != debit.piggy_bank_id
            and names.get(credit.piggy_bank_id) is not None
            and names.get(debit.piggy_bank_id) is not None
            and (debit.description or "").startswith(f"Transfer to {names[credit.piggy_bank_id]}: ")
            and (credit.description or "").startswith(f"Transfer from {names[debit.piggy_bank_id]}: ")
            and debit.description.split(": ", 1)[1] == credit.description.split(": ", 1)[1]
        )]
        if len(matches) == 1:
            candidates[debit.id] = matches[0].id
    credits = defaultdict(list)
    for debit_id, credit_id in candidates.items():
        credits[credit_id].append(debit_id)
    pairs = {}
    for debit_id, credit_id in candidates.items():
        if len(credits[credit_id]) == 1:
            pairs[debit_id] = credit_id
            pairs[credit_id] = debit_id
    return pairs
