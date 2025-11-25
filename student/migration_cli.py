#!/usr/bin/env python3
"""
Flask CLI commands for migration
Flask CLIコマンドを使用したマイグレーション
"""

import os
import sys

# Flaskアプリケーションの設定
os.environ.setdefault('FLASK_APP', 'app')
os.environ.setdefault('FLASK_ENV', 'development')

if __name__ == "__main__":
    # アプリケーションを作成してFlask CLIを有効にする
    from app import create_app
    app = create_app()
    
    # Flask-Migrateのコマンドを実行
    import subprocess
    import time
    
    try:
        print("=== Student Service Migration Setup ===")
        
        # マイグレーション初期化
        print("Step 1: Initializing migration repository...")
        result = subprocess.run(['flask', 'db', 'init'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0 or 'already exists' in result.stderr:
            print("✅ Migration repository initialized or already exists")
        else:
            print(f"❌ Migration init failed: {result.stderr}")
            sys.exit(1)
        
        # 初期マイグレーション作成
        print("Step 2: Creating initial migration...")
        result = subprocess.run(['flask', 'db', 'migrate', '-m', 'Initial migration for student service'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print("✅ Initial migration created successfully")
        else:
            print(f"❌ Migration creation failed: {result.stderr}")
            sys.exit(1)
        
        # マイグレーション適用
        print("Step 3: Applying migrations to database...")
        result = subprocess.run(['flask', 'db', 'upgrade'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print("✅ Migrations applied successfully")
        else:
            print(f"❌ Migration upgrade failed: {result.stderr}")
            sys.exit(1)
        
        print("🎉 Student service migration setup completed!")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
