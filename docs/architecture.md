# Architecture

## Running application

The browser runs a React single-page application. `frontend/src/api/` wraps HTTP requests to the versioned FastAPI routes in `backend/app/api/v1/`. Authentication uses a bearer token. Each query for banks, transactions, categories, backup data, or statistics is scoped to the authenticated user.

The API uses SQLAlchemy sessions against SQLite by default. `backend/app/models/` defines the persisted schema, `backend/app/schemas/` defines request and response shapes, and `backend/app/domain/` holds reusable rules. Some endpoint modules still perform database orchestration directly; move a workflow into a service when it has multiple callers or needs more complex invariants. `backend/app/db/repositories/` currently covers only some resources. Avoid adding repository wrappers that merely repeat a one-line query.

`backend/app/domain/transactions.py` and `backend/app/domain/reports.py` are older CSV/pandas bookkeeping code; the FastAPI app does not route through them. `cli.py` is a separate development tool. Keep these paths distinct until there is a deliberate migration or removal.

## Transaction identity and transfers

Every transaction has a numeric `transactions.id`. A standalone transaction's logical `transaction_id` is `entry:<id>`. A **PiggyBank transfer** between two owned PiggyBanks creates **two** transactions in one database commit: a negative source transaction and a positive target transaction. Both have `type=transfer` and the same UUID in `transfer_group_id`, exposed as `transaction_id`. The transfer API also returns both numeric transaction IDs.

A **bank transfer** has one transaction because the other account is outside PiggyNest. `type=transfer_out` uses a negative amount; `type=transfer_in` uses a positive amount. Its `transfer_group_id` is null, and it is created, edited, or deleted by its numeric transaction ID. Bank transfers out count as spending and bank transfers in count as income in the current statistics policy; users can choose a category to describe their purpose.

Create a PiggyBank transfer only through `POST /api/v1/transfers`. The ordinary transaction endpoint rejects `type=transfer` while accepting `transfer_out` and `transfer_in`. Fetch or edit any owned transaction with `GET` or `PUT /api/v1/transactions/{id}`. For a PiggyBank transfer, editing the signed amount, note, or date updates both transactions in one commit; the transfer direction and directional categories are fixed. Delete either transaction through `DELETE /api/v1/transactions/{id}` and the backend deletes both in the same commit. Deleting either PiggyBank also removes both transactions. PiggyBank transfers require the same currency; exchange rates are not modeled.

Older `type=transfer` transactions may lack `transfer_group_id`; some are historical PiggyBank transfers and others may represent bank transfers. `domain/transfer_links.py` identifies PiggyBank pairs only when amount, timestamp, source and target PiggyBank names, categories, and description agree uniquely. The [repair program](transfer-repair.md) audits them and can persist shared IDs. For an unresolved transaction, a person can explicitly link a reviewed debit and credit or mark it as a bank transfer. Until classified, editing or deleting that transaction, or deleting its PiggyBank, returns HTTP 409. Excel import rejects unclassified `type=transfer` transactions; run the repair before exporting data that will be imported elsewhere.

Balances sum signed amounts within a PiggyBank. Global income and spending statistics exclude PiggyBank transfers, since moving funds between owned PiggyBanks does not change overall income or expense.

## Persistence and backup

The default database URL points to the repository's Git-ignored `data/piggynest.db`, independent of the API process's working directory. The API creates it on first startup. A fresh clone needs a newly registered test account. Automated tests override the URL and use an isolated SQLite database.

Excel export has bank, transaction, and category sheets. Import validates all rows, remaps IDs, then commits the account import atomically. Its `entry_id` records a row's original ID; `transaction_id` links the two sides of a transfer. An imported account receives fresh database IDs.

`app.main` currently calls `create_all` and adds `transfer_group_id` with an inline schema change. This handles the current local schema but is not a general migration system. Use versioned migrations before production schema changes. SQLite `Float` is also unsuitable for exact financial arithmetic; migrate amounts to integer minor units or fixed decimal with a documented conversion plan.
