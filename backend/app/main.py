from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, piggy_banks, transactions, transfers, categories, statistics
from app.core.config import settings
from app.db.base import Base, engine

# Create the DB tables (Note: in production use Alembic migrations instead)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# Set up CORS
if settings.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Routers
app.include_router(
    auth.router, 
    prefix=f"{settings.API_V1_PREFIX}/auth", 
    tags=["Authentication"]
)
app.include_router(
    piggy_banks.router, 
    prefix=f"{settings.API_V1_PREFIX}/piggy-banks", 
    tags=["Piggy Banks (Subaccounts)"]
)
app.include_router(
    transactions.router, 
    prefix=f"{settings.API_V1_PREFIX}", 
    tags=["Transactions"]
)
app.include_router(
    transfers.router, 
    prefix=f"{settings.API_V1_PREFIX}/transfers", 
    tags=["Transfers"]
)
app.include_router(
    categories.router,
    prefix=f"{settings.API_V1_PREFIX}/categories",
    tags=["Categories"]
)
app.include_router(
    statistics.router,
    prefix=f"{settings.API_V1_PREFIX}/statistics",
    tags=["Statistics"]
)

@app.get("/")
def read_root():
    return {"message": "Welcome to PiggyNest API", "docs": "/docs"}
