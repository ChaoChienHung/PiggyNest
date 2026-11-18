# PiggyNest 🐷

A full-stack, comprehensive, categorized, and multi-currency personal finance bookkeeping application powered by FastAPI and React!

PiggyNest allows users to map their real-world Net Worth across various different independent "PiggyBanks".

## Terminology

Use these terms in issues, documentation, code reviews, and migration discussions:

| Term | Meaning in PiggyNest |
| --- | --- |
| **User account** | The person who logs in. A user owns PiggyBanks, categories, and transactions. Do not use “account” alone when it could mean either the user or a PiggyBank. |
| **PiggyBank** | One balance-holding ledger owned by a user. It may represent a bank account, cash, or a transit card; it is not necessarily a real bank. Each PiggyBank has one currency. |
| **Transaction** | One stored row in one PiggyBank, identified by its numeric `id`. Its signed `amount` changes that PiggyBank's balance. Use this word for every row, including both sides of a PiggyBank transfer. |
| **Logical transaction ID** | The API's `transaction_id`. A standalone transaction uses `entry:<id>`; the two transactions in a PiggyBank transfer share one UUID. Use a transaction's numeric `id` for API edit/delete requests. |
| **PiggyBank transfer** | Money moved between two PiggyBanks owned by the same user, regardless of whether either represents a real bank. It has a debit and a credit with different transaction IDs and one shared logical transaction ID. It is excluded from overall income and spending. The API stores both rows with `type=transfer`. |
| **Bank transfer** | Money moved to or from an account outside PiggyNest, such as another person's account. It has one transaction: `transfer_out` is negative, `transfer_in` is positive. There is no paired PiggyBank transaction. |
| **Type vs category** | `type` controls transaction behavior and statistics; `category` is a user-facing label. A legacy category such as `Withdrawal` or `Transfer` alone does not prove whether two transactions form a PiggyBank transfer. |
| **Balance and currency** | The current balance is calculated from the signed entries in one PiggyBank. Balances in different currencies are kept separate; the app does not convert between them. |
| **Legacy source ID** | An old CSV `Transaction ID` may restart each year and is only meaningful with its PiggyBank and source file. It is not the new database transaction ID and cannot establish a transfer pair by itself. |
| **Legacy source Balance** | The old CSV `Balance` is a running total that restarts by file/year. PiggyNest calculates its own balance from imported amounts instead of storing that old column. |

During legacy CSV imports, transactions whose transfer relationship is unclear are held for review instead of being added as ordinary income or spending. Their source details are kept in a local, Git-ignored report. The full data rules are in [Architecture](docs/architecture.md).

## Repository guide

This README is the shared entry point for users and agents: terminology, setup, and a stable map of the repository. `AGENTS.md` contains only agent-specific rules and verification steps. `docs/` explains features, system contracts, design decisions, and the technology stack. Keep this map at folder level so ordinary file changes do not require updates.

| Folder | Purpose |
| --- | --- |
| [`backend/`](backend/) | API, data model, migrations, import tools, and backend tests. |
| [`frontend/`](frontend/) | Browser interface, API client, and visual assets. |
| [`docs/`](docs/) | Feature guides, architecture, design rationale, and technology stack. |
| `data/` | Local database, backups, and import reports. This entire folder is ignored by Git. |

Start with [feature guides](docs/features.md) to see which folders implement a workflow. For deeper context, read [architecture](docs/architecture.md), [design decisions](docs/design-decisions.md), [technology stack](docs/tech-stack.md), [account recovery](docs/account-recovery.md), [data synchronization](docs/data-sync.md), or [current work](docs/backlog.md). Add a feature guide when a workflow spans folders, and link it back to this map instead of copying the folder descriptions.

### ✨ Core Features
- **Breathtaking Pink & Gold Theme 🐷:** Redesigned with a beautiful drifting radial background, bouncy transitions, custom form fields, and rounded cards.
- **Split-Screen Interactive Login/Register 💰:** A responsive split-screen layout featuring a gently floating, pure SVG-designed cute piggy bank catching falling golden coins in 3D-like CSS animations.
- **Secure Authentication:** JWT-based user registration and login system.
- **Multi-Currency:** Support for major localized currencies (USD, EUR, GBP, JPY, NTD, SGD).
- **PiggyBank Transfers:** Move funds between owned PiggyBanks while keeping both transactions linked.
- **Categorization:** Tag your expenses and incomes with robust custom string attributes (Rent, Food, Salary).
- **Cohesive Pastel Charts 📊:** Financial analytics using Recharts featuring soft tooltips, bouncy bars, and custom pie chart category segments styled with the cute pastel color tokens.

---

### 🖥️ Tech Stack
- **Backend**: Python 3.9+, FastAPI, SQLAlchemy, SQLite Database
- **Frontend**: TypeScript, React, Vite, Custom Cute CSS Design System, Recharts
- **Tooling**: Node.js, pip


---

### 🚀 Getting Started

#### 1. Booting the Backend (API Server)
PiggyNest runs a lightweight ASGI web server mapping models natively to a local `sqlite3` file.

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
*The API will be live at `http://127.0.0.1:8000`*
*(View the interactive Swagger API documentation at `/docs`)*

#### 2. Booting the Frontend (React App)
```bash
cd frontend
npm install
npm run dev
```
*The breathtaking UI will launch on `http://localhost:5173`*

To use the same ledger from two locations, run one reachable backend and configure both frontends with `VITE_API_BASE_URL` and CLIs with `PIGGYNEST_API_URL`. See [shared backend configuration](docs/data-sync.md#shared-backend-configuration). Excel backup is for export and restore; it does not merge two independently edited databases.

---

### 🛠️ Interactive Developer CLI

PiggyNest ships with a fully autonomous diagnostic root CLI script allowing immediate, raw, and unbridled interaction with the backend and the actual SQLite Database schemas exactly as they reflect on disk.

#### Launching the CLI
Ensure your `backend/venv` virtual environment is universally activated (so that the `requests` HTTP wrapper library is present in your PATH).
```bash
source backend/venv/bin/activate
python3 cli.py
```

The script will launch a terminal interface:
1. Provide an authenticated Email and Password payload (OAuth2 standard).
2. Issue HTTP requests to view PiggyBanks and edit a transaction by its numeric ID, including amount, category, note, and date. Editing a PiggyBank transfer updates both transactions.
3. Access an exclusive "DB Inspector" mode that natively fetches the `sqlite_master` map table and dumps rows from `.db` directly to console!
# Excel backups

In **Settings → Backup your Piggy Banks**, export one `.xlsx` file containing
`Piggy Banks`, `Transactions`, and `Categories` sheets. Import accepts the same format and adds
its banks and transactions to the signed-in account in one database transaction.
An existing bank name rejects the entire import, so importing the same file twice
does not duplicate entries. The import limit is 10 MB and 100,000 rows per sheet.

Both transactions of a new PiggyBank transfer carry the same logical `transaction_id`; their
`entry_id` values identify the individual debit and credit records in an Excel backup. The exporter also
pairs older transfers when their date, amount, bank names and descriptions identify
a unique match. Ambiguous older transfers remain separate rows, with their
original balances preserved. Deleting a linked PiggyBank transfer deletes both sides.
A bank transfer is one transaction with its own ID. Classify unresolved older transfers
with the [repair program](docs/transfer-repair.md) before importing their backup.

Install backend dependencies from `backend/requirements.txt` before starting the
API; the workbook feature uses `openpyxl`.

## Development test account

For local manual feature testing, use **Bob** in the development database
`data/piggynest.db`:

- Email / login: `bob@piggynest.test`
- Password: `BobTest2026!`

Bob is a disposable test account. Keep manual test data under Bob; automated
tests use a separate database. These credentials are for local development only.
The database is local and ignored by Git. A fresh clone starts with an empty
database; register Bob through the app before using this account.
