# Historical transfer repair

Internal transfers need two entries with one shared `transaction_id`. External transfers have one entry with `type=transfer_out` or `type=transfer_in` and an individual `entry:<id>` transaction ID. Older `type=transfer` rows without a shared ID may be either kind.

Run from `backend/` against the configured database:

```bash
venv/bin/python repair_transfer_ids.py
```

The default run only reports how many uniquely matched pairs can be linked and lists unresolved entry IDs. Back up the database before applying repairs. Then run:

```bash
venv/bin/python repair_transfer_ids.py --apply
```

The program links pairs whose amount, date, bank names, categories, and descriptions uniquely agree. It does not guess unresolved rows. Review those entries in the database or Excel export. For a confirmed internal pair, pass the debit ID first and credit ID second:

```bash
venv/bin/python repair_transfer_ids.py --apply --pair 12 13
```

For a confirmed single transfer to or from an external account:

```bash
venv/bin/python repair_transfer_ids.py --apply --external 14
```

The program checks ownership, bank distinction, direction, amount, and date for a manually linked pair. An external row becomes `transfer_out` when negative and `transfer_in` when positive. It keeps its original row ID and amount. Run the read-only audit again to confirm that no unresolved IDs remain. Until classified, an old `type=transfer` row without a unique pair cannot be deleted and its bank cannot be deleted; those APIs return HTTP 409.
