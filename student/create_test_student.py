#!/usr/bin/env python3
"""
Student サービス用のテストユーザー作成スクリプト
デバッグ用の学生ユーザーを作成します
"""

import sys
import os

# Flaskアプリケーションのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.database import db
from app.models.user import User
from datetime import datetime

def create_debug_students():
    """デバッグ用の学生ユーザーを作成"""
    app = create_app()
    
    with app.app_context():
        try:
            # デバッグ用学生ユーザーのデータ
            debug_students = [
                {
                    'student_id': '230092',
                    'idm_univ': 'IDM001',
                    'idm_bus': 'BUS001'
                },
                {
                    'student_id': '230093',
                    'idm_univ': 'IDM002',
                    'idm_bus': 'BUS002'
                },
                {
                    'student_id': '230094',
                    'idm_univ': 'IDM003',
                    'idm_bus': 'BUS003'
                },
                {
                    'student_id': '230095',
                    'idm_univ': 'IDM004',
                    'idm_bus': 'BUS004'
                }
            ]
            
            created_count = 0
            
            for student_data in debug_students:
                # 既存ユーザーの確認
                existing_user = User.query.filter(
                    User.student_id == student_data['student_id']
                ).first()
                
                if existing_user:
                    print(f"⚠️  ユーザー (学籍番号: {student_data['student_id']}) は既に存在します")
                    continue
                
                # 新しいユーザーを作成
                new_user = User(
                    student_id=student_data['student_id'],
                    idm_univ=student_data['idm_univ'],
                    idm_bus=student_data['idm_bus'],
                    regist_now_time=datetime.utcnow()
                )
                
                db.session.add(new_user)
                created_count += 1
                print(f"✅ デバッグユーザー作成: 学籍番号 {student_data['student_id']}")
            
            if created_count > 0:
                db.session.commit()
                print(f"\n🎉 {created_count}人のデバッグ学生ユーザーを作成しました！")
                print("📝 学籍番号:")
                for student_data in debug_students:
                    print(f"   - {student_data['student_id']}")
            else:
                print("ℹ️  新規作成されたユーザーはありません")
                
        except Exception as e:
            print(f"❌ エラーが発生しました: {str(e)}")
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    create_debug_students()