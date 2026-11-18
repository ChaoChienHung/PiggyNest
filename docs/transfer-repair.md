# Historical transfer repair

PiggyBank transfers need two transactions with one shared `transaction_id`. Bank transfers have one transaction with `type=transfer_out` or `type=transfer_in` and an individual `entry:<id>` logical transaction ID. Older `type=transfer` transactions without a shared ID may be either kind.

Run from `backend/` against the configured database:

```bash
venv/bin/python repair_transfer_ids.py
```

The default run only reports how many uniquely matched pairs can be linked and lists unresolved transaction IDs. Back up the database before applying repairs. Then run:

```bash
venv/bin/python repair_transfer_ids.py --apply
```

The program links pairs whose amount, date, bank names, categories, and descriptions uniquely agree. It does not guess unresolved rows. Review those entries in the database or Excel export. For a confirmed internal pair, pass the debit ID first and credit ID second:

```bash
venv/bin/python repair_transfer_ids.py --apply --pair 12 13
```

For a confirmed single bank transfer to or from an account outside PiggyNest:

```bash
venv/bin/python repair_transfer_ids.py --apply --external 14
```

The program checks ownership, PiggyBank distinction, direction, amount, and date for a manually linked pair. A bank transfer becomes `transfer_out` when negative and `transfer_in` when positive. It keeps its original transaction ID and amount. Run the read-only audit again to confirm that no unresolved IDs remain. Until classified, an old `type=transfer` transaction without a unique pair cannot be edited or deleted and its PiggyBank cannot be deleted; those APIs return HTTP 409.
