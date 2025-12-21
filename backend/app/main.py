"""
FastAPI Backend - Main Entry Point
Personal Finance Bookkeeping Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import transactions, accounts, categories, reports

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Personal Finance Bookkeeping API"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(transactions.router, prefix="/api/v1", tags=["transactions"])
app.include_router(accounts.router, prefix="/api/v1", tags=["accounts"])
app.include_router(categories.router, prefix="/api/v1", tags=["categories"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])


@app.get("/")
async def root():
    return {
        "message": "Personal Finance Bookkeeping API",
        "version": settings.VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )