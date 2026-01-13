#!/usr/bin/env python3
"""
重複予約クリーンアップスクリプト

Reservationテーブル内の重複データ（同じバスの同じ座席に複数の予約）を削除します。
最も新しい予約（IDが最大のもの）を残し、それ以外を削除します。

実行方法:
    docker exec -it takatuki_bus-v2-student-1 python clean_duplicate_reservations.py
"""

import sys
from app import create_app
from app.database import db
from app.models.reservation import Reservation
from sqlalchemy import text, func

def find_duplicates():
    """重複予約を検出"""
    app = create_app()
    
    with app.app_context():
        try:
            # 重複している(bus_id, seat_number)の組み合わせを取得
            duplicates_query = db.session.query(
                Reservation.bus_id,
                Reservation.seat_number,
                func.count(Reservation.id).label('count'),
                func.max(Reservation.id).label('latest_id')
            ).group_by(
                Reservation.bus_id,
                Reservation.seat_number
            ).having(
                func.count(Reservation.id) > 1
            ).all()
            
            return duplicates_query
            
        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            return []

def show_duplicate_details():
    """重複データの詳細を表示"""
    app = create_app()
    
    with app.app_context():
        try:
            duplicates = find_duplicates()
            
            if not duplicates:
                print("✅ 重複データは見つかりませんでした")
                return False
            
            print(f"\n⚠️  {len(duplicates)}件の重複が検出されました\n")
            print("-" * 80)
            
            total_to_delete = 0
            
            for dup in duplicates:
                bus_id, seat_number, count, latest_id = dup
                
                # 該当する全ての予約を取得
                reservations = db.session.query(Reservation).filter(
                    Reservation.bus_id == bus_id,
                    Reservation.seat_number == seat_number
                ).order_by(Reservation.id.desc()).all()
                
                print(f"\n📋 バスID: {bus_id}, 座席: {seat_number} ({count}件の予約)")
                print(f"   削除対象: {count - 1}件")
                
                for i, res in enumerate(reservations):
                    status = "✅ 保持" if res.id == latest_id else "❌ 削除予定"
                    approved_status = "承認済み" if res.approved == 1 else "未承認"
                    print(f"   {status} - ID: {res.id}, ユーザー: {res.user_id}, "
                          f"予約時刻: {res.reserved_time}, {approved_status}")
                
                total_to_delete += (count - 1)
            
            print("\n" + "-" * 80)
            print(f"\n📊 削除予定合計: {total_to_delete}件")
            
            return True
            
        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def clean_duplicates(dry_run=True):
    """重複予約を削除（最新のもの以外）"""
    app = create_app()
    
    with app.app_context():
        try:
            duplicates = find_duplicates()
            
            if not duplicates:
                print("✅ 重複データは見つかりませんでした")
                return
            
            if dry_run:
                print("\n🔍 ドライランモード（実際には削除されません）\n")
            else:
                print("\n⚠️  実行モード（データを削除します）\n")
            
            deleted_count = 0
            
            for dup in duplicates:
                bus_id, seat_number, count, latest_id = dup
                
                # 最新以外の予約を取得
                old_reservations = db.session.query(Reservation).filter(
                    Reservation.bus_id == bus_id,
                    Reservation.seat_number == seat_number,
                    Reservation.id != latest_id
                ).all()
                
                for res in old_reservations:
                    if dry_run:
                        print(f"[ドライラン] 削除: ID={res.id}, "
                              f"バス={bus_id}, 座席={seat_number}, "
                              f"ユーザー={res.user_id}")
                    else:
                        print(f"削除中: ID={res.id}, "
                              f"バス={bus_id}, 座席={seat_number}, "
                              f"ユーザー={res.user_id}")
                        db.session.delete(res)
                    
                    deleted_count += 1
            
            if not dry_run:
                db.session.commit()
                print(f"\n✅ {deleted_count}件の重複予約を削除しました")
            else:
                print(f"\n📊 {deleted_count}件の重複予約が見つかりました")
                print("\n実際に削除するには --execute オプションを使用してください")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ エラーが発生しました: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='重複予約をクリーンアップ')
    parser.add_argument('--execute', action='store_true', 
                       help='実際に削除を実行（指定しない場合はドライラン）')
    parser.add_argument('--show', action='store_true',
                       help='重複データの詳細を表示のみ')
    args = parser.parse_args()
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  重複予約クリーンアップツール                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

このスクリプトは、同じバスの同じ座席に複数の予約がある場合、
最も新しい予約（IDが最大のもの）を残し、それ以外を削除します。

使用方法:
    python clean_duplicate_reservations.py              # ドライラン（削除しない）
    python clean_duplicate_reservations.py --show       # 重複データの詳細を表示
    python clean_duplicate_reservations.py --execute    # 実際に削除

""")
    
    if args.show:
        print("=" * 80)
        print("📋 重複データの詳細")
        print("=" * 80)
        show_duplicate_details()
    else:
        print("=" * 80)
        print("🔍 重複予約を検索中...")
        print("=" * 80)
        clean_duplicates(dry_run=not args.execute)

if __name__ == "__main__":
    main()
