from datetime import datetime
from decimal import Decimal

from import_legacy_bookkeeping import LegacyRow, partition_rows


def row(bank, old_id, amount, category, description):
    return LegacyRow(bank, "2025_transactions.csv", old_id, datetime(2025, 9, 24),
                     Decimal(amount), category, description, Decimal(0))


def test_possible_internal_transfers_are_held_for_review():
    source = row("UnitedOverseasBank", 1, "-10", "Withdrawal", "EZLinkSG60")
    target = row("EZLinkSG60", 2, "10", "Savings", "UnitedOverseasBank")
    named_without_exact_pair = row("LudwigTaiwan", 3, "100", "Withdrawal", "ChangHwaBank")
    ambiguous_name = row("ChungHwaPost", 4, "200", "Savings", "Ludwig")
    unmatched_transfer = row("TaishinBank", 5, "-20", "Transfer", "Null")
    ordinary_expense = row("LudwigSingapore", 6, "-5", "Meal", "Lunch")

    safe, pending, matches, reasons = partition_rows([
        source, target, named_without_exact_pair, ambiguous_name,
        unmatched_transfer, ordinary_expense,
    ])

    assert safe == [ordinary_expense]
    assert {item.key for item in pending} == {
        source.key, target.key, named_without_exact_pair.key,
        ambiguous_name.key, unmatched_transfer.key,
    }
    assert matches[source.key] == {target.key}
    assert reasons[named_without_exact_pair.key] == "named_internal_transfer_without_exact_match"
    assert reasons[ambiguous_name.key] == "ambiguous_account_reference"
