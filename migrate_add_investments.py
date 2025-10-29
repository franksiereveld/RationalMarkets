#!/usr/bin/env python3
"""
Migration script to add investments table
Run this to create the investments table in the database
"""

from database import init_database
from models import Base, Investment

def migrate():
    """Add investments table to database"""
    print("Initializing database connection...")
    db = init_database()
    
    print(f"Connected to: {db.database_url}")
    print("\nCreating investments table...")
    
    try:
        # Create only the investments table
        Investment.__table__.create(db.engine, checkfirst=True)
        print("✅ Investments table created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating investments table: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = migrate()
    exit(0 if success else 1)

