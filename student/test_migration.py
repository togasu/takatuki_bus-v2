#!/usr/bin/env python3
"""
Student Service Migration Test Script
studentサービスのマイグレーション機能をテストするスクリプト
"""

import os
import sys
import subprocess
import time

def test_student_migration():
    """studentサービスのマイグレーション機能をテスト"""
    print("=== Student Service Migration Test ===")
    
    # カレントディレクトリの確認
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    # 必要なファイルの存在確認
    required_files = [
        'app/__init__.py',
        'app/database.py', 
        'app/models/__init__.py',
        'app_run.py',
        'requirements.txt'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    print("✅ All required files found")
    
    # Flask環境変数の設定
    env = os.environ.copy()
    env['FLASK_APP'] = 'app_run.py'
    env['FLASK_ENV'] = 'development'
    
    try:
        # Step 1: モデルのインポートテスト
        print("\nStep 1: Testing model imports...")
        result = subprocess.run([
            sys.executable, '-c', 
            """
import sys
sys.path.append('.')
try:
    from app import models
    print(f'Available models: {models.__all__}')
    print('✅ Model import successful')
except Exception as e:
    print(f'❌ Model import failed: {e}')
    sys.exit(1)
"""
        ], capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ Model import test failed: {result.stderr}")
            return False
        
        # Step 2: アプリケーション作成テスト
        print("\nStep 2: Testing application creation...")
        result = subprocess.run([
            sys.executable, '-c',
            """
import sys
sys.path.append('.')
try:
    from app import create_app
    app = create_app()
    print(f'✅ Application created: {app}')
    print(f'Database URI: {app.config.get("SQLALCHEMY_DATABASE_URI", "Not set")}')
except Exception as e:
    print(f'❌ Application creation failed: {e}')
    sys.exit(1)
"""
        ], capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ Application creation test failed: {result.stderr}")
            return False
        
        # Step 3: Flask CLIの動作確認
        print("\nStep 3: Testing Flask CLI...")
        result = subprocess.run(['flask', '--help'], 
                              capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            print("✅ Flask CLI available")
        else:
            print(f"❌ Flask CLI not available: {result.stderr}")
            return False
        
        # Step 4: Migration初期化テスト（実際には実行しない）
        print("\nStep 4: Migration setup simulation...")
        
        migration_commands = [
            "flask db init",
            "flask db migrate -m 'Initial migration'", 
            "flask db upgrade"
        ]
        
        print("Migration commands that would be executed:")
        for cmd in migration_commands:
            print(f"  {cmd}")
        
        print("✅ Migration simulation complete")
        
        print("\n🎉 All tests passed! Student service is ready for migration.")
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error during testing: {e}")
        return False

def show_migration_instructions():
    """マイグレーション手順を表示"""
    print("\n=== Migration Instructions ===")
    print("To run migrations manually:")
    print("1. Set environment variables:")
    print("   export FLASK_APP=app_run.py")
    print("   export FLASK_ENV=development")
    print("")
    print("2. Initialize migration repository:")
    print("   flask db init")
    print("")
    print("3. Create initial migration:")
    print("   flask db migrate -m 'Initial migration'")
    print("")
    print("4. Apply migrations:")
    print("   flask db upgrade")
    print("")
    print("Or use the start-dev.ps1 script with 'init' parameter:")
    print("   ./start-dev.ps1 init")

if __name__ == "__main__":
    success = test_student_migration()
    
    if success:
        show_migration_instructions()
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the configuration.")
        sys.exit(1)
