#!/usr/bin/env python3
"""
Add last_logout column to users table migration script
"""

import sys
import os
import sqlite3
from datetime import datetime

def add_last_logout_column():
    """Add last_logout column to users table in SQLite database"""
    
    # データベースファイルのパス
    db_path = "/app/instance/admin.db"
    
    try:
        # SQLite接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # last_logout カラムが既に存在するかチェック
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'last_logout' not in columns:
            # last_logout カラムを追加
            cursor.execute("ALTER TABLE users ADD COLUMN last_logout DATETIME")
            conn.commit()
            print(f"[{datetime.now()}] Successfully added last_logout column to users table")
        else:
            print(f"[{datetime.now()}] last_logout column already exists in users table")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[{datetime.now()}] Error adding last_logout column: {e}")
        return False

if __name__ == "__main__":
    print(f"[{datetime.now()}] Starting last_logout column migration...")
    
    if add_last_logout_column():
        print(f"[{datetime.now()}] Migration completed successfully")
        sys.exit(0)
    else:
        print(f"[{datetime.now()}] Migration failed")
        sys.exit(1)