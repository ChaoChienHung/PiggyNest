# 🧾 PiggyNest — Personal Finance App

This project is a personal bookkeeping application designed for both desktop and mobile use.  
Originally created for practice and experimentation, it also serves as a playground for adopting new technologies and improving full-stack development skills.

---

## 🧱 Project Architecture

```
 Web   -----\
       API Request → Server → Database
Mobile -----/
```

### Technology Stack

| Layer       | Technology                               | Purpose                                   |
|-------------|------------------------------------------|-------------------------------------------|
| Web Client  | Next.js, React                           | Browser-based UI                          |
| Mobile App  | Flutter                                  | Cross-platform mobile UI                  |
| Server API  | Python (FastAPI)                         | Business logic, validation, data routing  |
| Database    | SQLite, PostgreSQL, MySQL, MariaDB       | Persistent storage                        |

---

## 📌 Project Features

This project is a personal finance tracking application featuring a React-based frontend (or pure HTML/CSS/Tailwind), a FastAPI backend, and SQLite as the storage layer.  
The architecture balances simplicity, flexibility, and speed—ideal for personal or small-scale use.

- ✅ Query and review transaction history  
- ✅ Display charts (pie charts & bar charts) using Chart.js / Recharts  
- ✅ Deployable to Vercel, Netlify, or GitHub Pages  

---

## 📈 Planned Features

1. Input transactions (income, expenses, transfers)  
2. View transaction history (sorted by time)  
3. Pie chart: spending categorized by type  
4. Bar chart: monthly income & expense summary  

---

## 🔄 Workflow Overview

1. User enters transaction data (category, amount, date, note, etc.)  
2. Frontend sends an HTTP POST request to the FastAPI backend  
3. FastAPI validates the data and performs necessary logic  
4. Backend writes data to Google Sheets via Google API  
5. When users request history, the frontend sends a GET request  
6. FastAPI retrieves data from Google Drive and returns the results  
7. Frontend displays the data as tables or charts  

---

## Table Schema

| Column Name        | Data Type                                | Description                                         |
|--------------------|------------------------------------------|-----------------------------------------------------|
| `transaction_id`   | INTEGER PRIMARY KEY AUTOINCREMENT        | Unique ID for each transaction                      |
| `user_id`          | INTEGER                                  | ID of the user making the transaction               |
| `date`             | TEXT                                     | Date of transaction (ISO format `YYYY-MM-DD`)       |
| `amount`           | REAL                                     | Transaction amount                                  |
| `tags`             | REAL                                     | e.g., “groceries”, “rent”, “salary” (for analytics) |
| `category`         | TEXT                                     | e.g., Withdrawal, Deposit, Transfer                 |
| `description`      | TEXT                                     | Optional details                                    |
| `balance`          | REAL                                     | Account balance after transaction                   |
| `piggy_bank`       | TEXT                                     | Optional: name of the savings jar or sub-account    |
| `currency`         | TEXT                                     | e.g., USD, EUR, JPY                                 |

---

## 📁 Folder Structure

```bash
PiggyNest/
│
├── backend/
│   │                       
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app entry point
│   │   ├── config.py                   # Configuration management
│   │   ├── dependencies.py             # Dependency injection (DB session, auth)
│   │   │
│   │   ├── api/                        # API routes
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── transactions.py     # Transaction endpoints
│   │   │       ├── accounts.py         # Account endpoints
│   │   │       ├── categories.py       # Category endpoints
│   │   │       ├── piggy_banks.py      # Piggy bank endpoints
│   │   │       ├── reports.py          # Reports & analytics
│   │   │       └── auth.py             # Authentication endpoints
│   │   │
│   │   ├── domain/                     # Core business logic (stateless)
│   │   │   ├── accounts.py             # Account rules
│   │   │   ├── transactions.py         # Transaction rules
│   │   │   ├── categories.py           # Category rules
│   │   │   ├── piggy_banks.py          # Piggy bank rules
│   │   │   └── reports.py              # Report/aggregation logic
│   │   │
│   │   ├── models/                     # SQLAlchemy models
│   │   │   ├── base.py                 # Base class (declarative_base)
│   │   │   ├── account.py
│   │   │   ├── transaction.py
│   │   │   ├── category.py
│   │   │   └── piggy_bank.py
│   │   │
│   │   ├── schemas/                    # Pydantic schemas (request/response)
│   │   │   ├── account.py
│   │   │   ├── transaction.py
│   │   │   ├── category.py
│   │   │   └── piggy_bank.py
│   │   │
│   │   ├── db/                         # Database setup & repositories
│   │   │   ├── __init__.py
│   │   │   ├── session.py              # Engine & SessionLocal
│   │   │   ├── base.py                 # Base model metadata
│   │   │   └── repositories/           # Data access layer
│   │   │       ├── account_repo.py
│   │   │       ├── transaction_repo.py
│   │   │       ├── category_repo.py
│   │   │       └── piggy_bank_repo.py
│   │   │
│   │   └── utils/                      # Helpers
│   │       ├── date_utils.py
│   │       └── validators.py
│   │
│   ├── tests/                        
│   │   ├── __init__.py
│   │   ├── conftest.py               # Test fixtures (DB session)
│   │   ├── test_api/
│   │   ├── test_core/
│   │   └── test_services/
│   │
│   ├── requirements.txt              # (TODO)
│   ├── pyproject.toml                # (TODO)
│   ├── .env.example                  # (TODO)
│   └── README.md      
│
├── docker/                           # (TODO) Docker configurations
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── docs/                             # (TODO) Documentation
│   ├── api/                          # (TODO) API documentation
│   ├── setup.md                      # (TODO) Setup guide
│   └── architecture.md               # (TODO) Architecture docs
│
├── frontend/                         # (TODO) Next.js/React frontend
│   
├── mobile/                           # (TODO) Flutter mobile app
│
├── scripts/                          # (TODO) Script
│
│
├── .github/                          # (TODO) GitHub specific files
│   └── workflows/                    # (TODO) CI/CD workflows
│       ├── backend-tests.yml
│       └── frontend-tests.yml
│
├── .gitattributes                    # Git attribute rules
├── .gitignore                        # Git ignore rules
├── .env.example                      # (TODO) Environment variables template
├── DevNotes.md                       # Development notes
├── LICENSE                           # (TODO) License file
└── README.md                         # Main project README
```

## 📦 Deployment Recommendations

1. Frontend : Deploy on Vercel or Netlify
2. Backend  : Deploy on Render or Railway (note: may sleep on free tier)
3. Database : SQLite database

## 🔐 Notes & Considerations

- Free-tier backend services may sleep when idle, causing slow first-time responses
- Handle OAuth2 credentials and Service Account keys securely
- Implement basic client-side validation for better UX and data accuracy

## 🚀 Future Expansion

- User authentication & access control
- Migrate to a production-grade database (e.g., PostgreSQL)
- Enhanced analytics & charting features
- Notifications, report export, and other advanced tools

## 🙋‍♂️ About the Author — Ludwig
- B.S. in Computer Science, National Central University
- Master in School of Computing, National University of Singapore
- Passionate about AI, deep learning, and full-stack development
- Motivation: build a complete, practical full-stack system for personal use

## 📜 License
MIT License
