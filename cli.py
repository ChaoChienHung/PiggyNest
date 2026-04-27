#!/usr/bin/env python3
"""
PiggyNest Interactive CLI Tool
------------------------------
A command-line interface to manage personal finances via a REST API 
and inspect the underlying SQLite database directly for debugging.
"""

import requests
import sqlite3
import sys
import os

# -------------------------------------
# SECTION: Configuration & Global State
# -------------------------------------
# The root URL for the backend API services.
BASE_URL = "http://127.0.0.1:8000/api/v1"

# Absolute path to the local SQLite database. 
# It assumes a specific folder structure: ./backend/data/bookkeeping.db
DB_PATH = os.path.join(os.path.dirname(__file__), "backend", "data", "bookkeeping.db")

# Global session variable. Once logged in, this stores the JWT string 
# to authorize subsequent API requests.
token = None


# --------------------------------
# SECTION: UI & Formatting Helpers
# --------------------------------
def print_header(title):
    """
    Prints a visually distinct header to the console to separate 
    different functional sections of the CLI.
    """
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")


# ------------------------------------------------
# SECTION: API Communication Layer (REST Wrappers)
# ------------------------------------------------
# These functions encapsulate the 'requests' library to ensure 
# the Bearer Token is automatically attached if available.

def api_get(endpoint):
    """
    Performs an HTTP GET request.
    :param endpoint: The API path (e.g., "/piggy-banks")
    :return: Parsed JSON response as a dictionary/list.
    """
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
    return r.json()

def api_post(endpoint, json_data=None, data=None):
    """
    Performs an HTTP POST request.
    Handles two types of payloads:
    1. json_data: Used for standard API resource creation (Content-Type: application/json).
    2. data: Used for OAuth2 login forms (Content-Type: application/x-www-form-urlencoded).
    """
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if data:
        # Form-encoded data (primarily for the /auth/login endpoint)
        r = requests.post(f"{BASE_URL}{endpoint}", data=data, headers=headers)
    else:
        # JSON-encoded data for general resource creation
        r = requests.post(f"{BASE_URL}{endpoint}", json=json_data, headers=headers)
    return r.json()

def api_delete(endpoint):
    """
    Performs an HTTP DELETE request to remove a specific resource.
    """
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.delete(f"{BASE_URL}{endpoint}", headers=headers)
    return r.json()

def api_put(endpoint, json_data):
    """
    Performs an HTTP PUT request to update an existing resource.
    """
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.put(f"{BASE_URL}{endpoint}", json=json_data, headers=headers)
    return r.json()


# -----------------------------
# SECTION: Authentication Logic
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
        print("✅ Login successful! Token acquired.")
        return True
    else:
        # Gracefully handle login errors (e.g., 401 Unauthorized)
        print("❌ Login failed: ", resp.get("detail", "Unknown error"))
        return False


# -----------------------------
# SECTION: PiggyBank Operations
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
# SECTION: Transaction Management
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
        
        # Internal Logic: Ensure expenses are recorded as negative numbers for balance math
        if tx_type.lower() in ['expense', 'withdrawal']:
            amount = -abs(amount)
            
        payload = {
            "amount": amount,
            "type": tx_type,
            "description": desc
        }
        
        res = api_post(f"/piggy-banks/{pb_id}/transactions", json_data=payload)
        if "id" in res:
            print("✅ Transaction recorded successfully!")
        else:
            print("❌ Failed to record transaction:", res)
    except ValueError:
        print("Input Error: Ensure ID is an integer and Amount is a number.")

def edit_transaction():
    """
    Modifies an existing transaction.
    This demonstrates a 'Patch' style update where only non-empty fields are sent to the API.
    """
    print_header("Edit Existing Transaction")
    try:
        pb_id = int(input("Enter PiggyBank ID to view history: "))
        txs = api_get(f"/piggy-banks/{pb_id}/transactions")
        
        if not txs or not isinstance(txs, list):
            print("No history found for this bank.")
            return
            
        print("------------------------")
        print("Recent History (Last 10)")
        print("------------------------")
        for tx in txs[:10]:
            print(f"ID [{tx['id']}] {tx['date'][:10]} | {tx['type']} | {tx['amount']} | {tx['description']}")
            
        tx_id = int(input("\nEnter Transaction ID to Edit: "))
        
        # Locate the local object to show current values during prompt
        target_tx = next((t for t in txs if t['id'] == tx_id), None)
        if not target_tx:
            print("Transaction ID not found in current list.")
            return
            
        print(f"\nEditing ID {tx_id}. [Press Enter to keep the current value]")
        amt_in = input(f"New Amount ({target_tx['amount']}): ")
        type_in = input(f"New Type ({target_tx['type']}): ")
        desc_in = input(f"New Description ({target_tx['description']}): ")
        cat_in  = input(f"New Category ({target_tx['category'] or 'None'}): ")
        
        # Build the payload dynamically (partial update)
        payload = {}
        if amt_in: payload['amount'] = float(amt_in)
        if type_in: payload['type'] = type_in
        if desc_in: payload['description'] = desc_in
        if cat_in:  payload['category'] = cat_in
        
        if not payload:
            print("No changes detected. Operation cancelled.")
            return
            
        res = api_put(f"/transactions/{tx_id}", json_data=payload)
        if "id" in res:
            print("✅ Update successful!")
        else:
            print("❌ Update failed:", res)
            
    except ValueError:
        print("Input Error: Invalid data format.")


# ----------------------------------------
# SECTION: Debugging & Database Inspection
# ----------------------------------------
def inspect_db():
    """
    A developer-only tool to inspect the SQLite file directly.
    Helpful for verifying that the API is persisting data correctly.
    """
    print_header("Direct SQLite Database Inspection")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database file not found at: {DB_PATH}")
        return
        
    try:
        # Establish a read-only connection to the database
        conn = sqlite3.connect(DB_PATH)
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
                print(f" Table '{table}' does not exist in schema.")
                
        conn.close()
    except Exception as e:
        print("SQLite Error:", e)


# ----------------------------
# SECTION: Main Execution Loop
# ----------------------------
def main_loop():
    """
    The main engine of the CLI. Manages state (Logged In vs Logged Out)
    and routes user input to the correct functions.
    """
    print("Welcome to PiggyNest CLI v1.0")
    
    while True:
        # STATE: NOT LOGGED IN
        if not token:
            print("\nOptions: (1) Login (q) Quit")
            choice = input("> ").strip().lower()
            if choice == '1':
                login()
            elif choice == 'q':
                print("Exiting...")
                break
        
        # STATE: AUTHORIZED
        else:
            print("\n--- MAIN MENU ---")
            print("1) View PiggyBanks & Balances")
            print("2) Create New PiggyBank")
            print("3) Delete a PiggyBank")
            print("4) Add Transaction")
            print("5) Edit Transaction")
            print("6) Inspect Raw Database (Debug)")
            print("q) Logout & Exit")
            
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
                print("Invalid choice. Please pick 1-6 or q.")

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        # Catching Ctrl+C to exit cleanly without a traceback
        print("\nProcess interrupted by user. Closing...")
        sys.exit(0)