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

This project is a personal finance tracking application featuring a React-based frontend (or pure HTML/CSS/Tailwind), a FastAPI backend, and Google Drive as the storage layer.  
The architecture balances simplicity, flexibility, and speed—ideal for personal or small-scale use.

- ✅ Store records on Google Drive via API  
- ✅ Query and review transaction history  
- ✅ Display charts (pie charts & bar charts) using Chart.js / Recharts  
- ✅ Deployable to Vercel, Netlify, or GitHub Pages  

---

## 📈 Planned Features

1. Input transactions (income, expenses, transfers)  
2. View transaction history (sorted by time)  
3. Pie chart: spending categorized by type  
4. Bar chart: monthly income & expense summary  
5. Google OAuth login (advanced)  
6. Bidirectional sync (reflect Google Drive updates in UI)

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

## 🔧 Tech Stack

| Component | Technologies / Tools                         | Description                           |
|----------|-----------------------------------------------|---------------------------------------|
| Frontend | React + Tailwind CSS                          | User interface & data visualization   |
| Backend  | FastAPI                                       | API services & business logic         |
| Storage  | Google Drive                                   | Data storage and retrieval            |
| Auth     | Google Service Account + OAuth2               | Secure access to Google Drive         |

---

## 📁 Project Structure

```perl
PiggyNest/
├── backend/                          
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
│   ├── requirements.txt              
│   ├── requirements-dev.txt          
│   ├── pyproject.toml                
│   ├── .env.example                  
│   └── README.md      
│
├── frontend/                         # Next.js/React frontend
│   ├── public/
│   │   ├── favicon.ico
│   │   └── assets/
│   │
│   ├── src/
│   │   ├── app/                      # Next.js 13+ app directory
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── dashboard/
│   │   │   ├── transactions/
│   │   │   ├── reports/
│   │   │   └── settings/
│   │   │
│   │   ├── components/               # React components
│   │   │   ├── ui/                   # Reusable UI components
│   │   │   ├── transactions/
│   │   │   ├── charts/
│   │   │   ├── forms/
│   │   │   └── layouts/
│   │   │
│   │   ├── lib/                      # Utilities & helpers
│   │   │   ├── api.ts                # API client
│   │   │   ├── utils.ts
│   │   │   └── constants.ts
│   │   │
│   │   ├── hooks/                    # Custom React hooks
│   │   │   ├── useTransactions.ts
│   │   │   ├── useAccounts.ts
│   │   │   └── useAuth.ts
│   │   │
│   │   ├── store/                    # State management (Zustand/Redux)
│   │   │   ├── authStore.ts
│   │   │   ├── transactionStore.ts
│   │   │   └── uiStore.ts
│   │   │
│   │   └── types/                    # TypeScript types
│   │       ├── transaction.ts
│   │       ├── account.ts
│   │       └── api.ts
│   │
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   └── README.md
│
├── mobile/                           # Flutter mobile app
│   ├── lib/
│   │   ├── main.dart
│   │   ├── models/
│   │   ├── screens/
│   │   ├── widgets/
│   │   ├── services/
│   │   └── utils/
│   ├── pubspec.yaml
│   └── README.md
│
├── shared/                           # Shared code/types
│   ├── types/                        # Shared TypeScript types
│   └── constants/                    # Shared constants
│
├── data/                             # Local data storage
│   ├── user/                         # User-specific data
│   │   └── [account_name]/
│   │       └── piggy_banks/
│   │           └── [bank_name]/
│   │               ├── csv/
│   │               └── json/
│   └── cache/                        # Temporary cache
│
├── config/                           # Configuration files
│   ├── config.yaml                   # Main config
│   ├── config.dev.yaml               # Development config
│   └── config.prod.yaml              # Production config
│
├── scripts/                          # Utility scripts
│   ├── setup.sh                      # Setup script
│   ├── migrate.py                    # Data migration
│   └── backup.py                     # Backup utility
│
├── docs/                             # Documentation
│   ├── api/                          # API documentation
│   ├── setup.md                      # Setup guide
│   └── architecture.md               # Architecture docs
│
├── .github/                          # GitHub specific files
│   └── workflows/                    # CI/CD workflows
│       ├── backend-tests.yml
│       └── frontend-tests.yml
│
├── docker/                           # Docker configurations
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── .gitignore                        # Git ignore rules
├── .env.example                      # Environment variables template
├── README.md                         # Main project README
├── LICENSE                           # License file
└── CHANGELOG.md                      # Version history
```

## 📦 Deployment Recommendations

1. Frontend: Deploy on Vercel or Netlify
2.  Backend: Deploy on Render or Railway (note: may sleep on free tier)
3.  Google Drive: Configure Service Account and grant Spreadsheet access for secure operations

## 🔐 Notes & Considerations

- Google Drive is suitable for small datasets; for larger or complex workloads, consider PostgreSQL or other production databases
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
