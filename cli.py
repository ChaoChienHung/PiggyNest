#!/usr/bin/env python3
"""
PiggyNest Interactive CLI Tool
------------------------------
A command-line interface to manage personal finances through the PiggyNest API.
Connects over HTTP when a remote PIGGYNEST_API_URL is set or a local backend is
already running, and falls back to running the local FastAPI app in-process when
no local server is started.
"""

from collections import defaultdict
from datetime import date, datetime, timedelta
import importlib
import math
import os
import sqlite3
import sys
from typing import Any, Dict

import httpx

# -------------------------------------
# Section: Configuration & Global State
# -------------------------------------
API_PREFIX = "/api/v1"
LOCAL_API_URL = f"http://127.0.0.1:8000{API_PREFIX}"
RAW_API_URL = os.environ.get("PIGGYNEST_API_URL")
BASE_URL = (RAW_API_URL or LOCAL_API_URL).rstrip("/")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT_DIR, "data", "piggynest.db")
DIAGRAM_DIR = os.path.join(ROOT_DIR, "data", "diagram")
BACKUP_DIR = os.path.join(ROOT_DIR, "data", "backups")

# Global session state. Once logged in, this stores the JWT string and profile.
token = None
user_profile = {}

# Active transport client ("http" or "inprocess"), initialized lazily on first request.
_client = None
_transport_mode = None

# The signed-in user's preferences, read from their account after login.
DATE_FORMATS = ("YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY")
PAGE_SIZES = (10, 20, 50, 0)
date_format = "YYYY-MM-DD"
display_currency = "NTD"
transactions_per_page = 20
net_worth_hidden = False


def format_date(api_date, fmt=None):
    """Show an API date such as 2026-11-11T00:00:00 in the user's format."""
    year, month, day = api_date[:10].split("-")
    fmt = fmt or date_format
    if fmt == "DD/MM/YYYY":
        return f"{day}/{month}/{year}"
    if fmt == "MM/DD/YYYY":
        return f"{month}/{day}/{year}"
    return f"{year}-{month}-{day}"


def format_month_label(year, month, fmt=None):
    """Format a calendar month using the user's date format convention."""
    fmt = fmt or date_format
    if fmt == "YYYY-MM-DD":
        return f"{year:04d}/{month:02d}"
    return f"{month:02d}/{year:04d}"


def parse_date(text, fmt=None):
    """Read a date typed in the user's format and return it as an API datetime.

    DD/MM and MM/DD are ambiguous for days 1-12, so input that does not match
    the chosen format is rejected rather than guessed.
    """
    fmt = fmt or date_format
    value = text.strip()
    try:
        if fmt == "YYYY-MM-DD":
            year, month, day = value.split("-")
        elif fmt == "DD/MM/YYYY":
            day, month, year = value.split("/")
        else:
            month, day, year = value.split("/")
        if len(year) != 4 or not (1 <= len(month) <= 2 and 1 <= len(day) <= 2):
            raise ValueError
        parsed = date(int(year), int(month), int(day))
    except ValueError:
        raise ValueError(f"Enter a real date as {fmt}") from None
    return parsed.isoformat() + "T00:00:00"


def load_preferences():
    """Read the signed-in user's display preferences from the API."""
    global user_profile, date_format, display_currency, transactions_per_page, net_worth_hidden
    profile = api_post("/auth/test-token")
    if isinstance(profile, dict):
        user_profile = profile
        if profile.get("date_format") in DATE_FORMATS:
            date_format = profile["date_format"]
        if profile.get("display_currency"):
            display_currency = profile["display_currency"]
        if profile.get("transactions_per_page") in PAGE_SIZES:
            transactions_per_page = profile["transactions_per_page"]
        if isinstance(profile.get("net_worth_hidden"), bool):
            net_worth_hidden = profile["net_worth_hidden"]


# --------------------------------
# Section: UI & Formatting Helpers
# --------------------------------
def print_header(title):
    """Print a visually distinct header to separate CLI sections."""
    length = len(title)
    print(f"{'=' * length}")
    print(f"{title}")
    print(f"{'=' * length}")
    print()


def format_transaction_row(tx):
    """Format a transaction dict into a single readable summary line."""
    tx_date = format_date(tx["date"]) if tx.get("date") else "-"
    category = tx.get("category") or "-"
    desc = tx.get("description") or ""
    return f"ID [{tx['id']}] | {tx_date} | {tx['amount']:+.2f} | {tx['type']} | {category} | {desc}"


# ------------------------------------------------
# Section: API Communication Layer (REST Wrappers)
# ------------------------------------------------
def is_remote_api():
    """Return True when the CLI is configured to talk to a non-local API URL."""
    return BASE_URL != LOCAL_API_URL


def is_local_server_running():
    """Return True if the local FastAPI server is already reachable on 127.0.0.1:8000."""
    health_url = LOCAL_API_URL[:-len(API_PREFIX)] + "/"
    try:
        response = httpx.get(health_url, timeout=0.5)
        return response.status_code < 500
    except httpx.HTTPError:
        return False


def load_inprocess_client():
    """Load the local FastAPI app in-process without starting an HTTP server."""
    backend_dir = os.path.join(ROOT_DIR, "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from fastapi.testclient import TestClient
    app = importlib.import_module("app.main").app
    return TestClient(app)


def get_client():
    """Return the cached API client, selecting HTTP or in-process mode once."""
    global _client, _transport_mode
    if _client is not None:
        return _client

    if is_remote_api() or is_local_server_running():
        _transport_mode = "http"
        _client = httpx.Client(timeout=10.0)
    else:
        _transport_mode = "inprocess"
        _client = load_inprocess_client()
    return _client


def close_client():
    """Close the active API client and reset transport state."""
    global _client, _transport_mode
    if _client is not None:
        _client.close()
        _client = None
    _transport_mode = None


def _request_raw(method, endpoint, json_data=None, data=None, files=None):
    """Send an authenticated API request and return the raw httpx Response."""
    client = get_client()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"{API_PREFIX}{endpoint}" if _transport_mode == "inprocess" else f"{BASE_URL}{endpoint}"
    return client.request(method, url, json=json_data, data=data, files=files, headers=headers)


def _request(method, endpoint, json_data=None, data=None, files=None):
    """Send an authenticated API request and return parsed JSON."""
    return _request_raw(method, endpoint, json_data=json_data, data=data, files=files).json()


def api_get(endpoint):
    """Perform an authenticated GET request and return JSON."""
    return _request("GET", endpoint)


def api_post(endpoint, json_data=None, data=None, files=None):
    """Perform an authenticated POST request (JSON, form-data, or multipart files)."""
    if files is not None:
        return _request("POST", endpoint, files=files)
    if data:
        return _request("POST", endpoint, data=data)
    return _request("POST", endpoint, json_data=json_data)


def api_delete(endpoint):
    """Perform an authenticated DELETE request and return JSON."""
    return _request("DELETE", endpoint)


def api_put(endpoint, json_data):
    """Perform an authenticated PUT request and return JSON."""
    return _request("PUT", endpoint, json_data=json_data)


# -----------------------------------------
# Section: Currency & Analytics Helpers
# -----------------------------------------
def fetch_rates_map():
    """Return {currency: rate_to_ntd} for the signed-in user, always including NTD=1.0."""
    rates = {"NTD": 1.0}
    resp = api_get("/auth/me/rates")
    if isinstance(resp, list):
        for item in resp:
            if isinstance(item, dict) and item.get("currency") and item.get("rate_to_ntd"):
                rates[item["currency"]] = float(item["rate_to_ntd"])
    return rates


def convert_amount(amount, from_currency, to_currency, rates_map):
    """Convert amount via NTD reference rates. Returns None if a required rate is missing."""
    if from_currency == to_currency:
        return float(amount)
    from_rate = rates_map.get(from_currency)
    to_rate = rates_map.get(to_currency)
    if not from_rate or not to_rate:
        return None
    return float(amount) * from_rate / to_rate


def _parse_bank_selection(banks, prompt="PiggyBank IDs (comma-separated, Enter for all): "):
    """Select one or more PiggyBanks by ID; empty input selects all banks."""
    raw = input(prompt).strip()
    if not raw:
        return list(banks)
    by_id = {b["id"]: b for b in banks}
    selected = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        pb_id = int(part)
        if pb_id not in by_id:
            raise ValueError(f"Unknown PiggyBank ID: {pb_id}")
        if by_id[pb_id] not in selected:
            selected.append(by_id[pb_id])
    return selected


def _collect_filtered_transactions(selected_banks, start_iso=None, end_iso=None, categories=None):
    """Fetch transactions for selected PiggyBanks and apply optional date/category filters."""
    cat_set = {c.lower() for c in categories} if categories else None
    rows = []
    for pb in selected_banks:
        txs = api_get(f"/piggy-banks/{pb['id']}/transactions")
        if not isinstance(txs, list):
            continue
        for tx in txs:
            tx_day = tx["date"][:10]
            if start_iso and tx_day < start_iso[:10]:
                continue
            if end_iso and tx_day > end_iso[:10]:
                continue
            if cat_set is not None:
                tx_cat = (tx.get("category") or "").lower()
                if tx_cat not in cat_set:
                    continue
            rows.append((pb, tx))
    return rows


# ------------------------------------
# Section: Authentication & Recovery
# ------------------------------------
def login():
    """Prompt for credentials, retrieve a JWT, and load user preferences."""
    global token
    print_header("User Authentication")
    email = input("Email: ").strip()
    password = input("Password: ")

    resp = api_post("/auth/login", data={"username": email, "password": password})

    if isinstance(resp, dict) and "access_token" in resp:
        token = resp["access_token"]
        load_preferences()
        print(f"✅ Login successful! Dates use {date_format}, display currency is {display_currency}.")
        return True
    print("❌ Login failed:", resp.get("detail", "Unknown error") if isinstance(resp, dict) else resp)
    return False


def register():
    """Register a new user account."""
    print_header("Register New Account")
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    password = input("Password: ")
    if not username or not email or not password:
        print("❌ Username, email, and password are required.")
        return False

    resp = api_post("/auth/register", json_data={"username": username, "email": email, "password": password})
    if isinstance(resp, dict) and "id" in resp:
        print(f"✅ Account '{resp['username']}' registered! You can now log in.")
        return True
    print("❌ Registration failed:", resp.get("detail", resp) if isinstance(resp, dict) else resp)
    return False


def account_recovery():
    """Username reminder and password reset flows via email recovery endpoints."""
    print_header("Account Recovery")
    print("(1) Send username reminder")
    print("(2) Request password reset code")
    print("(3) Confirm password reset with code")
    print("(b) Back")
    choice = input("> ").strip().lower()

    if choice == "1":
        email = input("Registered email: ").strip()
        resp = api_post("/auth/recovery/username", json_data={"email": email})
        print(resp.get("message", resp.get("detail", resp)) if isinstance(resp, dict) else resp)
    elif choice == "2":
        email = input("Registered email: ").strip()
        resp = api_post("/auth/recovery/password", json_data={"email": email})
        print(resp.get("message", resp.get("detail", resp)) if isinstance(resp, dict) else resp)
    elif choice == "3":
        email = input("Registered email: ").strip()
        code = input("8-digit reset code: ").strip()
        new_password = input("New password: ")
        resp = api_post(
            "/auth/recovery/password/confirm",
            json_data={"email": email, "code": code, "new_password": new_password},
        )
        print(resp.get("message", resp.get("detail", resp)) if isinstance(resp, dict) else resp)


# -----------------------------
# Section: PiggyBank Operations
# -----------------------------
def list_piggybanks():
    """Fetch all owned PiggyBanks, print balances, and show Total Net Worth."""
    print_header("Your PiggyBanks")
    banks = api_get("/piggy-banks")

    if not isinstance(banks, list):
        print("Error: Could not retrieve banks.")
        return
    if not banks:
        print("No PiggyBanks found. Create one first!")
        return

    by_currency = defaultdict(float)
    for pb in banks:
        bal = api_get(f"/piggy-banks/{pb['id']}/balance")
        amount = float(bal.get("balance", 0)) if isinstance(bal, dict) else 0.0
        by_currency[pb["currency"]] += amount
        print(f"ID [{pb['id']}] | Name: {pb['name']} | Currency: {pb['currency']} | Balance: {amount}")

    # Combined Total Net Worth in display_currency
    print()
    if net_worth_hidden:
        print(f"Total Net Worth ({display_currency}): [Hidden in Settings]")
        return banks

    rates_map = fetch_rates_map()
    missing = []
    total_converted = 0.0
    for curr, curr_total in sorted(by_currency.items()):
        converted = convert_amount(curr_total, curr, display_currency, rates_map)
        if converted is None:
            missing.append(curr)
        else:
            total_converted += converted

    if missing:
        print(f"Total Net Worth ({display_currency}): Missing NTD exchange rate for {', '.join(missing)}. Set rates in Settings.")
    else:
        print(f"Total Net Worth ({display_currency}): {total_converted:,.2f}")
        if len(by_currency) > 1:
            parts = [f"{curr} {amt:,.2f}" for curr, amt in sorted(by_currency.items())]
            print("By currency: " + " | ".join(parts))
    return banks


def create_piggybank():
    """Collect user input to initialize a new PiggyBank."""
    print_header("Create New PiggyBank")
    name = input("Bank Name: ").strip()
    currency = (input("Currency (Default NTD): ").strip() or "NTD").upper()

    res = api_post("/piggy-banks", json_data={"name": name, "currency": currency})
    if isinstance(res, dict) and "id" in res:
        print(f"✅ PiggyBank '{name}' created successfully with ID {res['id']}.")
    else:
        print("❌ Creation failed:", res)


def delete_piggybank():
    """Delete a PiggyBank after user confirmation."""
    banks = list_piggybanks()
    if not banks:
        return

    try:
        pb_id = int(input("Enter PiggyBank ID to PERMANENTLY DELETE: "))
        confirm = input(f"Are you sure? This will delete all transactions in bank {pb_id}. (y/N): ")
        if confirm.lower() == "y":
            res = api_delete(f"/piggy-banks/{pb_id}")
            if isinstance(res, dict) and (res.get("success") or "id" not in res):
                print("✅ Deleted successfully.")
            else:
                print("❌ Delete failed:", res)
    except ValueError:
        print("Input Error: Please enter a valid numerical ID.")


# -------------------------------
# Section: Category Management
# -------------------------------
def choose_category():
    """
    Display the user's categories and let them pick by number, type a name,
    create a new category, or press Enter to skip.
    """
    cats = api_get("/categories")
    if not isinstance(cats, list):
        cats = []
    names = [c["name"] for c in cats if isinstance(c, dict) and "name" in c]

    print("\nCategories:")
    for idx, name in enumerate(names, 1):
        print(f"({idx}) {name}")
    print("(n) Add new category")
    print("(Enter) Skip")

    while True:
        choice = input("Category: ").strip()
        if not choice:
            return None
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(names):
                return names[idx - 1]
        if choice.lower() == "n":
            new_name = input("New category name: ").strip()
            if not new_name:
                continue
            res = api_post("/categories", json_data={"name": new_name})
            if isinstance(res, dict) and "name" in res:
                print(f"✅ Added category: {res['name']}")
                return res["name"]
            print("❌ Could not add category:", res.get("detail", res) if isinstance(res, dict) else res)
            continue
        for existing in names:
            if existing.lower() == choice.lower():
                return existing
        print("Invalid category choice. Enter a number, an existing name, 'n' to add, or press Enter to skip.")


def manage_categories():
    """List, add, rename, or delete user categories."""
    print_header("Manage Categories")
    cats = api_get("/categories")
    if isinstance(cats, list) and cats:
        for cat in cats:
            print(f"ID [{cat['id']}] | {cat['name']}")
    else:
        print("(No categories yet)")

    print("\n(1) Add category")
    print("(2) Rename category")
    print("(3) Delete category")
    print("(b) Back")
    choice = input("> ").strip().lower()

    if choice == "1":
        name = input("New category name: ").strip()
        if not name:
            print("Cancelled.")
            return
        res = api_post("/categories", json_data={"name": name})
        if isinstance(res, dict) and "id" in res:
            print(f"✅ Added category '{res['name']}' (ID {res['id']}).")
        else:
            print("❌ Failed:", res)
    elif choice == "2":
        try:
            cat_id = int(input("Category ID to rename: "))
        except ValueError:
            print("Input Error: Enter a valid numeric ID.")
            return
        current_name = next((c["name"] for c in (cats if isinstance(cats, list) else []) if c.get("id") == cat_id), "")
        new_name = input("New name: ").strip()
        res = api_put(f"/categories/{cat_id}", json_data={"name": current_name or new_name, "new_name": new_name})
        if isinstance(res, dict) and "id" in res:
            print(f"✅ Renamed to '{res['name']}'.")
        else:
            print("❌ Failed:", res)
    elif choice == "3":
        try:
            cat_id = int(input("Category ID to delete: "))
        except ValueError:
            print("Input Error: Enter a valid numeric ID.")
            return
        res = api_delete(f"/categories/{cat_id}")
        if isinstance(res, dict) and res.get("success"):
            print("✅ Category deleted.")
        else:
            print("❌ Failed:", res)


# -------------------------------
# Section: Transaction Management
# -------------------------------
def list_transactions():
    """List transactions for a PiggyBank with optional limit, category, and date filters."""
    print_header("View Transactions")
    try:
        pb_id = int(input("PiggyBank ID: "))
    except ValueError:
        print("Input Error: Please enter a valid numerical PiggyBank ID.")
        return

    default_limit = "all" if transactions_per_page == 0 else str(transactions_per_page)
    limit_in = input(f"How many recent rows? (Default {default_limit}, 'all' for all): ").strip().lower()
    if not limit_in:
        limit = None if transactions_per_page == 0 else transactions_per_page
    elif limit_in == "all":
        limit = None
    else:
        try:
            limit = int(limit_in)
            if limit <= 0:
                raise ValueError
        except ValueError:
            print("Input Error: Enter a positive integer or 'all'.")
            return

    txs = api_get(f"/piggy-banks/{pb_id}/transactions")
    if not isinstance(txs, list):
        print("❌ Could not retrieve transactions:", txs)
        return
    if not txs:
        print("No transactions found in this PiggyBank.")
        return

    shown = txs if limit is None else txs[:limit]
    for tx in shown:
        print(format_transaction_row(tx))
    print(f"\nShowing {len(shown)} of {len(txs)} transactions.")


def add_transaction():
    """Create a new transaction entry with category selection and direction normalization."""
    print_header("Add New Transaction")
    try:
        pb_id = int(input("Target PiggyBank ID: "))
        amount = float(input("Amount: "))
        if not math.isfinite(amount):
            raise ValueError("Amount must be finite")
        print("Available Types: [expense, income, transfer_out, transfer_in]")
        tx_type = (input("Type (Default 'expense'): ").strip() or "expense").lower()
        category = choose_category()
        desc = input("Description/Note: ")
        date_in = input(f"Date {date_format} (Enter for today): ").strip()

        if tx_type in ["expense", "withdrawal", "transfer_out"]:
            amount = -abs(amount)
        elif tx_type in ["income", "deposit", "transfer_in"]:
            amount = abs(amount)

        payload = {
            "amount": amount,
            "type": tx_type,
            "description": desc,
        }
        if category:
            payload["category"] = category
        if date_in:
            payload["date"] = parse_date(date_in)

        res = api_post(f"/piggy-banks/{pb_id}/transactions", json_data=payload)
        if isinstance(res, dict) and "id" in res:
            print(f"✅ Transaction recorded successfully! (ID {res['id']})")
        else:
            print("❌ Failed to record transaction:", res)
    except ValueError as exc:
        print(f"Input Error: Ensure ID is an integer, Amount is a number, and Date is {date_format}. ({exc})")


def edit_transaction():
    """
    Modify a transaction directly by its numeric ID through the authenticated API.
    Supports cross-currency PiggyBank transfer counterpart_amount editing.
    Empty input keeps the current value; '-' clears a note or category.
    """
    print_header("Edit Existing Transaction")
    try:
        tx_id = int(input("Enter Transaction ID to Edit: "))
        target_tx = api_get(f"/transactions/{tx_id}")
        if not isinstance(target_tx, dict) or "id" not in target_tx:
            print("Transaction not found or not owned by this user:", target_tx)
            return

        is_piggybank_transfer = target_tx["type"] == "transfer"
        if is_piggybank_transfer and target_tx["transaction_id"] == f"entry:{tx_id}":
            print("This historical transfer needs repair before it can be edited.")
            return

        is_cross_currency = False
        counterpart_amount_current = None
        if is_piggybank_transfer:
            pair = api_get(f"/transfers/{target_tx['transaction_id']}")
            if isinstance(pair, dict) and "debit" in pair and "credit" in pair:
                banks = api_get("/piggy-banks")
                curr_by_pb = {b["id"]: b["currency"] for b in banks} if isinstance(banks, list) else {}
                debit_leg, credit_leg = pair["debit"], pair["credit"]
                debit_curr = curr_by_pb.get(debit_leg.get("piggy_bank_id"))
                credit_curr = curr_by_pb.get(credit_leg.get("piggy_bank_id"))
                if debit_curr and credit_curr and debit_curr != credit_curr:
                    is_cross_currency = True
                    other_leg = credit_leg if debit_leg.get("id") == tx_id else debit_leg
                    counterpart_amount_current = abs(other_leg.get("amount", 0))

        description = target_tx.get("description") or ""
        if is_piggybank_transfer:
            description = description.partition(": ")[2]
        print(f"\nEditing ID {tx_id}. [Press Enter to keep the current value]")
        amt_in = input(f"New signed amount ({target_tx['amount']}): ").strip()
        counterpart_in = ""
        if is_cross_currency:
            counterpart_in = input(f"New positive counterpart amount ({counterpart_amount_current}): ").strip()
        type_in = "" if is_piggybank_transfer else input(f"New Type ({target_tx['type']}): ").strip()
        desc_in = input(f"New note ({description or 'None'}; '-' clears): ")
        cat_in = "" if is_piggybank_transfer else input(f"New Category ({target_tx['category'] or 'None'}; '-' clears): ")
        date_in = input(f"New date {date_format} ({format_date(target_tx['date'])}): ").strip()

        payload: Dict[str, Any] = {}
        if amt_in:
            amount = float(amt_in)
            if not math.isfinite(amount):
                raise ValueError("Amount must be finite")
            payload["amount"] = amount
        if counterpart_in:
            counterpart_val = float(counterpart_in)
            if not math.isfinite(counterpart_val) or counterpart_val <= 0:
                raise ValueError("Counterpart amount must be positive")
            payload["counterpart_amount"] = counterpart_val
        if type_in:
            payload["type"] = type_in
        if desc_in:
            payload["description"] = ("" if is_piggybank_transfer else None) if desc_in == "-" else desc_in
        if cat_in:
            payload["category"] = None if cat_in == "-" else cat_in
        if date_in:
            payload["date"] = parse_date(date_in)

        if not payload:
            print("No changes detected. Operation cancelled.")
            return

        res = api_put(f"/transactions/{tx_id}", json_data=payload)
        if isinstance(res, dict) and "id" in res:
            print("✅ Update successful!")
        else:
            print("❌ Update failed:", res)

    except ValueError:
        print(f"Input Error: Enter a valid numeric ID, signed amount, and a date as {date_format}.")


def delete_transaction():
    """Delete a transaction by its numeric ID after showing a preview and confirming."""
    print_header("Delete Transaction")
    try:
        tx_id = int(input("Enter Transaction ID to Delete: "))
    except ValueError:
        print("Input Error: Please enter a valid numerical ID.")
        return

    target_tx = api_get(f"/transactions/{tx_id}")
    if not isinstance(target_tx, dict) or "id" not in target_tx:
        print("Transaction not found or not owned by this user:", target_tx)
        return

    print(format_transaction_row(target_tx))
    if target_tx.get("type") == "transfer" and target_tx.get("transaction_id") != f"entry:{tx_id}":
        print("Note: This is a PiggyBank transfer. Deleting it removes both linked transactions.")

    confirm = input("Delete this transaction? (y/N): ").strip().lower()
    if confirm != "y":
        print("Delete cancelled.")
        return

    res = api_delete(f"/transactions/{tx_id}")
    if isinstance(res, dict) and res.get("success"):
        print("✅ Transaction deleted successfully.")
    else:
        print("❌ Delete failed:", res)


# -----------------------------
# Section: PiggyBank Transfers
# -----------------------------
def transfer_between_piggybanks():
    """Create a same-currency or cross-currency PiggyBank transfer atomically."""
    print_header("Transfer Between PiggyBanks")
    banks = api_get("/piggy-banks")
    if not isinstance(banks, list) or len(banks) < 2:
        print("You need at least two PiggyBanks to make a PiggyBank transfer.")
        return

    by_id = {b["id"]: b for b in banks}
    for pb in banks:
        print(f"ID [{pb['id']}] | {pb['name']} ({pb['currency']})")

    try:
        src_id = int(input("\nSource PiggyBank ID: "))
        dst_id = int(input("Target PiggyBank ID: "))
        if src_id not in by_id or dst_id not in by_id:
            print("❌ Invalid PiggyBank ID.")
            return
        if src_id == dst_id:
            print("❌ Source and target PiggyBanks must be different.")
            return

        src_bank, dst_bank = by_id[src_id], by_id[dst_id]
        amount = float(input(f"Amount sent ({src_bank['currency']}): "))
        if not math.isfinite(amount) or amount <= 0:
            raise ValueError("Amount must be positive")

        payload = {
            "source_piggy_bank_id": src_id,
            "target_piggy_bank_id": dst_id,
            "amount": amount,
        }

        if src_bank["currency"] != dst_bank["currency"]:
            received = float(input(f"Amount received ({dst_bank['currency']}): "))
            if not math.isfinite(received) or received <= 0:
                raise ValueError("Received amount must be positive")
            payload["received_amount"] = received
            print(f"Implied rate: 1 {src_bank['currency']} = {received / amount:.4f} {dst_bank['currency']}")

        desc = input("Description/Note (optional): ").strip()
        if desc:
            payload["description"] = desc
        date_in = input(f"Date {date_format} (Enter for today): ").strip()
        if date_in:
            payload["date"] = parse_date(date_in)

        res = api_post("/transfers", json_data=payload)
        if isinstance(res, dict) and res.get("success"):
            entry_ids = res.get("entry_ids", [])
            print(f"✅ Transfer recorded! Transaction IDs: {entry_ids}")
        else:
            print("❌ Transfer failed:", res)
    except ValueError as exc:
        print(f"Input Error: {exc}")


# ------------------------------------
# Section: Reports & Chart Export
# ------------------------------------
def _period_keys_between(start_day, end_day, period):
    """Return every calendar period key between start_day and end_day inclusive."""
    s = date.fromisoformat(start_day)
    e = date.fromisoformat(end_day)
    keys = []
    if period == "daily":
        cur = s
        while cur <= e:
            keys.append(cur.isoformat())
            cur += timedelta(days=1)
    elif period == "monthly":
        y, m = s.year, s.month
        while (y, m) <= (e.year, e.month):
            keys.append(f"{y:04d}-{m:02d}")
            m += 1
            if m > 12:
                m = 1
                y += 1
    else:  # yearly
        for y in range(s.year, e.year + 1):
            keys.append(f"{y:04d}")
    return keys


def _tx_period_key(day_str, period):
    if period == "daily":
        return day_str[:10]
    if period == "monthly":
        return day_str[:7]
    return day_str[:4]


def _format_period_key(key, period):
    if period == "daily":
        return format_date(key + "T00:00:00")
    if period == "monthly":
        y, m = key.split("-")
        return format_month_label(int(y), int(m))
    return key


def view_reports():
    """Print daily, monthly, or yearly numeric summaries in the display currency."""
    print_header("Numeric Reports")
    banks = api_get("/piggy-banks")
    if not isinstance(banks, list) or not banks:
        print("No PiggyBanks found.")
        return

    for pb in banks:
        print(f"ID [{pb['id']}] | {pb['name']} ({pb['currency']})")

    try:
        selected = _parse_bank_selection(banks)
        if not selected:
            print("No PiggyBanks selected.")
            return
        period = (input("Period [daily / monthly / yearly] (Default 'monthly'): ").strip() or "monthly").lower()
        if period not in ("daily", "monthly", "yearly"):
            print("Invalid period. Choose daily, monthly, or yearly.")
            return
        start_in = input(f"Start date {date_format} (Enter for earliest): ").strip()
        end_in = input(f"End date {date_format} (Enter for latest): ").strip()
        start_iso = parse_date(start_in) if start_in else None
        end_iso = parse_date(end_in) if end_in else None
        cat_in = input("Filter categories (comma-separated, Enter for all): ").strip()
        categories = [c.strip() for c in cat_in.split(",") if c.strip()] if cat_in else None
    except ValueError as exc:
        print(f"Input Error: {exc}")
        return

    rates_map = fetch_rates_map()
    rows = _collect_filtered_transactions(selected, start_iso=start_iso, end_iso=end_iso, categories=categories)
    if not rows:
        print("No matching transactions.")
        return

    # Check currency conversion
    converted_rows = []
    missing_currencies = set()
    for pb, tx in rows:
        val = convert_amount(tx["amount"], pb["currency"], display_currency, rates_map)
        if val is None:
            missing_currencies.add(pb["currency"])
        else:
            converted_rows.append((pb, tx, val))

    if missing_currencies:
        print(f"❌ Missing NTD exchange rate for: {', '.join(sorted(missing_currencies))}. Configure rates in Settings.")
        return

    days = [tx["date"][:10] for _, tx, _ in converted_rows]
    min_day = start_iso[:10] if start_iso else min(days)
    max_day = end_iso[:10] if end_iso else max(days)
    period_keys = _period_keys_between(min_day, max_day, period)

    buckets = {k: {"income": 0.0, "spending": 0.0, "count": 0} for k in period_keys}
    for _, tx, val in converted_rows:
        if tx.get("type") == "transfer":
            continue  # Exclude PiggyBank transfers from income and spending totals
        k = _tx_period_key(tx["date"][:10], period)
        if k not in buckets:
            continue
        buckets[k]["count"] += 1
        if val > 0:
            buckets[k]["income"] += val
        elif val < 0:
            buckets[k]["spending"] += abs(val)

    print(f"\nReport ({period}, currency: {display_currency})")
    print(f"{'Period':<12} | {'Income':>12} | {'Spending':>12} | {'Net':>12} | {'Count':>5}")
    print("-" * 65)
    for k in period_keys:
        b = buckets[k]
        net = b["income"] - b["spending"]
        print(f"{_format_period_key(k, period):<12} | {b['income']:>12.2f} | {b['spending']:>12.2f} | {net:>+12.2f} | {b['count']:>5}")

    n = len(period_keys)
    total_inc = sum(b["income"] for b in buckets.values())
    total_spd = sum(b["spending"] for b in buckets.values())
    total_net = total_inc - total_spd
    total_cnt = sum(b["count"] for b in buckets.values())
    print("-" * 65)
    print(f"{'Total':<12} | {total_inc:>12.2f} | {total_spd:>12.2f} | {total_net:>+12.2f} | {total_cnt:>5}")
    print(f"{'Average':<12} | {total_inc / n:>12.2f} | {total_spd / n:>12.2f} | {total_net / n:>+12.2f} | {total_cnt / n:>5.1f}")


def export_charts(output_dir=None):
    """Export balance, monthly cashflow, and expense category charts as PNGs under data/diagram/."""
    print_header("Export Charts to data/diagram/")
    banks = api_get("/piggy-banks")
    if not isinstance(banks, list) or not banks:
        print("No PiggyBanks found.")
        return []

    for pb in banks:
        print(f"ID [{pb['id']}] | {pb['name']} ({pb['currency']})")

    try:
        selected = _parse_bank_selection(banks)
        if not selected:
            print("No PiggyBanks selected.")
            return []
        chart_choice = (input("Chart type [balance / cashflow / categories / all] (Default 'all'): ").strip() or "all").lower()
        if chart_choice not in ("balance", "cashflow", "categories", "all"):
            print("Invalid chart type.")
            return []
        start_in = input(f"Start date {date_format} (Enter for earliest): ").strip()
        end_in = input(f"End date {date_format} (Enter for latest): ").strip()
        start_iso = parse_date(start_in) if start_in else None
        end_iso = parse_date(end_in) if end_in else None
        cat_in = input("Filter categories (comma-separated, Enter for all): ").strip()
        categories = [c.strip() for c in cat_in.split(",") if c.strip()] if cat_in else None
    except ValueError as exc:
        print(f"Input Error: {exc}")
        return []

    rates_map = fetch_rates_map()
    target_currency = selected[0]["currency"] if len(selected) == 1 else display_currency
    rows = _collect_filtered_transactions(selected, start_iso=start_iso, end_iso=end_iso, categories=categories)
    if not rows:
        print("No matching transactions to plot.")
        return []

    converted_rows = []
    missing_currencies = set()
    for pb, tx in rows:
        val = convert_amount(tx["amount"], pb["currency"], target_currency, rates_map)
        if val is None:
            missing_currencies.add(pb["currency"])
        else:
            converted_rows.append((pb, tx, val))

    if missing_currencies:
        print(f"❌ Missing NTD exchange rate for: {', '.join(sorted(missing_currencies))}. Configure rates in Settings.")
        return []

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    target_dir = output_dir or DIAGRAM_DIR
    os.makedirs(target_dir, exist_ok=True)
    scope_slug = selected[0]["name"].replace(" ", "_") if len(selected) == 1 else "combined"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    saved_paths = []
    want = {"balance", "cashflow", "categories"} if chart_choice == "all" else {chart_choice}

    # 1. Balance over time (includes PiggyBank transfers since they change balance)
    if "balance" in want:
        daily_delta = defaultdict(float)
        for _, tx, val in converted_rows:
            daily_delta[tx["date"][:10]] += val
        sorted_days = sorted(daily_delta.keys())
        running = 0.0
        balances = []
        for d in sorted_days:
            running += daily_delta[d]
            balances.append(running)
        labels = [format_date(d + "T00:00:00") for d in sorted_days]

        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.plot(range(len(labels)), balances, color="#e05780", linewidth=2)
        ax.fill_between(range(len(labels)), balances, alpha=0.15, color="#ff8da1")
        step = max(1, len(labels) // 8)
        ticks = list(range(0, len(labels), step))
        ax.set_xticks(ticks)
        ax.set_xticklabels([labels[i] for i in ticks], rotation=30, ha="right")
        ax.set_title(f"Balance Over Time ({scope_slug}, {target_currency})")
        ax.set_ylabel(target_currency)
        ax.grid(alpha=0.25)
        fig.tight_layout()
        out_path = os.path.join(target_dir, f"balance_{scope_slug}_{stamp}.png")
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        saved_paths.append(out_path)

    # 2. Monthly income vs spending (excludes PiggyBank transfers)
    if "cashflow" in want:
        monthly_inc = defaultdict(float)
        monthly_spd = defaultdict(float)
        for _, tx, val in converted_rows:
            if tx.get("type") == "transfer":
                continue
            ym = tx["date"][:7]
            if val > 0:
                monthly_inc[ym] += val
            elif val < 0:
                monthly_spd[ym] += abs(val)
        months = sorted(set(monthly_inc.keys()) | set(monthly_spd.keys()))
        if months:
            m_labels = [_format_period_key(m, "monthly") for m in months]
            inc_vals = [monthly_inc[m] for m in months]
            spd_vals = [monthly_spd[m] for m in months]
            x = list(range(len(months)))
            width = 0.38

            fig, ax = plt.subplots(figsize=(9, 4.5))
            ax.bar([i - width / 2 for i in x], inc_vals, width=width, label="Income", color="#2a9d8f")
            ax.bar([i + width / 2 for i in x], spd_vals, width=width, label="Spending", color="#e76f51")
            ax.set_xticks(x)
            ax.set_xticklabels(m_labels, rotation=30, ha="right")
            ax.set_title(f"Monthly Income vs Spending ({scope_slug}, {target_currency})")
            ax.set_ylabel(target_currency)
            ax.legend()
            ax.grid(axis="y", alpha=0.25)
            fig.tight_layout()
            out_path = os.path.join(target_dir, f"cashflow_{scope_slug}_{stamp}.png")
            fig.savefig(out_path, dpi=150)
            plt.close(fig)
            saved_paths.append(out_path)

    # 3. Expense category breakdown (excludes PiggyBank transfers)
    if "categories" in want:
        by_cat = defaultdict(float)
        for _, tx, val in converted_rows:
            if tx.get("type") == "transfer" or val >= 0:
                continue
            by_cat[tx.get("category") or "Uncategorized"] += abs(val)
        if by_cat:
            sorted_cats = sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)
            cat_labels = [k for k, _ in sorted_cats]
            cat_vals = [v for _, v in sorted_cats]

            fig, ax = plt.subplots(figsize=(7, 5))
            ax.pie(cat_vals, labels=cat_labels, autopct="%1.1f%%", startangle=140)
            ax.set_title(f"Expense Breakdown ({scope_slug}, {target_currency})")
            fig.tight_layout()
            out_path = os.path.join(target_dir, f"categories_{scope_slug}_{stamp}.png")
            fig.savefig(out_path, dpi=150)
            plt.close(fig)
            saved_paths.append(out_path)

    if saved_paths:
        print("✅ Exported charts:")
        for p in saved_paths:
            print(f"  - {p}")
    else:
        print("No data available for the requested chart(s).")
    return saved_paths


# ---------------------------------
# Section: Settings & Excel Backup
# ---------------------------------
def settings_and_backup():
    """Manage profile, display preferences, exchange rates, Excel backup, and account deletion."""
    global token
    print_header("Settings & Backup")
    print(f"User: {user_profile.get('username', '-')} ({user_profile.get('email', '-')})")
    print(f"Date format: {date_format} | Display currency: {display_currency} | Rows/page: {transactions_per_page or 'all'} | Hide net worth: {net_worth_hidden}\n")

    print("(1) Update username or password")
    print("(2) Update display preferences (date format / currency / page size / hide net worth)")
    print("(3) View or update NTD exchange rates")
    print("(4) Export Excel backup (.xlsx)")
    print("(5) Import Excel backup (.xlsx, add-only)")
    print("(6) Delete account (Danger Zone)")
    print("(b) Back")
    choice = input("> ").strip().lower()

    if choice == "1":
        new_username = input("New username (Enter to keep): ").strip()
        new_password = input("New password (Enter to keep): ")
        payload = {}
        if new_username:
            payload["username"] = new_username
        if new_password:
            payload["password"] = new_password
        if not payload:
            print("No changes.")
            return
        res = api_put("/auth/me", json_data=payload)
        if isinstance(res, dict) and "id" in res:
            if new_password:
                token = None
                print("✅ Password updated. Previous tokens were invalidated — please log in again.")
            else:
                load_preferences()
                print(f"✅ Username updated to '{res['username']}'.")
        else:
            print("❌ Update failed:", res)

    elif choice == "2":
        fmt = input(f"Date format {DATE_FORMATS} (Enter to keep '{date_format}'): ").strip()
        curr = input(f"Display currency (Enter to keep '{display_currency}'): ").strip().upper()
        page_in = input(f"Transactions per page {PAGE_SIZES} (Enter to keep {transactions_per_page}): ").strip()
        hide_in = input(f"Hide net worth? [y/n] (Enter to keep {'y' if net_worth_hidden else 'n'}): ").strip().lower()

        payload: Dict[str, Any] = {}
        if fmt:
            payload["date_format"] = fmt
        if curr:
            payload["display_currency"] = curr
        if page_in:
            try:
                payload["transactions_per_page"] = int(page_in)
            except ValueError:
                print("Input Error: Page size must be an integer.")
                return
        if hide_in in ("y", "n"):
            payload["net_worth_hidden"] = hide_in == "y"
        if not payload:
            print("No changes.")
            return

        res = api_put("/auth/me", json_data=payload)
        if isinstance(res, dict) and "id" in res:
            load_preferences()
            print("✅ Preferences updated.")
        else:
            print("❌ Update failed:", res)

    elif choice == "3":
        rates = api_get("/auth/me/rates")
        if isinstance(rates, list) and rates:
            for r in rates:
                print(f"1 {r['currency']} = {r['rate_to_ntd']} NTD (updated {r.get('updated_at', '-')})")
        else:
            print("No custom rates configured.")
        curr = input("\nCurrency to set (e.g. SGD, Enter to skip): ").strip().upper()
        if not curr:
            return
        try:
            rate_val = float(input(f"1 {curr} = ? NTD: "))
        except ValueError:
            print("Input Error: Enter a valid number.")
            return
        res = api_put(f"/auth/me/rates/{curr}", json_data={"rate_to_ntd": rate_val})
        if isinstance(res, dict) and "rate_to_ntd" in res:
            print(f"✅ Saved: 1 {res['currency']} = {res['rate_to_ntd']} NTD")
        else:
            print("❌ Failed:", res)

    elif choice == "4":
        os.makedirs(BACKUP_DIR, exist_ok=True)
        default_path = os.path.join(BACKUP_DIR, f"piggynest-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.xlsx")
        out_path = input(f"Save path (Enter for {default_path}): ").strip() or default_path
        resp = _request_raw("GET", "/backup/export")
        if resp.status_code == 200:
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(resp.content)
            print(f"✅ Backup exported to: {out_path}")
        else:
            print("❌ Export failed:", resp.text)

    elif choice == "5":
        file_path = input("Path to .xlsx backup file: ").strip()
        if not file_path or not os.path.exists(file_path):
            print("❌ File not found.")
            return
        with open(file_path, "rb") as f:
            res = api_post(
                "/backup/import",
                files={"file": (os.path.basename(file_path), f.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
        if isinstance(res, dict) and res.get("success"):
            print(f"✅ Import complete: {res}")
        else:
            print("❌ Import failed:", res)

    elif choice == "6":
        confirm = input("Type DELETE to permanently delete your account and all data: ").strip()
        if confirm != "DELETE":
            print("Account deletion cancelled.")
            return
        res = api_delete("/auth/me")
        if isinstance(res, dict) and res.get("success"):
            token = None
            print("✅ Account permanently deleted.")
        else:
            print("❌ Account deletion failed:", res)


# ----------------------------------------
# Section: Debugging & Database Inspection
# ----------------------------------------
def inspect_db():
    """Inspect the local SQLite file directly (read-only, local-only)."""
    print_header("Direct SQLite Database Inspection")
    if is_remote_api():
        print("DB Inspector is local-only; the CLI is connected to a different API.")
        return

    if not os.path.exists(DB_PATH):
        print(f"❌ Database file not found at: {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Schema Tables: {[t[0] for t in tables]}")

        for table in ["users", "piggy_banks", "transactions"]:
            print("-" * 100)
            print(f"Preview: {table} (Top 3 Rows)")
            print("-" * 100)
            try:
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                rows = cursor.fetchall()
                if not rows:
                    print(" (Empty Table)")
                for r in rows:
                    print(r)
            except sqlite3.OperationalError:
                print(f"Table '{table}' does not exist in schema.")

        conn.close()
    except Exception as e:
        print("SQLite Error:", e)


# ----------------------------
# Section: Main Execution Loop
# ----------------------------
def main_loop():
    """Manage CLI session state and route user input to each feature."""
    print_header("Welcome to PiggyNest CLI v1.0")
    get_client()
    if _transport_mode == "inprocess":
        print("Mode: Local in-process API (no server required)\n")
    else:
        print(f"Mode: HTTP API ({BASE_URL})\n")

    try:
        while True:
            if not token:
                print("Options:")
                print("(1) Login")
                print("(2) Register")
                print("(3) Account Recovery")
                print("(q) Quit")
                print()
                choice = input("> ").strip().lower()
                if choice == "1":
                    login()
                elif choice == "2":
                    register()
                elif choice == "3":
                    account_recovery()
                elif choice == "q":
                    print("Thanks for using PiggyNest! See you next time.")
                    break
            else:
                print_header("Main Menu")
                print("(1) View PiggyBanks & Net Worth")
                print("(2) Create New PiggyBank")
                print("(3) Delete a PiggyBank")
                print("(4) View Transactions")
                print("(5) Add Transaction")
                print("(6) Edit Transaction")
                print("(7) Delete Transaction")
                print("(8) Transfer Between PiggyBanks")
                print("(9) Manage Categories")
                print("(10) Reports (Numeric Summary)")
                print("(11) Export Charts (data/diagram/)")
                print("(12) Settings & Backup")
                print("(13) Inspect Raw Database (Debug)")
                print("(q) Logout & Exit")

                choice = input("> ").strip().lower()

                if choice == "1":
                    list_piggybanks()
                elif choice == "2":
                    create_piggybank()
                elif choice == "3":
                    delete_piggybank()
                elif choice == "4":
                    list_transactions()
                elif choice == "5":
                    add_transaction()
                elif choice == "6":
                    edit_transaction()
                elif choice == "7":
                    delete_transaction()
                elif choice == "8":
                    transfer_between_piggybanks()
                elif choice == "9":
                    manage_categories()
                elif choice == "10":
                    view_reports()
                elif choice == "11":
                    export_charts()
                elif choice == "12":
                    settings_and_backup()
                elif choice == "13":
                    inspect_db()
                elif choice == "q":
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice. Please pick (1-13) or (q).")
    finally:
        close_client()


if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print_header("Process interrupted by user. Closing...")
        sys.exit(0)
