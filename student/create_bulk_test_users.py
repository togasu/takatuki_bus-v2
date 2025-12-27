#!/usr/bin/env python3
"""
大量テストユーザー作成スクリプト
並行予約テスト用に多数のテストユーザーを作成します
"""

import sys
from app import create_app
from app.database import db
from app.models.user import User
from datetime import datetime

def create_bulk_test_users(count=500):
    """
    大量のテストユーザーを作成
    
    Args:
        count: 作成するユーザー数（デフォルト: 500）
    """
    app = create_app()
    
    with app.app_context():
        try:
            print(f"🚀 {count}人のテストユーザーを作成します...")
            
            # 既存のテストユーザー数を確認
            existing_count = User.query.filter(
                User.student_id.like('23009%')
            ).count()
            
            print(f"📊 既存のテストユーザー: {existing_count}人")
            
            created_count = 0
            skipped_count = 0
            
            # 230090000 から始まる学籍番号で作成
            base_student_id = 230090000
            
            for i in range(count):
                student_id = str(base_student_id + i)
                
                # 既存ユーザーの確認
                existing_user = User.query.filter(
                    User.student_id == student_id
                ).first()
                
                if existing_user:
                    skipped_count += 1
                    continue
                
                # 新しいユーザーを作成
                new_user = User(
                    student_id=student_id,
                    idm_univ=f'TEST_UNIV_{i:06d}',
                    idm_bus=f'TEST_BUS_{i:06d}',
                    regist_now_time=datetime.utcnow()
                )
                
                db.session.add(new_user)
                created_count += 1
                
                # 100人ごとにコミット
                if created_count % 100 == 0:
                    db.session.commit()
                    print(f"   ✅ {created_count}人作成完了...")
            
            # 最後のコミット
            if created_count % 100 != 0:
                db.session.commit()
            
            # 最終確認
            final_count = User.query.filter(
                User.student_id.like('23009%')
            ).count()
            
            print(f"\n{'='*60}")
            print(f"🎉 テストユーザー作成完了！")
            print(f"{'='*60}")
            print(f"新規作成: {created_count}人")
            print(f"スキップ: {skipped_count}人 (既存)")
            print(f"総数: {final_count}人")
            print(f"{'='*60}")
            print(f"\n📝 学籍番号範囲: {base_student_id} ~ {base_student_id + count - 1}")
            print(f"IDM_UNIV範囲: TEST_UNIV_000000 ~ TEST_UNIV_{count-1:06d}")
            print(f"IDM_BUS範囲: TEST_BUS_000000 ~ TEST_BUS_{count-1:06d}")
            
        except Exception as e:
            print(f"\n❌ エラーが発生しました: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            sys.exit(1)

def main():
    """メイン処理"""
    count = 500
    
    # コマンドライン引数の処理
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            print(f"❌ エラー: ユーザー数は整数で指定してください")
            sys.exit(1)
    
    create_bulk_test_users(count)

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    大量テストユーザー作成ツール                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

使用方法:
    python create_bulk_test_users.py [ユーザー数]

引数:
    ユーザー数: 作成するユーザー数（デフォルト: 500）

例:
    python create_bulk_test_users.py 500
    python create_bulk_test_users.py 1000

注意:
    - 学籍番号は 230090000 から始まります
    - 既存のユーザーはスキップされます
    - IDM_UNIVとIDM_BUSは自動生成されます

""")
    main()
