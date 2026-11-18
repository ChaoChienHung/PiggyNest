"""Exact cent-based storage and validation for ledger amounts."""

from decimal import Decimal, InvalidOperation

CENT = Decimal("0.01")


def to_minor_units(value) -> int:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Amount must be a finite number") from exc
    try:
        if not amount.is_finite() or amount != amount.quantize(CENT):
            raise ValueError("Amount must have at most two decimal places")
        minor = int(amount * 100)
    except InvalidOperation as exc:
        raise ValueError("Amount is outside the supported range") from exc
    if abs(minor) > 2**63 - 1:
        raise ValueError("Amount is outside the supported range")
    return minor


def from_minor_units(value: int) -> float:
    return float(Decimal(value) / 100)
