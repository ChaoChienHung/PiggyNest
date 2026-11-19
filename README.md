# PiggyNest 🐷

PiggyNest is a personal finance app for tracking money across separate PiggyBanks, such as bank accounts, cash, and transit cards. It has a FastAPI backend, a React frontend, and a local SQLite database.

## Features

- **Accounts:** Register and sign in with email. With SMTP configured, users can receive a username reminder or a code to reset a forgotten password.
- **PiggyBanks and transactions:** Keep a balance for each PiggyBank and currency. Add, categorize, and edit transactions by ID in the browser or CLI.
- **Transfers:** Move money between owned PiggyBanks with two linked transactions, or record a transfer to or from an outside account with one transaction.
- **Reports:** Compare PiggyBanks in one display currency with fixed rates, view combined charts, and inspect daily, monthly, and yearly numeric summaries.
- **Backups:** Export and import Excel backups. Import adds new PiggyBanks; it does not merge independently edited copies of an existing PiggyBank.
- **Multiple locations:** Point browser and CLI clients at one shared backend to use the same ledger from different places.

See the [feature guide](docs/features.md) for the implementation areas and links to each feature's detailed behavior.

## Quick start

Start the backend in one terminal:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`, with interactive documentation at `/docs`. Its default database is `data/piggynest.db` at the repository root; `data/` is ignored by Git.

Start the frontend in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. For account recovery email, configure the backend using [`.env.example`](backend/.env.example) and the [recovery guide](docs/account-recovery.md). To connect from multiple locations, use the [shared backend configuration](docs/data-sync.md#shared-backend-configuration); a reachable backend must be deployed separately.

## CLI

Run the root CLI from the repository root using the backend virtual environment. It goes through the same FastAPI routes as the browser and can edit a transaction by its numeric ID. When no local server is running, it automatically loads the local FastAPI app in-process so you do not need to start `uvicorn` first; if the local server is already running, it connects over HTTP. Its database inspector reads only the local development database.

```bash
source backend/venv/bin/activate
python3 cli.py
```

Set `PIGGYNEST_API_URL` to use a shared backend. When pointing to a remote API, the CLI strictly uses HTTP and disables both local in-process fallback and the database inspector.

## Development test account

For local manual testing, register this disposable account in a fresh database if it is not already present:

- Username: `Bob`
- Email: `bob@piggynest.test`
- Password: `BobTest2026!`

Keep manual test data under Bob. Automated tests use a separate database; these credentials are for local development only.

## Terminology

Use these terms in issues, documentation, code reviews, and import discussions:

| Term | Meaning |
| --- | --- |
| **User account** | The person who signs in with an email and owns PiggyBanks, categories, and transactions. |
| **PiggyBank** | One balance-holding ledger with one currency. It can represent a bank account, cash, or another store of money. |
| **Transaction** | One stored row in one PiggyBank. Its numeric `id` is used for edit and delete requests; its signed amount changes that PiggyBank's balance. |
| **PiggyBank transfer** | Money moved between two PiggyBanks owned by the same user. It has a debit and a credit with one shared logical transaction ID. |
| **Bank transfer** | Money moved to or from an account outside PiggyNest. It has one transaction and no paired PiggyBank transaction. |
| **Logical transaction ID** | The API's `transaction_id`: `entry:<id>` for a standalone transaction, or a shared UUID for the two sides of a PiggyBank transfer. |
| **Type and category** | `type` determines transaction behavior; `category` is a user-facing label. A legacy category alone does not establish a transfer pair. |

See [architecture](docs/architecture.md#transaction-identity-and-transfers) for transaction rules and [transfer repair](docs/transfer-repair.md) for older records without shared IDs.

## Repository guide

This README is the shared entry point for users and agents. [`AGENTS.md`](AGENTS.md) holds agent-specific rules and checks; [`docs/`](docs/) holds feature details, system contracts, and design rationale. This map lists folders rather than individual files so it stays useful as the repository grows.

| Folder | Purpose |
| --- | --- |
| [`backend/`](backend/) | API, data model, migrations, import tools, and backend tests. |
| [`frontend/`](frontend/) | Browser interface, API client, and visual assets. |
| [`docs/`](docs/) | Feature guides, architecture, design decisions, and technology stack. |
| `data/` | Git-ignored local database and import reports. |

Start with the [feature guide](docs/features.md) to find the folders behind a workflow. For deeper context, see the [architecture](docs/architecture.md), [design decisions](docs/design-decisions.md), [technology stack](docs/tech-stack.md), and [backlog](docs/backlog.md).
