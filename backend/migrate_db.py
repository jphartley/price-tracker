#!/usr/bin/env python3
"""
Database migration script to add currency column to products table
"""

import sqlite3
import os

def migrate_database():
    db_path = "price_tracker.db"
    
    if not os.path.exists(db_path):
        print("Database doesn't exist, nothing to migrate")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if currency column already exists
        cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'currency' not in columns:
            print("Adding currency column to products table...")
            cursor.execute("ALTER TABLE products ADD COLUMN currency TEXT DEFAULT 'GBP'")
            
            # Update existing products with USD currency if they have prices > 0
            # (since we know from testing that US store shows USD prices)
            cursor.execute("UPDATE products SET currency = 'USD' WHERE current_price > 0")
            
            conn.commit()
            print("✅ Currency column added successfully")
        else:
            print("✅ Currency column already exists")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()