#!/usr/bin/env python3
"""
学期管理CLI - 学期の作成・切り替え・管理を行うためのコマンドラインツール

使用例:
    # 新しい学期を作成
    python semester_cli.py create "2024年秋学期" 2024-09-01 2025-01-31

    # 学期をアクティブにする
    python semester_cli.py activate 1

    # 学期を切り替える（ユーザー移行込み）
    python semester_cli.py switch 2

    # 自動学期チェック
    python semester_cli.py auto-check

    # 全学期一覧
    python semester_cli.py list

    # ユーザー移行のみ実行
    python semester_cli.py migrate-users
"""

import sys
import os
import argparse
from datetime import datetime

# プロジェクトのルートパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.semester_utils import SemesterManager
from app.database import db

def create_semester_cmd(args):
    """学期作成コマンド"""
    app = create_app()
    with app.app_context():
        semester, message = SemesterManager.create_semester(
            name=args.name,
            start_date=args.start_date,
            end_date=args.end_date,
            is_active=args.active
        )
        
        if semester:
            print(f"✓ 学期作成成功: {message}")
            print(f"  ID: {semester.id}")
            print(f"  名前: {semester.name}")
            print(f"  期間: {semester.start_date} - {semester.end_date}")
            print(f"  アクティブ: {semester.is_active}")
        else:
            print(f"✗ 学期作成失敗: {message}")
            sys.exit(1)

def list_semesters_cmd(args):
    """学期一覧コマンド"""
    app = create_app()
    with app.app_context():
        semesters = SemesterManager.get_all_semesters()
        active_semester = SemesterManager.get_active_semester()
        current_semester = SemesterManager.get_current_semester()
        
        print("=== 学期一覧 ===")
        if not semesters:
            print("登録されている学期はありません")
            return
            
        for semester in semesters:
            status_indicators = []
            if semester.is_active:
                status_indicators.append("ACTIVE")
            if current_semester and semester.id == current_semester.id:
                status_indicators.append("CURRENT")
            
            status = f" [{', '.join(status_indicators)}]" if status_indicators else ""
            
            print(f"ID: {semester.id:2d} | {semester.name:20s} | {semester.start_date} - {semester.end_date}{status}")

def activate_semester_cmd(args):
    """学期アクティベーションコマンド"""
    app = create_app()
    with app.app_context():
        success, message = SemesterManager.activate_semester(args.semester_id)
        
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            sys.exit(1)

def switch_semester_cmd(args):
    """学期切り替えコマンド"""
    app = create_app()
    with app.app_context():
        # 確認プロンプト
        if not args.force:
            semester = SemesterManager.get_semester_by_id(args.semester_id)
            if not semester:
                print(f"✗ 学期ID {args.semester_id} が見つかりません")
                sys.exit(1)
                
            print(f"学期を「{semester.name}」に切り替えます。")
            if args.migrate_users:
                print("この操作により、現在のUserテーブルのデータがLastSemester_userテーブルに移行され、Userテーブルはクリアされます。")
            
            response = input("続行しますか？ (y/N): ")
            if response.lower() != 'y':
                print("操作をキャンセルしました")
                return
        
        success, message = SemesterManager.switch_semester(args.semester_id, args.migrate_users)
        
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            sys.exit(1)

def auto_check_cmd(args):
    """自動学期チェックコマンド"""
    app = create_app()
    with app.app_context():
        success, message = SemesterManager.auto_semester_check()
        
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            sys.exit(1)

def migrate_users_cmd(args):
    """ユーザー移行コマンド"""
    app = create_app()
    with app.app_context():
        # 確認プロンプト
        if not args.force:
            print("この操作により、現在のUserテーブルのデータがLastSemester_userテーブルに移行され、Userテーブルはクリアされます。")
            response = input("続行しますか？ (y/N): ")
            if response.lower() != 'y':
                print("操作をキャンセルしました")
                return
        
        success, message, migrated_count = SemesterManager.migrate_users_to_last_semester()
        
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            sys.exit(1)

def status_cmd(args):
    """現在の学期状況表示コマンド"""
    app = create_app()
    with app.app_context():
        active_semester = SemesterManager.get_active_semester()
        current_semester = SemesterManager.get_current_semester()
        
        print("=== 学期状況 ===")
        print(f"現在の日付: {datetime.now().date()}")
        
        if active_semester:
            print(f"アクティブな学期: {active_semester.name} ({active_semester.start_date} - {active_semester.end_date})")
        else:
            print("アクティブな学期: なし")
            
        if current_semester:
            print(f"日付に該当する学期: {current_semester.name} ({current_semester.start_date} - {current_semester.end_date})")
        else:
            print("日付に該当する学期: なし")
            
        if active_semester and current_semester:
            if active_semester.id == current_semester.id:
                print("状態: 正常（アクティブな学期と現在の学期が一致）")
            else:
                print("状態: 不一致（学期切り替えが必要かもしれません）")

def main():
    parser = argparse.ArgumentParser(description='学期管理CLI')
    subparsers = parser.add_subparsers(dest='command', help='利用可能なコマンド')

    # create コマンド
    create_parser = subparsers.add_parser('create', help='新しい学期を作成')
    create_parser.add_argument('name', help='学期名')
    create_parser.add_argument('start_date', help='開始日 (YYYY-MM-DD)')
    create_parser.add_argument('end_date', help='終了日 (YYYY-MM-DD)')
    create_parser.add_argument('--active', action='store_true', help='作成時にアクティブにする')
    create_parser.set_defaults(func=create_semester_cmd)

    # list コマンド
    list_parser = subparsers.add_parser('list', help='学期一覧を表示')
    list_parser.set_defaults(func=list_semesters_cmd)

    # activate コマンド
    activate_parser = subparsers.add_parser('activate', help='学期をアクティブにする')
    activate_parser.add_argument('semester_id', type=int, help='学期ID')
    activate_parser.set_defaults(func=activate_semester_cmd)

    # switch コマンド
    switch_parser = subparsers.add_parser('switch', help='学期を切り替える')
    switch_parser.add_argument('semester_id', type=int, help='切り替え先学期ID')
    switch_parser.add_argument('--no-migrate', dest='migrate_users', action='store_false', help='ユーザー移行をスキップ')
    switch_parser.add_argument('--force', action='store_true', help='確認プロンプトをスキップ')
    switch_parser.set_defaults(func=switch_semester_cmd, migrate_users=True)

    # auto-check コマンド
    auto_parser = subparsers.add_parser('auto-check', help='自動学期チェック・切り替え')
    auto_parser.set_defaults(func=auto_check_cmd)

    # migrate-users コマンド
    migrate_parser = subparsers.add_parser('migrate-users', help='ユーザーを手動で移行')
    migrate_parser.add_argument('--force', action='store_true', help='確認プロンプトをスキップ')
    migrate_parser.set_defaults(func=migrate_users_cmd)

    # status コマンド
    status_parser = subparsers.add_parser('status', help='現在の学期状況を表示')
    status_parser.set_defaults(func=status_cmd)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # コマンドの実行
    args.func(args)

if __name__ == '__main__':
    main()