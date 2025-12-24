"""
API Routes - Transaction Management
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.core.transactions import TransactionManager

router = APIRouter()


class TransactionCreate(BaseModel):
    date: str
    amount: float
    category: str
    description: str = ""


class TransactionFilter(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    category: Optional[str] = None


@router.post("/accounts/{account_name}/piggy-banks/{piggy_bank_name}/transactions")
async def add_transaction(
    account_name: str,
    piggy_bank_name: str,
    transaction: TransactionCreate
):
    """Add a new transaction"""
    tm = TransactionManager(account_name, piggy_bank_name)
    
    # Load existing data
    load_result = tm.load_from_csv()
    
    # Add transaction
    result = tm.add_transaction(
        date=transaction.date,
        amount=transaction.amount,
        category=transaction.category,
        description=transaction.description
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Save to file
    tm.save_to_csv()
    
    return result


@router.get("/accounts/{account_name}/piggy-banks/{piggy_bank_name}/transactions")
async def get_transactions(
    account_name: str,
    piggy_bank_name: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    year: Optional[int] = Query(None)
):
    """Get transactions with optional filters"""
    tm = TransactionManager(account_name, piggy_bank_name)
    
    # Load data
    load_result = tm.load_from_csv(year)
    if not load_result["success"] and load_result.get("error") != "File not found":
        raise HTTPException(status_code=404, detail=load_result["error"])
    
    # Get filtered transactions
    df = tm.get_transactions(start_date, end_date, category)
    
    # Convert to dict
    transactions = df.to_dict('records')
    
    # Convert timestamps to strings
    for t in transactions:
        if 'Date' in t:
            t['Date'] = t['Date'].isoformat()
    
    return {
        "transactions": transactions,
        "count": len(transactions),
        "balance": tm.current_balance
    }


@router.delete("/accounts/{account_name}/piggy-banks/{piggy_bank_name}/transactions/{transaction_id}")
async def delete_transaction(
    account_name: str,
    piggy_bank_name: str,
    transaction_id: int
):
    """Delete a transaction by ID"""
    tm = TransactionManager(account_name, piggy_bank_name)
    
    # Load existing data
    load_result = tm.load_from_csv()
    if not load_result["success"]:
        raise HTTPException(status_code=404, detail=load_result["error"])
    
    # Delete transaction
    result = tm.delete_transaction_by_id(transaction_id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    
    # Save changes
    tm.save_to_csv()
    
    return result


@router.get("/accounts/{account_name}/piggy-banks/{piggy_bank_name}/balance")
async def get_balance(account_name: str, piggy_bank_name: str, year: Optional[int] = None):
    """Get current balance"""
    tm = TransactionManager(account_name, piggy_bank_name)
    
    load_result = tm.load_from_csv(year)
    
    return {
        "balance": tm.current_balance,
        "transaction_count": len(tm.transactions_df),
        "year": tm.loaded_year
    }
