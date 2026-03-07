# PiggyNest v2.0 🐷

A full-stack, comprehensive, categorized, and multi-currency personal finance bookkeeping application powered by FastAPI and React!

PiggyNest allows users to map their real-world Net Worth across various different independent "PiggyBanks".

### ✨ Core Features
- **Secure Authentication:** JWT-based user registration and login system.
- **Multi-Currency:** Support for major localized currencies (USD, EUR, GBP, JPY, NTD, SGD).
- **Inter-Bank Transfers:** Transfer static funds seamlessly between specific sub-accounts.
- **Categorization:** Tag your expenses and incomes with robust custom string attributes (Rent, Food, Salary).
- **Financial Analytics:** Auto-populated Recharts animations generating Pie charts predicting your Money Flow layout!

---

### 🖥️ Tech Stack
- **Backend**: Python 3.9+, FastAPI, SQLAlchemy, SQLite Database
- **Frontend**: TypeScript, React, Vite, TailwindCSS (Utility classes), Recharts
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
