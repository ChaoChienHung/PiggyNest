import sqlite3
import os
from app.core.config import LOCAL_DATA_DIR

def upgrade():
    db_path = LOCAL_DATA_DIR / 'piggynest.db'
    if not os.path.exists(db_path):
        print("DB not found at", db_path)
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if currency column exists
    cursor.execute("PRAGMA table_info(piggy_banks);")
    columns = [col[1] for col in cursor.fetchall()]

    if "currency" not in columns:
        print("Adding currency column to piggy_banks table...")
        cursor.execute("ALTER TABLE piggy_banks ADD COLUMN currency VARCHAR(10) NOT NULL DEFAULT 'USD';")
        conn.commit()
        print("Successfully added currency column.")
    else:
        print("currency column already exists in piggy_banks.")

    conn.close()

if __name__ == "__main__":
    upgrade()
