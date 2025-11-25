#!/usr/bin/env python3
"""
Student サービス用のテストペナルティ付与スクリプト
デバッグ用に数名の学生にペナルティを付与します
"""

import sys
import os

# Flaskアプリケーションのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.database import db
from app.models.user import User, User_Penalty
from datetime import datetime, timedelta
import random

def add_test_penalties():
    """テスト用のペナルティを付与"""
    app = create_app()
    
    with app.app_context():
        try:
            # 全学生を取得
            all_students = User.query.all()
            
            if len(all_students) == 0:
                print("❌ 学生ユーザーが見つかりません。先にcreate_test_student.pyを実行してください。")
                return
            
            print(f"📋 現在の学生数: {len(all_students)}人")
            
            # ランダムに3-4名の学生を選択してペナルティを付与
            students_to_penalize = random.sample(all_students, min(4, len(all_students)))
            
            penalty_count = 0
            
            for student in students_to_penalize:
                # 既にペナルティがあるかチェック
                existing_penalty = User_Penalty.query.filter(
                    User_Penalty.student_id == int(student.student_id)
                ).first()
                
                if existing_penalty:
                    print(f"⚠️  学籍番号 {student.student_id} には既にペナルティが付与されています")
                    continue
                
                # ペナルティ回数をランダムに設定（1-3回）
                penalty_count_value = random.randint(1, 3)
                
                # ペナルティを作成
                penalty = User_Penalty(
                    student_id=int(student.student_id),
                    penalty_count=penalty_count_value,
                    penalty_time=datetime.utcnow()
                )
                
                db.session.add(penalty)
                penalty_count += 1
                
                print(f"✅ ペナルティ付与: 学籍番号 {student.student_id}")
                print(f"   ペナルティ回数: {penalty_count_value}回")
                print()
            
            if penalty_count > 0:
                db.session.commit()
                print(f"🎉 {penalty_count}人の学生にペナルティを付与しました！")
                
                # 結果サマリーを表示
                print("\n📊 ペナルティ付与結果:")
                penalized_students = User.query.join(User_Penalty, User.student_id == User_Penalty.student_id.cast(db.String)).all()
                for student in penalized_students:
                    penalty = User_Penalty.query.filter(
                        User_Penalty.student_id == int(student.student_id)
                    ).first()
                    print(f"   - 学籍番号: {student.student_id}, ペナルティ回数: {penalty.penalty_count}回")
                    
            else:
                print("ℹ️  新規ペナルティは付与されませんでした（既存のペナルティがあるため）")
                
        except Exception as e:
            print(f"❌ エラーが発生しました: {str(e)}")
            db.session.rollback()
            sys.exit(1)

def show_penalty_status():
    """現在のペナルティ状況を表示"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n📈 現在のペナルティ状況:")
            print("-" * 50)
            
            all_students = User.query.all()
            penalty_count = 0
            
            for student in all_students:
                penalty = User_Penalty.query.filter(
                    User_Penalty.student_id == int(student.student_id)
                ).first()
                
                if penalty:
                    penalty_count += 1
                    print(f"🚫 学籍番号: {student.student_id}")
                    print(f"   ペナルティ回数: {penalty.penalty_count}回")
                    print(f"   付与日時: {penalty.penalty_time}")
                    print()
                else:
                    print(f"✅ 学籍番号: {student.student_id} - ペナルティなし")
            
            print(f"\n📊 合計: {len(all_students)}人中 {penalty_count}人がペナルティ中")
            
        except Exception as e:
            print(f"❌ エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        show_penalty_status()
    else:
        add_test_penalties()
        show_penalty_status()