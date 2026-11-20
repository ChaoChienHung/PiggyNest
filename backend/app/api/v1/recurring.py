from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.domain.category_names import canonical_category
from app.domain.recurring import advance_date, parse_iso_date, process_due_recurring_rules
from app.models.piggy_bank import PiggyBank
from app.models.recurring_rule import RecurringExecution, RecurringRule
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.recurring import (
    RecurringRuleCreate,
    RecurringRuleRead,
    RecurringRuleUpdate,
    RecurringRunRequest,
)

router = APIRouter()


def _validate_transfer_direction(tx_type: str, amount: float) -> None:
    if (tx_type == "transfer_out" and amount >= 0) or (tx_type == "transfer_in" and amount <= 0):
        raise HTTPException(
            status_code=400,
            detail="External transfer direction must match the signed amount",
        )


def _get_user_bank(db: Session, pb_id: int, user_id: int) -> PiggyBank:
    pb = db.query(PiggyBank).filter(PiggyBank.id == pb_id, PiggyBank.user_id == user_id).first()
    if pb is None:
        raise HTTPException(status_code=404, detail="Piggy bank not found or not owned by user")
    return pb


def _get_user_rule(db: Session, rule_id: int, user_id: int) -> RecurringRule:
    rule = (
        db.query(RecurringRule)
        .filter(RecurringRule.id == rule_id, RecurringRule.user_id == user_id)
        .first()
    )
    if rule is None:
        raise HTTPException(status_code=404, detail="Recurring rule not found")
    return rule


def _serialize(
    rule: RecurringRule,
    bank: Optional[PiggyBank] = None,
    execution_count: int = 0,
) -> RecurringRuleRead:
    pb = bank or rule.piggy_bank
    return RecurringRuleRead(
        id=rule.id,
        piggy_bank_id=rule.piggy_bank_id,
        piggy_bank_name=pb.name if pb else None,
        piggy_bank_currency=pb.currency if pb else None,
        amount=rule.amount,
        type=rule.type,
        category=rule.category,
        description=rule.description,
        frequency=rule.frequency,
        interval=rule.interval,
        start_date=rule.start_date,
        next_run_date=rule.next_run_date,
        end_date=rule.end_date,
        status=rule.status,
        execution_count=execution_count,
        created_at=rule.created_at,
    )


@router.get("", response_model=List[RecurringRuleRead])
def list_recurring_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run any due schedules for the user and list all recurring rules."""
    process_due_recurring_rules(db, current_user.id)
    rules = (
        db.query(RecurringRule)
        .filter(RecurringRule.user_id == current_user.id)
        .order_by(RecurringRule.id.desc())
        .all()
    )
    banks = {
        pb.id: pb
        for pb in db.query(PiggyBank).filter(PiggyBank.user_id == current_user.id).all()
    }
    count_rows = (
        db.query(RecurringExecution.rule_id, func.count(RecurringExecution.id))
        .join(RecurringRule)
        .filter(RecurringRule.user_id == current_user.id)
        .group_by(RecurringExecution.rule_id)
        .all()
    )
    counts = {rule_id: count for rule_id, count in count_rows}
    return [_serialize(rule, banks.get(rule.piggy_bank_id), counts.get(rule.id, 0)) for rule in rules]


@router.post("", response_model=RecurringRuleRead)
def create_recurring_rule(
    payload: RecurringRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a recurring transaction schedule and process due occurrences if applicable."""
    bank = _get_user_bank(db, payload.piggy_bank_id, current_user.id)
    _validate_transfer_direction(payload.type, payload.amount)
    if payload.end_date and payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="End date must be on or after start date")

    initial_tx: Optional[Transaction] = None
    if payload.initial_transaction_id is not None:
        initial_tx = (
            db.query(Transaction)
            .join(PiggyBank)
            .filter(
                Transaction.id == payload.initial_transaction_id,
                PiggyBank.user_id == current_user.id,
            )
            .first()
        )
        if initial_tx is None:
            raise HTTPException(status_code=404, detail="Initial transaction not found")

    anchor_day = parse_iso_date(payload.start_date).day
    next_run = (
        advance_date(payload.start_date, payload.frequency, payload.interval, anchor_day=anchor_day)
        if initial_tx is not None
        else payload.start_date
    )
    initial_status = "stopped" if (payload.end_date and next_run > payload.end_date) else "active"

    rule = RecurringRule(
        user_id=current_user.id,
        piggy_bank_id=bank.id,
        type=payload.type,
        category=canonical_category(payload.category),
        description=payload.description,
        frequency=payload.frequency,
        interval=payload.interval,
        start_date=payload.start_date,
        next_run_date=next_run,
        end_date=payload.end_date,
        status=initial_status,
    )
    rule.amount = payload.amount
    db.add(rule)
    db.flush()

    if initial_tx is not None:
        initial_tx.recurring_rule_id = rule.id
        db.add(
            RecurringExecution(
                rule_id=rule.id,
                scheduled_date=payload.start_date,
                transaction_id=initial_tx.id,
            )
        )

    db.commit()
    process_due_recurring_rules(db, current_user.id)
    db.refresh(rule)
    exec_count = db.query(RecurringExecution).filter(RecurringExecution.rule_id == rule.id).count()
    return _serialize(rule, bank, exec_count)


@router.put("/{rule_id}", response_model=RecurringRuleRead)
def update_recurring_rule(
    rule_id: int,
    payload: RecurringRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Edit a recurring schedule, including pausing, resuming, or stopping future runs."""
    rule = _get_user_rule(db, rule_id, current_user.id)
    data = payload.model_dump(exclude_unset=True)

    next_type = data.get("type", rule.type)
    next_amount = data.get("amount", rule.amount)
    _validate_transfer_direction(next_type, next_amount)

    if "amount" in data and data["amount"] is not None:
        rule.amount = data["amount"]
    if "type" in data and data["type"] is not None:
        rule.type = data["type"]
    if "category" in data:
        rule.category = canonical_category(data["category"])
    if "description" in data:
        rule.description = data["description"]
    if "frequency" in data and data["frequency"] is not None:
        rule.frequency = data["frequency"]
    if "interval" in data and data["interval"] is not None:
        rule.interval = data["interval"]
    if "next_run_date" in data and data["next_run_date"] is not None:
        rule.next_run_date = data["next_run_date"]
    if "end_date" in data:
        rule.end_date = data["end_date"]
    if "status" in data and data["status"] is not None:
        rule.status = data["status"]

    if rule.end_date and rule.end_date < rule.start_date:
        raise HTTPException(status_code=400, detail="End date must be on or after start date")

    db.commit()
    db.refresh(rule)
    bank = _get_user_bank(db, rule.piggy_bank_id, current_user.id)
    exec_count = db.query(RecurringExecution).filter(RecurringExecution.rule_id == rule.id).count()
    return _serialize(rule, bank, exec_count)


@router.post("/run-due")
def run_due_recurring_rules(
    payload: Optional[RecurringRunRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Explicitly process all due recurring rules for the authenticated user."""
    as_of = payload.as_of if payload else None
    created = process_due_recurring_rules(db, current_user.id, as_of=as_of)
    return {
        "posted_count": len(created),
        "transaction_ids": [tx.id for tx in created],
    }


@router.delete("/{rule_id}")
def delete_recurring_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a recurring schedule while preserving all historical posted transactions."""
    rule = _get_user_rule(db, rule_id, current_user.id)
    # Detach historical transactions explicitly (SQLite FK SET NULL may be disabled).
    db.query(Transaction).filter(Transaction.recurring_rule_id == rule.id).update(
        {Transaction.recurring_rule_id: None}
    )
    db.delete(rule)
    db.commit()
    return {"success": True}
