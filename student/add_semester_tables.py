"""
学期管理テーブル追加マイグレーション

新しいテーブル:
- semester: 学期情報を管理
- semester_transition: 学期切り替え履歴を記録

実行方法:
    python add_semester_tables.py
"""

import sys
import os

# プロジェクトのルートパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.semester import Semester, SemesterTransition
from datetime import datetime, date

def create_semester_tables():
    """学期関連のテーブルを作成"""
    app = create_app()
    
    with app.app_context():
        try:
            # テーブルを作成
            print("学期管理テーブルを作成中...")
            db.create_all()
            
            # 初期データの投入
            print("初期学期データを作成中...")
            create_initial_semesters()
            
            print("✓ 学期管理テーブルの作成が完了しました")
            
        except Exception as e:
            print(f"✗ エラーが発生しました: {str(e)}")
            raise

def create_initial_semesters():
    """初期学期データを作成"""
    try:
        # 既存の学期があるかチェック
        existing_semester = Semester.query.first()
        if existing_semester:
            print("既存の学期データが見つかりました。初期データの作成をスキップします。")
            return
        
        # 現在の年度を基準に学期を作成
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # 秋学期（9月 - 1月）
        if current_month >= 9:
            # 現在が秋学期
            autumn_semester = Semester(
                name=f"{current_year}年秋学期",
                start_date=date(current_year, 9, 1),
                end_date=date(current_year + 1, 1, 31),
                is_active=True
            )
            db.session.add(autumn_semester)
            print(f"作成: {autumn_semester.name} (アクティブ)")
            
            # 次の春学期も作成
            spring_semester = Semester(
                name=f"{current_year + 1}年春学期",
                start_date=date(current_year + 1, 4, 1),
                end_date=date(current_year + 1, 8, 31),
                is_active=False
            )
            db.session.add(spring_semester)
            print(f"作成: {spring_semester.name}")
            
        elif current_month >= 4:
            # 現在が春学期
            spring_semester = Semester(
                name=f"{current_year}年春学期",
                start_date=date(current_year, 4, 1),
                end_date=date(current_year, 8, 31),
                is_active=True
            )
            db.session.add(spring_semester)
            print(f"作成: {spring_semester.name} (アクティブ)")
            
            # 次の秋学期も作成
            autumn_semester = Semester(
                name=f"{current_year}年秋学期",
                start_date=date(current_year, 9, 1),
                end_date=date(current_year + 1, 1, 31),
                is_active=False
            )
            db.session.add(autumn_semester)
            print(f"作成: {autumn_semester.name}")
            
        else:
            # 1-3月：前年度秋学期の終わり
            autumn_semester = Semester(
                name=f"{current_year - 1}年秋学期",
                start_date=date(current_year - 1, 9, 1),
                end_date=date(current_year, 1, 31),
                is_active=True
            )
            db.session.add(autumn_semester)
            print(f"作成: {autumn_semester.name} (アクティブ)")
            
            # 次の春学期も作成
            spring_semester = Semester(
                name=f"{current_year}年春学期",
                start_date=date(current_year, 4, 1),
                end_date=date(current_year, 8, 31),
                is_active=False
            )
            db.session.add(spring_semester)
            print(f"作成: {spring_semester.name}")
        
        db.session.commit()
        print("✓ 初期学期データの作成が完了しました")
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ 初期学期データ作成エラー: {str(e)}")
        raise

def main():
    print("=== 学期管理テーブル追加マイグレーション ===")
    create_semester_tables()
    print("\n使用方法:")
    print("  学期一覧表示: python semester_cli.py list")
    print("  学期切り替え: python semester_cli.py switch <学期ID>")
    print("  自動チェック: python semester_cli.py auto-check")

if __name__ == '__main__':
    main()