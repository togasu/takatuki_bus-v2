#!/usr/bin/env python3
"""
データベースの内容を詳しく確認するデバッグスクリプト
"""

import sys
import os

# Flaskアプリケーションのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.database import db
from app.models.user import User, User_Penalty

def debug_database():
    """データベースの内容を詳しく確認"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=== User テーブル ===")
            users = User.query.all()
            for user in users:
                print(f"ID: {user.id}, student_id: {user.student_id} (type: {type(user.student_id)})")
            
            print("\n=== User_Penalty テーブル ===")
            penalties = User_Penalty.query.all()
            for penalty in penalties:
                print(f"ID: {penalty.id}, student_id: {penalty.student_id} (type: {type(penalty.student_id)}), count: {penalty.penalty_count}, time: {penalty.penalty_time}")
            
            print("\n=== ペナルティとユーザーのマッチング確認 ===")
            for user in users:
                print(f"ユーザー: {user.student_id}")
                
                # int()変換でのマッチング試行
                try:
                    penalty_int = User_Penalty.query.filter_by(student_id=int(user.student_id)).first()
                    print(f"  int()変換でのマッチ: {penalty_int is not None}")
                    if penalty_int:
                        print(f"    ペナルティ回数: {penalty_int.penalty_count}")
                except Exception as e:
                    print(f"  int()変換エラー: {e}")
                
                # 文字列でのマッチング試行
                try:
                    penalty_str = User_Penalty.query.filter_by(student_id=user.student_id).first()
                    print(f"  文字列でのマッチ: {penalty_str is not None}")
                    if penalty_str:
                        print(f"    ペナルティ回数: {penalty_str.penalty_count}")
                except Exception as e:
                    print(f"  文字列マッチエラー: {e}")
                
                print()
                
        except Exception as e:
            print(f"❌ エラーが発生しました: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_database()