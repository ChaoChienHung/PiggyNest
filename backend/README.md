# Backend

## 📁 Project Structure

```bash
backend/
    │                       
    ├── app/
    │    │
    │    ├── api/                         # API routes
    │    │    └── v1/
    │    │        ├── __init__.py
    │    │        ├── transactions.py     # Transaction endpoints
    │    │        ├── accounts.py         # Account endpoints
    │    │        ├── categories.py       # Category endpoints
    │    │        ├── piggy_banks.py      # Piggy bank endpoints
    │    │        ├── reports.py          # Reports & analytics
    │    │        └── auth.py             # Authentication endpoints
    │    │
    │    ├── core/                        # Database setup & repositories
    │    │
    │    ├── db/                          # Database setup & repositories
    │    │    ├── __init__.py
    │    │    ├── session.py              # Engine & SessionLocal
    │    │    ├── base.py                 # Base model metadata
    │    │    └── repositories/           # Data access layer
    │    │        ├── account_repo.py
    │    │        ├── transaction_repo.py
    │    │        ├── category_repo.py
    │    │        └── piggy_bank_repo.py
    │    │
    │    ├── domain/                      # Core business logic (stateless)
    │    │    ├── accounts.py             # Account rules
    │    │    ├── transactions.py         # Transaction rules
    │    │    ├── categories.py           # Category rules
    │    │    ├── piggy_banks.py          # Piggy bank rules
    │    │    └── reports.py              # Report/aggregation logic
    │    │
    │    ├── models/                      # SQLAlchemy models
    │    │    ├── base.py                 # Base class (declarative_base)
    │    │    ├── account.py
    │    │    ├── transaction.py
    │    │    ├── category.py
    │    │    └── piggy_bank.py
    │    │
    │    ├── schemas/                     # Pydantic schemas (request/response)
    │    │    ├── account.py
    │    │    ├── transaction.py
    │    │    ├── category.py
    │    │    └── piggy_bank.py
    │    │
    │    ├── services/                    # App services
    │    │
    │    ├── __init__.py
    │    └── main.py                      # FastAPI app entry point
    │ 
    ├── tests/                            # (TODO)
    │    ├── __init__.py
    │    ├── conftest.py                  # Test fixtures (DB session)
    │    ├── test_api/
    │    ├── test_core/
    │    └── test_services/
    │ 
    ├── requirements.txt                  
    ├── pyproject.toml                    # (TODO)
    ├── .env.example                      # (TODO)
    └── README.md      
```
