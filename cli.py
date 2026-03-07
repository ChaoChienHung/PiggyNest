#!/usr/bin/env python3
import requests
import sqlite3
import sys
import os

BASE_URL = "http://127.0.0.1:8000/api/v1"
DB_PATH = os.path.join(os.path.dirname(__file__), "backend", "data", "bookkeeping.db")

token = None

def print_header(title):
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

def api_get(endpoint):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
    return r.json()

def api_post(endpoint, json_data=None, data=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if data:
        r = requests.post(f"{BASE_URL}{endpoint}", data=data, headers=headers)
    else:
        r = requests.post(f"{BASE_URL}{endpoint}", json=json_data, headers=headers)
    return r.json()

def api_delete(endpoint):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.delete(f"{BASE_URL}{endpoint}", headers=headers)
    return r.json()

def login():
    global token
    print_header("Authentication")
    email = input("Email: ")
    password = input("Password: ")
    
    # OAuth2 spec requires form data
    resp = api_post("/auth/login", data={"username": email, "password": password})
    if "access_token" in resp:
        token = resp["access_token"]
        print("✅ Login successful!")
        return True
    else:
        print("❌ Login failed: ", resp.get("detail", "Unknown error"))
        return False

def list_piggybanks():
    print_header("Your PiggyBanks")
    banks = api_get("/piggy-banks")
    if not isinstance(banks, list):
        print("Failed to fetch.")
        return

    if not banks:
        print("No PiggyBanks found.")
        return

    for pb in banks:
        bal = api_get(f"/piggy-banks/{pb['id']}/balance")
        print(f"[{pb['id']}] {pb['name']} ({pb['currency']}) - Balance: {bal.get('balance', 0)}")

def add_transaction():
    print_header("Add Transaction")
    try:
        pb_id = int(input("PiggyBank ID: "))
        amount = float(input("Amount: "))
        types = ['expense', 'income', 'deposit', 'withdrawal']
        print(f"Types: {', '.join(types)}")
        tx_type = input("Type (default: expense): ") or 'expense'
        desc = input("Description: ")
        
        # Simple negative logic for expenses
        if tx_type in ['expense', 'withdrawal']:
            amount = -abs(amount)
            
        payload = {
            "amount": amount,
            "type": tx_type,
            "description": desc
        }
        
        res = api_post(f"/piggy-banks/{pb_id}/transactions", json_data=payload)
        if "id" in res:
            print("✅ Transaction added successfully!")
        else:
            print("❌ Failed:", res)
    except ValueError:
        print("Invalid input.")

def inspect_db():
    print_header("Raw Database Inspection")
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Show tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables in database:", [t[0] for t in tables])
        
        # Show sample data
        for table in ['users', 'piggy_banks', 'transactions']:
            print(f"\n--- Top 3 rows of {table} ---")
            try:
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                rows = cursor.fetchall()
                if not rows:
                    print(" (empty)")
                for r in rows:
                    print(r)
            except sqlite3.OperationalError:
                print(" Table does not exist.")
                
        conn.close()
    except Exception as e:
        print("DB Error:", e)

def main_loop():
    print("Welcome to PiggyNest Interactive CLI!")
    while True:
        if not token:
            print("\nOptions: (1) Login (q) Quit")
            choice = input("> ")
            if choice == '1':
                login()
            elif choice == 'q':
                break
        else:
            print("\nOptions:")
            print("1) List PiggyBanks & Balances")
            print("2) Add Transaction")
            print("3) Inspect Raw SQLite Database")
            print("q) Quit")
            choice = input("> ")
            
            if choice == '1':
                list_piggybanks()
            elif choice == '2':
                add_transaction()
            elif choice == '3':
                inspect_db()
            elif choice == 'q':
                print("Goodbye!")
                break
            else:
                print("Invalid option.")

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
