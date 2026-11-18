# PiggyNest 🐷

Engineering documentation: [architecture](docs/architecture.md), [technology stack](docs/tech-stack.md), [design decisions](docs/design-decisions.md), and [backlog](docs/backlog.md).

A full-stack, comprehensive, categorized, and multi-currency personal finance bookkeeping application powered by FastAPI and React!

PiggyNest allows users to map their real-world Net Worth across various different independent "PiggyBanks".

### ✨ Core Features
- **Breathtaking Pink & Gold Theme 🐷:** Redesigned with a beautiful drifting radial background, bouncy transitions, custom form fields, and rounded cards.
- **Split-Screen Interactive Login/Register 💰:** A responsive split-screen layout featuring a gently floating, pure SVG-designed cute piggy bank catching falling golden coins in 3D-like CSS animations.
- **Secure Authentication:** JWT-based user registration and login system.
- **Multi-Currency:** Support for major localized currencies (USD, EUR, GBP, JPY, NTD, SGD).
- **Inter-Bank Transfers:** Transfer static funds seamlessly between specific sub-accounts.
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
2. Issue HTTP requests natively to pull PiggyBank arrays and format your transactions.
3. Access an exclusive "DB Inspector" mode that natively fetches the `sqlite_master` map table and dumps rows from `.db` directly to console!
# Excel backups

In **Settings → Backup your Piggy Banks**, export one `.xlsx` file containing
`Piggy Banks`, `Transactions`, and `Categories` sheets. Import accepts the same format and adds
its banks and transactions to the signed-in account in one database transaction.
An existing bank name rejects the entire import, so importing the same file twice
does not duplicate entries. The import limit is 10 MB and 100,000 rows per sheet.

Both rows of a new internal transfer carry the same logical `transaction_id`; their
`entry_id` values identify the individual debit and credit records. The exporter also
pairs older transfers when their date, amount, bank names and descriptions identify
a unique match. Ambiguous older transfers remain separate rows, with their
original balances preserved. Deleting a linked internal transfer deletes both sides.
An external transfer is one row with its own ID. Classify unresolved older transfers
with the [repair program](docs/transfer-repair.md) before importing their backup.

Install backend dependencies from `backend/requirements.txt` before starting the
API; the workbook feature uses `openpyxl`.

## Development test account

For local manual feature testing, use **Bob** in the development database
`backend/data/piggynest.db` (with the API started from `backend/`):

- Email / login: `bob@piggynest.test`
- Password: `BobTest2026!`

Bob is a disposable test account. Keep manual test data under Bob; automated
tests use a separate database. These credentials are for local development only.
The database is local and ignored by Git. A fresh clone starts with an empty
database; register Bob through the app before using this account.
