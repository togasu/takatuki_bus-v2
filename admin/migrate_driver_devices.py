"""
ドライバーデバイス管理テーブルを追加するマイグレーションスクリプト

使用方法:
    python migrate_driver_devices.py
"""
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.database import db
from app.models.driver_device import DriverDevice

def migrate():
    """マイグレーションを実行"""
    app = create_app()
    
    with app.app_context():
        print("Starting migration: Adding driver_devices table...")
        
        try:
            # テーブルを作成
            db.create_all()
            print("✓ driver_devices table created successfully")
            
            # テーブルが正しく作成されたか確認
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'driver_devices' in tables:
                print("✓ Migration completed successfully")
                
                # テーブルの構造を表示
                columns = inspector.get_columns('driver_devices')
                print("\nTable structure:")
                for column in columns:
                    print(f"  - {column['name']}: {column['type']}")
                
                return True
            else:
                print("✗ Migration failed: table not found")
                return False
                
        except Exception as e:
            print(f"✗ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
