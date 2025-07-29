#!/usr/bin/env python3
"""
Migration script to add original_price columns to existing database tables.
Run this once after updating the schema.
"""

import sqlite3
import os

def migrate_database():
    db_path = "price_tracker.db"
    
    if not os.path.exists(db_path):
        print("Database file not found. No migration needed.")
        return
    
    print("Starting database migration...")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if original_price column exists in products table
        cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "original_price" not in columns:
            print("Adding original_price column to products table...")
            cursor.execute("ALTER TABLE products ADD COLUMN original_price REAL")
            print("✓ Added original_price to products table")
        else:
            print("original_price column already exists in products table")
        
        # Check if original_price column exists in price_history table
        cursor.execute("PRAGMA table_info(price_history)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "original_price" not in columns:
            print("Adding original_price column to price_history table...")
            cursor.execute("ALTER TABLE price_history ADD COLUMN original_price REAL")
            print("✓ Added original_price to price_history table")
        else:
            print("original_price column already exists in price_history table")
        
        # Commit changes
        conn.commit()
        print("✓ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
