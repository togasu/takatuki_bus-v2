#!/usr/bin/env python3
"""
一意制約追加マイグレーション

Reservationテーブルに(bus_id, seat_number)の一意制約を追加して、
並行予約時の重複予約を防止します。

実行方法:
    docker exec -it takatuki_bus-v2-student-1 python add_unique_constraint_reservation.py
"""

import sys
from app import create_app
from app.database import db
from sqlalchemy import text

def add_unique_constraint():
    """Reservationテーブルに一意制約を追加"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=" * 70)
            print("🔧 Reservationテーブルに一意制約を追加します")
            print("=" * 70)
            
            # 既存の制約を確認
            check_constraint_sql = """
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'Reservation' 
            AND constraint_name = 'uq_bus_seat'
            """
            
            result = db.session.execute(text(check_constraint_sql)).fetchone()
            
            if result:
                print("ℹ️  一意制約 'uq_bus_seat' は既に存在します")
                print("✅ マイグレーション完了（変更なし）")
                return
            
            # 既存の重複データを確認
            print("\n📊 既存の重複データを確認中...")
            duplicate_check_sql = """
            SELECT bus_id, seat_number, COUNT(*) as count
            FROM "Reservation"
            GROUP BY bus_id, seat_number
            HAVING COUNT(*) > 1
            """
            
            duplicates = db.session.execute(text(duplicate_check_sql)).fetchall()
            
            if duplicates:
                print(f"\n⚠️  警告: {len(duplicates)}件の重複データが検出されました")
                print("\n重複データの詳細:")
                for dup in duplicates:
                    print(f"  - バスID {dup[0]}, 座席 {dup[1]}: {dup[2]}件の予約")
                
                print("\n❌ エラー: 一意制約を追加する前に重複データを削除してください")
                print("\n重複データを削除する方法:")
                print("  1. 手動で削除")
                print("  2. 以下のコマンドで最新以外を削除:")
                print("     python clean_duplicate_reservations.py")
                return
            
            print("✅ 重複データなし")
            
            # 一意制約を追加
            print("\n🔨 一意制約を追加中...")
            add_constraint_sql = """
            ALTER TABLE "Reservation"
            ADD CONSTRAINT uq_bus_seat UNIQUE (bus_id, seat_number)
            """
            
            db.session.execute(text(add_constraint_sql))
            db.session.commit()
            
            print("✅ 一意制約 'uq_bus_seat' を追加しました")
            
            # 制約が正しく追加されたか確認
            result = db.session.execute(text(check_constraint_sql)).fetchone()
            if result:
                print("\n✅ マイグレーション成功！")
                print("\n📝 追加された制約:")
                print(f"  - テーブル: Reservation")
                print(f"  - 制約名: uq_bus_seat")
                print(f"  - カラム: (bus_id, seat_number)")
                print(f"  - 効果: 同じバスの同じ座席に複数の予約を防止")
            else:
                print("\n⚠️  警告: 制約の確認に失敗しました")
            
            print("=" * 70)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ エラーが発生しました: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

def check_constraint_status():
    """現在の制約状態を確認"""
    app = create_app()
    
    with app.app_context():
        try:
            print("\n" + "=" * 70)
            print("📊 Reservationテーブルの制約情報")
            print("=" * 70)
            
            constraint_sql = """
            SELECT 
                constraint_name,
                constraint_type
            FROM information_schema.table_constraints 
            WHERE table_name = 'Reservation'
            ORDER BY constraint_type, constraint_name
            """
            
            constraints = db.session.execute(text(constraint_sql)).fetchall()
            
            if constraints:
                print("\n現在の制約:")
                for constraint in constraints:
                    constraint_type_map = {
                        'PRIMARY KEY': '🔑 主キー',
                        'FOREIGN KEY': '🔗 外部キー',
                        'UNIQUE': '🎯 一意制約',
                        'CHECK': '✓ チェック制約'
                    }
                    type_icon = constraint_type_map.get(constraint[1], '📌')
                    print(f"  {type_icon} {constraint[0]} ({constraint[1]})")
            else:
                print("\n制約が見つかりません")
            
            print("=" * 70)
            
        except Exception as e:
            print(f"\n❌ エラー: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Reservationテーブルに一意制約を追加')
    parser.add_argument('--check', action='store_true', help='制約の状態を確認のみ')
    args = parser.parse_args()
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║           Reservation一意制約追加マイグレーション                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    if args.check:
        check_constraint_status()
    else:
        add_unique_constraint()
        check_constraint_status()
