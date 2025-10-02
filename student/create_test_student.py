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
from app.models.reservation import Reservation
from app.utils.penalty_manager import PenaltyManager
from datetime import datetime, timedelta

def create_penalty_test_data(student_data, user_id):
    """ペナルティテスト用のデータを作成"""
    try:
        student_id = student_data['student_id']
        penalty_type = student_data.get('penalty_type', 'auto')
        
        if penalty_type == 'auto':
            # 自動ペナルティ用：3つの未承認予約を作成
            print(f"   🔄 自動ペナルティテスト用予約作成: {student_id}")
            
            # 過去の時間で3つの未承認予約を作成
            for i in range(3):
                test_reservation = Reservation(
                    seat_number=i + 10,  # 座席番号10-12を使用
                    bus_id=1,  # テストバスID
                    user_id=user_id,  # ユーザーのID（数値）
                    approved=0,  # 未承認
                    reserved_time=datetime.utcnow() - timedelta(hours=2 + i)  # 2-4時間前
                )
                db.session.add(test_reservation)
            
            print(f"   ✅ 3つの未承認予約を作成 (座席10-12)")
            
        elif penalty_type == 'manual':
            # 手動ペナルティ用：ペナルティを直接適用
            print(f"   ⚖️  手動ペナルティ適用: {student_id}")
            
            # 1週間後の22:00にペナルティ終了
            end_time = datetime.utcnow() + timedelta(days=7)
            end_time = end_time.replace(hour=22, minute=0, second=0, microsecond=0)
            
            result = PenaltyManager.apply_manual_penalty(
                student_id, 
                "テスト用手動ペナルティ（デバッグデータ）", 
                end_time
            )
            
            if result.get('success'):
                print(f"   ✅ 手動ペナルティ適用完了 (終了: {end_time.strftime('%Y-%m-%d %H:%M')})")
            else:
                print(f"   ❌ 手動ペナルティ適用失敗: {result.get('message')}")
                return False
        
        return True
        
    except Exception as e:
        student_id = student_data.get('student_id', 'unknown')
        print(f"   ❌ ペナルティテストデータ作成エラー ({student_id}): {str(e)}")
        return False

def create_debug_students():
    """デバッグ用の学生ユーザーを作成（ペナルティテスト用データ含む）"""
    app = create_app()
    
    with app.app_context():
        try:
            # デバッグ用学生ユーザーのデータ（ペナルティ設定付き）
            debug_students = [
                {
                    'student_id': '230092',
                    'idm_univ': 'IDM001',
                    'idm_bus': 'BUS001',
                    'penalty_test': True,  # 自動ペナルティテスト用
                    'penalty_type': 'auto'
                },
                {
                    'student_id': '230093',
                    'idm_univ': 'IDM002',
                    'idm_bus': 'BUS002',
                    'penalty_test': True,  # 手動ペナルティテスト用
                    'penalty_type': 'manual'
                },
                {
                    'student_id': '230094',
                    'idm_univ': 'IDM003',
                    'idm_bus': 'BUS003',
                    'penalty_test': False  # ペナルティなし（正常ユーザー）
                },
                {
                    'student_id': '230095',
                    'idm_univ': 'IDM004',
                    'idm_bus': 'BUS004',
                    'penalty_test': False  # ペナルティなし（正常ユーザー）
                }
            ]
            
            created_count = 0
            penalty_created_count = 0
            
            for student_data in debug_students:
                # 既存ユーザーの確認
                existing_user = User.query.filter(
                    User.student_id == student_data['student_id']
                ).first()
                
                if existing_user:
                    print(f"⚠️  ユーザー (学籍番号: {student_data['student_id']}) は既に存在します")
                    # 既存ユーザーにもペナルティテストデータを作成
                    if student_data.get('penalty_test', False):
                        if create_penalty_test_data(student_data, existing_user.id):
                            penalty_created_count += 1
                    continue
                
                # 新しいユーザーを作成
                new_user = User(
                    student_id=student_data['student_id'],
                    idm_univ=student_data['idm_univ'],
                    idm_bus=student_data['idm_bus'],
                    regist_now_time=datetime.utcnow()
                )
                
                db.session.add(new_user)
                db.session.flush()  # IDを取得するためにflush
                created_count += 1
                print(f"✅ デバッグユーザー作成: 学籍番号 {student_data['student_id']}")
                
                # ペナルティテストデータの作成
                if student_data.get('penalty_test', False):
                    if create_penalty_test_data(student_data, new_user.id):
                        penalty_created_count += 1
            
            if created_count > 0 or penalty_created_count > 0:
                db.session.commit()
                print(f"\n🎉 {created_count}人のデバッグ学生ユーザーを作成しました！")
                print(f"⚖️  {penalty_created_count}人にペナルティテストデータを作成しました！")
                print("\n📝 学籍番号とペナルティ状況:")
                for student_data in debug_students:
                    penalty_status = "ペナルティテスト用" if student_data.get('penalty_test') else "正常ユーザー"
                    penalty_type = student_data.get('penalty_type', 'なし')
                    print(f"   - {student_data['student_id']} ({penalty_status} - {penalty_type})")
                
                # 自動ペナルティチェック実行
                print("\n🔄 自動ペナルティチェック実行中...")
                auto_penalty_applied = 0
                for student_data in debug_students:
                    if student_data.get('penalty_type') == 'auto':
                        student_id = student_data['student_id']
                        if PenaltyManager.check_and_apply_auto_penalty(student_id):
                            auto_penalty_applied += 1
                            print(f"   ✅ 自動ペナルティ適用: {student_id}")
                        else:
                            print(f"   ℹ️  自動ペナルティ適用なし: {student_id}")
                
                if auto_penalty_applied > 0:
                    print(f"\n⚖️  {auto_penalty_applied}人に自動ペナルティを適用しました")
                else:
                    print("\n⚖️  自動ペナルティ適用対象者はありませんでした")
                    
            else:
                print("ℹ️  新規作成されたユーザーはありません")
                
        except Exception as e:
            print(f"❌ エラーが発生しました: {str(e)}")
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    create_debug_students()