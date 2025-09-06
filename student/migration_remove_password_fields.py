#!/usr/bin/env python3
"""
パスワード関連フィールドを削除するマイグレーション
LDAP認証専用に変更するため、password_hash と password_salt を削除
"""

import os
import sys
sys.path.append('/app')

from app.database import db
from app import create_app

def migrate_remove_password_fields():
    """パスワード関連フィールドを削除"""
    try:
        # SQLでカラムを削除
        print("パスワード関連フィールドを削除中...")
        
        # password_hash カラムを削除
        with db.engine.connect() as connection:
            connection.execute(db.text("ALTER TABLE students DROP COLUMN IF EXISTS password_hash"))
            print("✓ password_hash カラムを削除しました")
            
            # password_salt カラムを削除
            connection.execute(db.text("ALTER TABLE students DROP COLUMN IF EXISTS password_salt"))
            print("✓ password_salt カラムを削除しました")
            
            connection.commit()
        
        print("✓ マイグレーション完了: LDAP認証専用に変更されました")
        
    except Exception as e:
        print(f"❌ マイグレーションエラー: {e}")
        raise e

if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        # データベース接続の確認
        try:
            # テーブルが存在するかチェック
            with db.engine.connect() as connection:
                result = connection.execute(db.text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'students' 
                    AND column_name IN ('password_hash', 'password_salt')
                """))
                
                existing_columns = [row[0] for row in result]
                
                if existing_columns:
                    print(f"削除対象のカラム: {existing_columns}")
                    migrate_remove_password_fields()
                else:
                    print("パスワード関連フィールドは既に削除されています")
                
        except Exception as e:
            print(f"マイグレーション実行エラー: {e}")
            sys.exit(1)
