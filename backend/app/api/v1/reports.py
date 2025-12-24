"""
API Routes - Reports and Analytics
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.transactions import TransactionManager
from app.core.reports import ReportGenerator

router = APIRouter()


@router.get("/accounts/{account_name}/piggy-banks/{piggy_bank_name}/reports/monthly")
async def get_monthly_report(
    account_name: str,
    piggy_bank_name: str,
    year: int,
    month: int
):
    """Generate monthly financial report"""
    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    
    tm = TransactionManager(account_name, piggy_bank_name)
    load_result = tm.load_from_csv(year)
    
    if not load_result["success"]:
        raise HTTPException(status_code=404, detail=load_result["error"])
    
    report_gen = ReportGenerator(tm)
    report = report_gen.generate_monthly_report(year, month)
    
    return report


@router.get("/accounts/{account_name}/piggy-banks/{piggy_bank_name}/reports/yearly")
async def get_yearly_report(
    account_name: str,
    piggy_bank_name: str,
    year: int
):
    """Generate yearly financial report"""
    tm = TransactionManager(account_name, piggy_bank_name)
    load_result = tm.load_from_csv(year)
    
    if not load_result["success"]:
        raise HTTPException(status_code=404, detail=load_result["error"])
    
    report_gen = ReportGenerator(tm)
    report = report_gen.generate_yearly_report(year)
    
    return report


@router.get("/accounts/{account_name}/piggy-banks/{piggy_bank_name}/reports/category-summary")
async def get_category_summary(
    account_name: str,
    piggy_bank_name: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    year: Optional[int] = Query(None)
):
    """Get spending summary by category"""
    tm = TransactionManager(account_name, piggy_bank_name)
    load_result = tm.load_from_csv(year)
    
    if not load_result["success"]:
        raise HTTPException(status_code=404, detail=load_result["error"])
    
    report_gen = ReportGenerator(tm)
    summary = report_gen.get_category_summary(start_date, end_date)
    
    return summary
