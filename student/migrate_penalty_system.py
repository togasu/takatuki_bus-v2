#!/usr/bin/env python3
"""
ペナルティシステムのデータベースマイグレーション
既存のUser_Penaltyテーブルを新しいスキーマに移行
"""

import sys
import os

# Flaskアプリケーションのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.database import db
from app.models.user import User_Penalty, Penalty_Reservation
from datetime import datetime, timedelta, time
import logging

# ログの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_penalty_system():
    """ペナルティシステムのマイグレーション"""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("ペナルティシステムのマイグレーション開始")
            
            # 新しいテーブルを作成
            db.create_all()
            logger.info("新しいテーブル構造を作成しました")
            
            # 既存のデータがある場合の移行処理
            # 注意: この処理は既存データがあることを前提としています
            # 実際の運用では既存データの構造を確認してから実行してください
            
            logger.info("マイグレーション完了")
            
        except Exception as e:
            logger.error(f"マイグレーション中にエラーが発生: {str(e)}")
            db.session.rollback()
            return False
        
        return True

def create_test_penalty():
    """テスト用ペナルティデータの作成"""
    app = create_app()
    
    with app.app_context():
        try:
            # テスト用のペナルティを作成
            test_penalty = User_Penalty(
                student_id='230092',
                end_time_of_usage_restriction=datetime.utcnow() + timedelta(days=14),
                reason='テスト用ペナルティ',
                penalty_type='manual',
                applied_time=datetime.utcnow(),
                is_active=True
            )
            
            db.session.add(test_penalty)
            db.session.commit()
            
            logger.info("テスト用ペナルティを作成しました")
            return True
            
        except Exception as e:
            logger.error(f"テストペナルティ作成中にエラーが発生: {str(e)}")
            db.session.rollback()
            return False

def main():
    """メイン処理"""
    import sys
    
    # コマンドライン引数で非対話モード対応
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "migrate" or action == "1":
            if migrate_penalty_system():
                print("✅ マイグレーションが完了しました")
                sys.exit(0)
            else:
                print("❌ マイグレーションが失敗しました")
                sys.exit(1)
        elif action == "test" or action == "2":
            if create_test_penalty():
                print("✅ テストペナルティを作成しました")
                sys.exit(0)
            else:
                print("❌ テストペナルティ作成が失敗しました")
                sys.exit(1)
    
    # 対話モード
    print("ペナルティシステムマイグレーション")
    print("1. マイグレーション実行")
    print("2. テストペナルティ作成")
    print("3. 終了")
    
    choice = input("選択してください (1-3): ")
    
    if choice == '1':
        if migrate_penalty_system():
            print("✅ マイグレーションが完了しました")
        else:
            print("❌ マイグレーションが失敗しました")
    elif choice == '2':
        if create_test_penalty():
            print("✅ テストペナルティを作成しました")
        else:
            print("❌ テストペナルティ作成が失敗しました")
    elif choice == '3':
        print("終了します")
    else:
        print("無効な選択です")

if __name__ == "__main__":
    main()