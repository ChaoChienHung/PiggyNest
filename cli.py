#!/usr/bin/env python3
"""
PiggyNest Interactive CLI Tool
------------------------------
A command-line interface to manage personal finances through the PiggyNest API.
Connects over HTTP when a remote PIGGYNEST_API_URL is set or a local backend is
already running, and falls back to running the local FastAPI app in-process when
no local server is started.
"""

import httpx
import importlib
import sqlite3
import sys
import os
import math
from datetime import date

# -------------------------------------
# Section: Configuration & Global State
# -------------------------------------
# The root URL for the backend API services.
API_PREFIX = "/api/v1"
LOCAL_API_URL = f"http://127.0.0.1:8000{API_PREFIX}"
RAW_API_URL = os.environ.get("PIGGYNEST_API_URL")
BASE_URL = (RAW_API_URL or LOCAL_API_URL).rstrip("/")

# Absolute path to the local SQLite database. 
# Local database lives in the repository's Git-ignored data directory.
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "piggynest.db")

# Global session variable. Once logged in, this stores the JWT string 
# to authorize subsequent API requests.
token = None

# Active transport client ("http" or "inprocess"), initialized lazily on first request.
_client = None
_transport_mode = None

# The signed-in user's date format, read from their account after login.
# The API always sends and accepts ISO dates; the CLI converts only for prompts and display.
DATE_FORMATS = ("YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY")
date_format = "YYYY-MM-DD"


def format_date(api_date, fmt=None):
    """Show an API date such as 2026-11-11T00:00:00 in the user's format."""
    year, month, day = api_date[:10].split("-")
    fmt = fmt or date_format
    if fmt == "DD/MM/YYYY":
        return f"{day}/{month}/{year}"
    if fmt == "MM/DD/YYYY":
        return f"{month}/{day}/{year}"
    return f"{year}-{month}-{day}"


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
    global date_format
    profile = api_post("/auth/test-token")
    if isinstance(profile, dict) and profile.get("date_format") in DATE_FORMATS:
        date_format = profile["date_format"]


# --------------------------------
# Section: UI & Formatting Helpers
# --------------------------------
def print_header(title):
    """
    Prints a visually distinct header to the console to separate 
    different functional sections of the CLI.
    """
    length: int = len(title)
    print(f"{'=' * length}")
    print(f"{title}")
    print(f"{'=' * length}")
    print()


# ------------------------------------------------
# Section: API Communication Layer (REST Wrappers)
# ------------------------------------------------
# Connects over HTTP when targeting a remote API or when a local server is
# running; otherwise runs the local FastAPI app in-process with no server needed.

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
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
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


def _request(method, endpoint, json_data=None, data=None):
    """Send an authenticated API request via HTTP or the in-process FastAPI app."""
    client = get_client()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"{API_PREFIX}{endpoint}" if _transport_mode == "inprocess" else f"{BASE_URL}{endpoint}"
    r = client.request(method, url, json=json_data, data=data, headers=headers)
    return r.json()


def api_get(endpoint):
    """
    Performs an HTTP GET request.
    :param endpoint: The API path (e.g., "/piggy-banks")
    :return: Parsed JSON response as a dictionary/list.
    """
    return _request("GET", endpoint)


def api_post(endpoint, json_data=None, data=None):
    """
    Performs an HTTP POST request.
    Handles two types of payloads:
    1. json_data: Used for standard API resource creation (Content-Type: application/json).
    2. data: Used for OAuth2 login forms (Content-Type: application/x-www-form-urlencoded).
    """
    if data:
        # Form-encoded data (primarily for the /auth/login endpoint)
        return _request("POST", endpoint, data=data)
    # JSON-encoded data for general resource creation
    return _request("POST", endpoint, json_data=json_data)


def api_delete(endpoint):
    """
    Performs an HTTP DELETE request to remove a specific resource.
    """
    return _request("DELETE", endpoint)


def api_put(endpoint, json_data):
    """
    Performs an HTTP PUT request to update an existing resource.
    """
    return _request("PUT", endpoint, json_data=json_data)


# -----------------------------
# Section: Authentication Logic
# -----------------------------
def login():
    """
    Prompts user for credentials and attempts to retrieve a JWT.
    Updates the global 'token' variable upon success.
    """
    global token
    print_header("User Authentication")
    email = input("Email: ")
    password = input("Password: ")
    
    # OAuth2 Password Flow typically requires form-data fields 'username' and 'password'
    resp = api_post("/auth/login", data={"username": email, "password": password})
    
    if "access_token" in resp:
        token = resp["access_token"]
        load_preferences()
        print(f"✅ Login successful! Dates use {date_format}.")
        return True
    else:
        # Gracefully handle login errors (e.g., 401 Unauthorized)
        print("❌ Login failed: ", resp.get("detail", "Unknown error"))
        return False


# -----------------------------
# Section: PiggyBank Operations
# -----------------------------
def list_piggybanks():
    """
    Fetches all PiggyBanks owned by the user.
    For each bank found, it makes a secondary API call to fetch the real-time balance.
    """
    print_header("Your PiggyBanks")
    banks = api_get("/piggy-banks")
    
    if not isinstance(banks, list):
        print("Error: Could not retrieve banks.")
        return
    if not banks:
        print("No PiggyBanks found. Create one first!")
        return
    
    # Iterate through the list and display details
    for pb in banks:
        # Get the calculated balance for this specific bank ID
        bal = api_get(f"/piggy-banks/{pb['id']}/balance")
        print(f"ID [{pb['id']}] | Name: {pb['name']} | Currency: {pb['currency']} | Balance: {bal.get('balance', 0)}")
    return banks

def create_piggybank():
    """
    Collects user input to initialize a new PiggyBank resource.
    """
    print_header("Create New PiggyBank")
    name = input("Bank Name: ")
    currency = input("Currency (Default USD): ") or "USD"
    
    res = api_post("/piggy-banks", json_data={"name": name, "currency": currency})
    if "id" in res:
        print(f"✅ PiggyBank '{name}' created successfully with ID {res['id']}.")
    else:
        print("❌ Creation failed:", res)

def delete_piggybank():
    """
    Deletes a PiggyBank after user confirmation.
    """
    banks = list_piggybanks()
    if not banks: return
    
    try:
        pb_id = int(input("Enter PiggyBank ID to PERMANENTLY DELETE: "))
        confirm = input(f"Are you sure? This will delete all transactions in bank {pb_id}. (y/N): ")
        if confirm.lower() == 'y':
            res = api_delete(f"/piggy-banks/{pb_id}")
            if res.get("success") or "id" not in res: # Adjusting based on API response style
                print("✅ Deleted successfully.")
            else:
                print("❌ Delete failed:", res)

    except ValueError:
        print("Input Error: Please enter a valid numerical ID.")


# -------------------------------
# Section: Transaction Management
# -------------------------------
def add_transaction():
    """
    Creates a new transaction entry. 
    Logic: Automatically converts 'expense' or 'withdrawal' amounts to negative values.
    """
    print_header("Add New Transaction")
    try:
        pb_id = int(input("Target PiggyBank ID: "))
        amount = float(input("Amount: "))
        print("Available Types: [expense, income, deposit, withdrawal]")
        tx_type = input("Type (Default 'expense'): ") or 'expense'
        desc = input("Description/Note: ")
        date_in = input(f"Date {date_format} (Enter for today): ").strip()
        
        # Internal Logic: Ensure expenses are recorded as negative numbers for balance math
        if tx_type.lower() in ['expense', 'withdrawal']:
            amount = -abs(amount)
            
        payload = {
            "amount": amount,
            "type": tx_type,
            "description": desc
        }
        if date_in:
            payload["date"] = parse_date(date_in)
        
        res = api_post(f"/piggy-banks/{pb_id}/transactions", json_data=payload)
        if "id" in res:
            print("✅ Transaction recorded successfully!")
        else:
            print("❌ Failed to record transaction:", res)
    except ValueError as exc:
        print(f"Input Error: Ensure ID is an integer, Amount is a number, and Date is {date_format}. ({exc})")

def edit_transaction():
    """
    Modifies a transaction directly by its numeric ID through the authenticated API.
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
        description = target_tx.get("description") or ""
        if is_piggybank_transfer:
            description = description.partition(": ")[2]
        print(f"\nEditing ID {tx_id}. [Press Enter to keep the current value]")
        amt_in = input(f"New signed amount ({target_tx['amount']}): ").strip()
        type_in = "" if is_piggybank_transfer else input(f"New Type ({target_tx['type']}): ").strip()
        desc_in = input(f"New note ({description or 'None'}; '-' clears): ")
        cat_in = "" if is_piggybank_transfer else input(f"New Category ({target_tx['category'] or 'None'}; '-' clears): ")
        date_in = input(f"New date {date_format} ({format_date(target_tx['date'])}): ").strip()

        payload = {}
        if amt_in:
            amount = float(amt_in)
            if not math.isfinite(amount):
                raise ValueError("Amount must be finite")
            payload['amount'] = amount
        if type_in: payload['type'] = type_in
        if desc_in:
            payload['description'] = ("" if is_piggybank_transfer else None) if desc_in == "-" else desc_in
        if cat_in: payload['category'] = None if cat_in == "-" else cat_in
        if date_in: payload['date'] = parse_date(date_in)

        if not payload:
            print("No changes detected. Operation cancelled.")
            return

        res = api_put(f"/transactions/{tx_id}", json_data=payload)
        if "id" in res:
            print("✅ Update successful!")
        else:
            print("❌ Update failed:", res)

    except ValueError:
        print(f"Input Error: Enter a valid numeric ID, signed amount, and a date as {date_format}.")


# ----------------------------------------
# Section: Debugging & Database Inspection
# ----------------------------------------
def inspect_db():
    """
    A developer-only tool to inspect the SQLite file directly.
    Helpful for verifying that the API is persisting data correctly.
    """
    print_header("Direct SQLite Database Inspection")
    if BASE_URL != LOCAL_API_URL:
        print("DB Inspector is local-only; the CLI is connected to a different API.")
        return
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database file not found at: {DB_PATH}")
        return
        
    try:
        # Establish a read-only connection to the database
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        cursor = conn.cursor()
        
        # Metadata check: List all tables in the schema
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Schema Tables: {[t[0] for t in tables]}")
        
        # Data check: Show a preview of the primary tables
        for table in ['users', 'piggy_banks', 'transactions']:
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
    """
    The main engine of the CLI. Manages state (Logged In vs Logged Out)
    and routes user input to the correct functions.
    """
    print_header("Welcome to PiggyNest CLI v1.0")
    get_client()
    if _transport_mode == "inprocess":
        print("Mode: Local in-process API (no server required)\n")
    else:
        print(f"Mode: HTTP API ({BASE_URL})\n")

    try:
        while True:
            # State: Not Logged In
            # --------------------
            if not token:
                print("Options:")
                print("(1) Login")
                print("(q) Quit")
                print()
                choice = input("> ").strip().lower()
                if choice == '1':
                    login()

                elif choice == 'q':
                    print("Thanks for using PiggyNest! See you next time.")
                    break
            
            # State: Authorized
            # -----------------
            else:
                print_header("Main Menu")
                print("(1) View PiggyBanks & Balances")
                print("(2) Create New PiggyBank")
                print("(3) Delete a PiggyBank")
                print("(4) Add Transaction")
                print("(5) Edit Transaction")
                print("(6) Inspect Raw Database (Debug)")
                print("(q) Logout & Exit")

                choice = input("> ").strip().lower()

                if choice == '1':
                    list_piggybanks()

                elif choice == '2':
                    create_piggybank()

                elif choice == '3':
                    delete_piggybank()

                elif choice == '4':
                    add_transaction()

                elif choice == '5':
                    edit_transaction()

                elif choice == '6':
                    inspect_db()

                elif choice == 'q':
                    print("Goodbye!")
                    break

                else:
                    print("Invalid choice. Please pick (1-6) or (q).")
    finally:
        close_client()

if __name__ == "__main__":
    try:
        main_loop()

    except KeyboardInterrupt:
        # Catching Ctrl+C to exit cleanly without a traceback
        print_header("Process interrupted by user. Closing...")
        sys.exit(0)
