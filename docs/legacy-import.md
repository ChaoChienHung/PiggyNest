# Ludwig legacy CSV resolution

The one-time importer in `backend/import_legacy_bookkeeping.py` reads the old per-bank CSV files, creates Ludwig's PiggyBanks, imports unambiguous rows, and writes a private pending report under Git-ignored `data/`. The source CSV's `Transaction ID` restarts by file; identify a source entry with its bank, filename, and old ID. PiggyNest assigns new numeric transaction IDs.

`backend/resolve_legacy_bookkeeping.py` links unique same-day, equal-amount internal pairs. `backend/apply_legacy_rules.py` applies the rules confirmed during review. Run either without `--apply` to audit first. The scripts check the current ledger and local reports before writing, commit related ledger changes together, and refuse a duplicate run. Keep the source CSVs and generated reports private; do not commit them or the database.

## Confirmed classification rules

- Any description containing `Mother` is a one-entry **bank transfer**, with direction determined by its signed amount.
- A description naming another PiggyBank identifies an internal **PiggyBank transfer**. `Ludwig` means `LudwigTaiwan` for NTD and `LudwigSingapore` for SGD.
- `Withdrawal` and `Withdraw` default to an internal PiggyBank transfer to `LudwigTaiwan` or `LudwigSingapore` by currency, unless a specific other PiggyBank is named.
- If a confirmed internal transfer has no source-row opposite leg, create a synthetic opposite entry with the same principal and one shared transfer UUID. The target PiggyBank balance changes accordingly.
- Where a source debit contains a known fee, split it into an equal-principal transfer pair and a separate `Bank Fee` expense. This preserves the source PiggyBank's original total.
- The two equal TaishinBank withdrawals dated 2024-12-17 and the LudwigTaiwan credit dated 2024-12-10 are three distinct transfers; each receives its own synthetic opposite leg. This was chosen because the old source IDs and dates do not identify a unique pair.
- Six otherwise unspecified legacy `Transfer` rows are internal transfers with `LudwigTaiwan` as the NTD counterparty. Three ChangHwaBank debits follow the confirmed five-dollar fee pattern and are split into principal plus fee.

All 1,102 source rows are now represented in the local ledger and the pending report is empty. The 96 internal transfer groups each have two opposite, equal minor-unit amounts. Synthetic legs and fee expenses add ledger rows beyond the source row count. Explicitly named destinations take precedence over a coincidental same-day amount match; this avoids joining an `Ezlink` debit to a `LudwigSingapore` credit that names `UnitedOverseasBank`.

Known sub-cent Float residue in old ChungHwaPost NTD rows is normalized to whole NTD before import. The local float-correction audit lists existing rows corrected during the storage migration. The normal API and Excel importer require cent precision.
