# Feature guide

Use the [repository guide](../README.md#repository-guide) for each folder's overall purpose. This page shows where a feature is implemented; [architecture](architecture.md) holds the detailed contracts and [design decisions](design-decisions.md) explains why they exist.

## Accounts and sign-in

Users register and sign in through the browser. The API authenticates requests and scopes PiggyBanks, categories, transactions, and backups to the signed-in user.

The sign-in page also offers username reminders and email-code password resets. See [account recovery](account-recovery.md) for the flow, mail configuration, and security limits.

Look in [`frontend/`](../frontend/) for the screens and API calls, and [`backend/`](../backend/) for authentication, authorization, and tests.

## PiggyBanks and transactions

Each PiggyBank has one currency and a balance calculated from its signed transactions. Users can create, view, edit, and delete a transaction by its numeric ID. The root `cli.py` offers the same ID-based edit through the API.

Look in [`frontend/`](../frontend/) for the ledger and edit form, and [`backend/`](../backend/) for the transaction routes, data model, and tests. See [transaction identity](architecture.md#transaction-identity-and-transfers) for the shared logical ID used by PiggyBank transfers.

## Transfers

A PiggyBank transfer moves money between two owned PiggyBanks and keeps its two transactions linked. A bank transfer moves money to or from an account outside PiggyNest and has one transaction. The [terminology](../README.md#terminology) and [transaction contract](architecture.md#transaction-identity-and-transfers) define both cases. Historical records that need classification use the [transfer repair guide](transfer-repair.md).

Look in [`frontend/`](../frontend/) for the transfer form and ledger actions, and [`backend/`](../backend/) for pair creation, atomic edits and deletion, repair, and tests.

## Backups and legacy imports

Users can export and import an Excel backup from the browser. A separate backend import tool reads legacy CSV files, imports clear transactions, and leaves possible PiggyBank transfers in a local review report. See [persistence and backup](architecture.md#persistence-and-backup) and [transfer repair](transfer-repair.md).

Excel import assigns new local numeric IDs. It does not merge two independently edited copies of the same PiggyBank. See [backup identity and future synchronization](data-sync.md).

Look in [`frontend/`](../frontend/) for backup controls, [`backend/`](../backend/) for validation and import logic, and `data/` for the local database and review reports. The `data/` directory is ignored by Git.

## Statistics and reports

The browser displays balances and category charts from the API. PiggyBank transfers are excluded from global income and spending totals; bank transfers follow their signed direction.

Look in [`frontend/`](../frontend/) for charts and report views, and [`backend/`](../backend/) for calculations and tests.
