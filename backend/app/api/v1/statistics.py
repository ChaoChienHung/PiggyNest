from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.piggy_bank import PiggyBank
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/")
def get_statistics(
    timeframe: str = "monthly",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Fetch comprehensive financial analytics for the authenticated user.
    Aggregates all PiggyBanks linked to the user, mapping total Income, Expenses, 
    and categorized spending percentages grouped by Month (`monthly`) or Year (`yearly`).
    """
    # Get all PiggyBanks for the current user to find their IDs and currencies
    piggy_banks = db.query(PiggyBank.id, PiggyBank.currency).filter(PiggyBank.user_id == current_user.id).all()
    if not piggy_banks:
        return []
        
    pb_map = {pb.id: pb.currency for pb in piggy_banks}
    pb_ids = list(pb_map.keys())

    # Query all transactions for these piggy banks
    transactions = db.query(Transaction).filter(Transaction.piggy_bank_id.in_(pb_ids)).all()

    # Aggregate by timeframe, currency, and type
    stats_map = {}

    for tx in transactions:
        currency = pb_map[tx.piggy_bank_id]
        
        if timeframe == "monthly":
            period_key = tx.date.strftime("%Y-%m")
        elif timeframe == "yearly":
            period_key = tx.date.strftime("%Y")
        else:
            period_key = "all"
            
        map_key = f"{period_key}_{currency}"
        
        if map_key not in stats_map:
            stats_map[map_key] = {
                "period": period_key,
                "currency": currency,
                "income": 0.0,
                "expense": 0.0,
                "category_expenses": {},
                "category_incomes": {},
            }

        # Map types to income/expense for charting purposes
        if tx.type in ['income', 'deposit']:
            stats_map[map_key]["income"] += tx.amount
            if tx.category:
                stats_map[map_key]["category_incomes"][tx.category] = stats_map[map_key]["category_incomes"].get(tx.category, 0) + tx.amount
        elif tx.type in ['expense', 'withdrawal', 'transfer']:
            # Transfers are generally treated as expenses from the source piggy bank.
            # Convert negative numbers to positive for charting expenses.
            amt = abs(tx.amount)
            stats_map[map_key]["expense"] += amt
            if tx.category:
                stats_map[map_key]["category_expenses"][tx.category] = stats_map[map_key]["category_expenses"].get(tx.category, 0) + amt

    # Convert map to list and sort by period
    stats_list = list(stats_map.values())
    stats_list.sort(key=lambda x: x["period"])

    return stats_list
