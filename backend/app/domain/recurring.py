import calendar
from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.domain.category_names import canonical_category
from app.domain.notifications import create_notification
from app.models.piggy_bank import PiggyBank
from app.models.recurring_rule import RecurringExecution, RecurringRule
from app.models.transaction import Transaction

MAX_CATCHUP_OCCURRENCES = 366


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def advance_date(
    current: str,
    frequency: str,
    interval: int = 1,
    anchor_day: Optional[int] = None,
) -> str:
    """Advance an ISO `YYYY-MM-DD` calendar date by one recurrence step."""
    d = parse_iso_date(current)
    step = max(1, interval)
    if frequency == "daily":
        return (d + timedelta(days=step)).isoformat()
    if frequency == "weekly":
        return (d + timedelta(weeks=step)).isoformat()
    if frequency == "monthly":
        total_months = (d.year * 12 + (d.month - 1)) + step
        new_year, zero_month = divmod(total_months, 12)
        new_month = zero_month + 1
        target_day = anchor_day if anchor_day is not None else d.day
        last_day = calendar.monthrange(new_year, new_month)[1]
        return date(new_year, new_month, min(target_day, last_day)).isoformat()
    if frequency == "yearly":
        new_year = d.year + step
        target_day = anchor_day if anchor_day is not None else d.day
        last_day = calendar.monthrange(new_year, d.month)[1]
        return date(new_year, d.month, min(target_day, last_day)).isoformat()
    raise ValueError(f"Unsupported recurrence frequency: {frequency}")


def process_due_recurring_rules(
    db: Session,
    user_id: int,
    as_of: Optional[str] = None,
) -> List[Transaction]:
    """
    Atomically and idempotently post all due recurring occurrences for `user_id`
    up to `as_of` (defaults to today's local calendar date).
    """
    cutoff = parse_iso_date(as_of).isoformat() if as_of else date.today().isoformat()
    rules = (
        db.query(RecurringRule)
        .filter(
            RecurringRule.user_id == user_id,
            RecurringRule.status == "active",
            RecurringRule.next_run_date <= cutoff,
        )
        .all()
    )
    if not rules:
        return []

    banks_by_id = {
        pb.id: pb
        for pb in db.query(PiggyBank).filter(PiggyBank.user_id == user_id).all()
    }
    created: List[Transaction] = []

    for rule in rules:
        bank = banks_by_id.get(rule.piggy_bank_id)
        if bank is None:
            rule.status = "stopped"
            continue

        anchor_day = parse_iso_date(rule.start_date).day
        iterations = 0
        while (
            rule.status == "active"
            and rule.next_run_date <= cutoff
            and iterations < MAX_CATCHUP_OCCURRENCES
        ):
            if rule.end_date and rule.next_run_date > rule.end_date:
                rule.status = "stopped"
                break

            scheduled = rule.next_run_date
            existing = (
                db.query(RecurringExecution)
                .filter(
                    RecurringExecution.rule_id == rule.id,
                    RecurringExecution.scheduled_date == scheduled,
                )
                .first()
            )
            if existing is None:
                tx = Transaction(
                    piggy_bank_id=rule.piggy_bank_id,
                    amount_minor=rule.amount_minor,
                    type=rule.type,
                    category=canonical_category(rule.category),
                    description=rule.description,
                    date=datetime.fromisoformat(f"{scheduled}T00:00:00"),
                    recurring_rule_id=rule.id,
                )
                db.add(tx)
                db.flush()

                execution = RecurringExecution(
                    rule_id=rule.id,
                    scheduled_date=scheduled,
                    transaction_id=tx.id,
                )
                db.add(execution)
                created.append(tx)

                sign = "+" if rule.amount >= 0 else "-"
                label = rule.description or rule.category or rule.type.title()
                create_notification(
                    db,
                    user_id=user_id,
                    kind="recurring_posted",
                    title=f"Recurring entry posted: {label}",
                    body=(
                        f"Your recurring schedule ({rule.frequency}, every {rule.interval}) "
                        f"posted a transaction to {bank.name}.\n\n"
                        f"Date: {scheduled}\n"
                        f"Amount: {sign}{abs(rule.amount):.2f} {bank.currency}\n"
                        f"Category: {tx.category or 'Uncategorized'}\n"
                        f"Description: {tx.description or '-'}"
                    ),
                    event_key=f"recurring:{rule.id}:{scheduled}",
                )

            next_date = advance_date(scheduled, rule.frequency, rule.interval, anchor_day=anchor_day)
            rule.next_run_date = next_date
            if rule.end_date and rule.next_run_date > rule.end_date:
                rule.status = "stopped"
            iterations += 1

    if created or rules:
        db.commit()
    return created
