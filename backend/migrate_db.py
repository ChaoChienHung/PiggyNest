import sqlite3
import os

def migrate():
    db_path = './data/bookkeeping.db'
    if not os.path.exists(db_path):
        print("DB not found at", db_path)
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN username VARCHAR(255)")
        cursor.execute("UPDATE users SET username = email WHERE username IS NULL")
        cursor.execute("CREATE UNIQUE INDEX ix_users_username ON users (username)")
        print("Successfully added username to users table.")
    except Exception as e:
        print(f"Skipping users migration (may already exist): {e}")

    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN type VARCHAR(50) DEFAULT 'expense'")
        cursor.execute("UPDATE transactions SET type = 'transfer' WHERE category IN ('Transfer In', 'Transfer Out')")
        print("Successfully added type to transactions table.")
    except Exception as e:
        print(f"Skipping transactions migration (may already exist): {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
