#!/usr/bin/env python3
"""
並行予約負荷テスト

500人の学生がほぼ同時に予約を試みた際のデータベースロック問題を検証するスクリプト
"""

import concurrent.futures
import threading
import time
import random
from datetime import datetime
from collections import defaultdict
from app import create_app
from app.models.reservation import Reservation
from app.models.bus import Bus
from app.models.seat import Seat
from app.models.user import User
from app.database import db

# グローバル統計
stats = {
    'success': 0,
    'failed': 0,
    'lock_errors': 0,
    'duplicate_errors': 0,
    'other_errors': 0,
    'total_time': 0,
    'errors': []
}
stats_lock = threading.Lock()

def now_jst():
    """JST時刻を取得"""
    return datetime.now()

def log_message(message):
    """ログ出力（タイムスタンプ付き）"""
    timestamp = now_jst().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")

def make_reservation(app, user_id, bus_id, seat_number, test_id):
    """
    単一の予約を試行
    
    Args:
        app: Flaskアプリケーションインスタンス
        user_id: ユーザーID
        bus_id: バスID
        seat_number: 座席番号
        test_id: テスト識別番号
    
    Returns:
        dict: 結果情報
    """
    start_time = time.time()
    result = {
        'test_id': test_id,
        'user_id': user_id,
        'bus_id': bus_id,
        'seat_number': seat_number,
        'success': False,
        'error': None,
        'duration': 0,
        'error_type': None
    }
    
    try:
        with app.app_context():
            # トランザクション開始
            # PostgreSQLの場合、row-levelロックを使用
            reservation = Reservation(
                seat_number=seat_number,
                user_id=user_id,
                bus_id=bus_id,
                approved=0,
                reserved_time=now_jst()
            )
            
            # 重複チェック（SELECT FOR UPDATE相当）
            existing = db.session.query(Reservation).filter(
                Reservation.bus_id == bus_id,
                Reservation.seat_number == seat_number
            ).with_for_update().first()
            
            if existing:
                result['error'] = f"座席{seat_number}は既に予約済み"
                result['error_type'] = 'duplicate'
            else:
                db.session.add(reservation)
                db.session.commit()
                result['success'] = True
                
    except Exception as e:
        error_msg = str(e).lower()
        result['error'] = str(e)
        
        # エラータイプの分類
        if 'lock' in error_msg or 'deadlock' in error_msg:
            result['error_type'] = 'lock'
        elif 'duplicate' in error_msg or 'unique' in error_msg:
            result['error_type'] = 'duplicate'
        else:
            result['error_type'] = 'other'
        
        try:
            db.session.rollback()
        except:
            pass
    
    finally:
        result['duration'] = time.time() - start_time
    
    return result

def update_stats(result):
    """統計情報を更新"""
    with stats_lock:
        stats['total_time'] += result['duration']
        
        if result['success']:
            stats['success'] += 1
        else:
            stats['failed'] += 1
            stats['errors'].append({
                'test_id': result['test_id'],
                'user_id': result['user_id'],
                'seat': result['seat_number'],
                'error': result['error'],
                'error_type': result['error_type']
            })
            
            if result['error_type'] == 'lock':
                stats['lock_errors'] += 1
            elif result['error_type'] == 'duplicate':
                stats['duplicate_errors'] += 1
            else:
                stats['other_errors'] += 1

def run_concurrent_test(num_users=500, max_workers=50, test_mode='same_seat'):
    """
    並行予約テストを実行
    
    Args:
        num_users: シミュレートするユーザー数
        max_workers: 並行実行する最大スレッド数
        test_mode: テストモード
            - 'same_seat': 全員が同じ座席を予約（最悪ケース）
            - 'different_seats': 異なる座席を予約（通常ケース）
            - 'random_seats': ランダムに座席を選択（現実的ケース）
    """
    
    log_message("=" * 80)
    log_message(f"🚌 並行予約負荷テスト開始")
    log_message(f"   ユーザー数: {num_users}")
    log_message(f"   並行スレッド数: {max_workers}")
    log_message(f"   テストモード: {test_mode}")
    log_message("=" * 80)
    
    app = create_app()
    
    # テスト用データの準備
    with app.app_context():
        # テストユーザーを取得
        users = User.query.filter(
            User.student_id.like('23009%')
        ).limit(num_users).all()
        
        if len(users) < num_users:
            log_message(f"⚠️  警告: {num_users}人必要ですが、{len(users)}人のユーザーしかいません")
            log_message(f"   テストユーザーを作成してください: python create_test_student.py")
            return
        
        # テスト用のバスを取得
        bus = Bus.query.filter(Bus.status == 0).first()
        if not bus:
            log_message("❌ エラー: 利用可能なバスが見つかりません")
            return
        
        # バスの情報を変数に格納（セッション外で使用するため）
        bus_id_value = bus.id
        bus_busid_value = bus.busid
        bus_seats_count = bus.seats
        
        log_message(f"✅ テスト用バス: バス{bus_busid_value} (ID: {bus_id_value})")
        log_message(f"✅ テストユーザー: {len(users)}人準備完了")
        
        # 既存の予約をクリア（テスト用）
        existing_count = Reservation.query.filter(
            Reservation.bus_id == bus_id_value
        ).delete()
        db.session.commit()
        
        if existing_count > 0:
            log_message(f"🗑️  既存予約 {existing_count}件をクリアしました")
        
        # ユーザー情報を辞書リストに変換（セッション外で使用するため）
        users_data = [{'student_id': u.student_id} for u in users]
    
    # バスの座席数とIDを取得（セッション外で使用するため）
    # テストケースの準備
    test_cases = []
    for i, user_data in enumerate(users_data):
        if test_mode == 'same_seat':
            # 全員が座席1を予約（最悪ケース）
            seat_number = 1
        elif test_mode == 'different_seats':
            # 異なる座席を予約（通常ケース）
            seat_number = (i % bus_seats_count) + 1
        else:  # random_seats
            # ランダムに座席を選択（現実的ケース）
            seat_number = random.randint(1, bus_seats_count)
        
        test_cases.append({
            'user_id': user_data['student_id'],
            'bus_id': bus_id_value,
            'seat_number': seat_number,
            'test_id': i + 1
        })
    
    log_message(f"\n🏁 テスト開始...\n")
    
    # 並行実行
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 全てのタスクをほぼ同時に投入
        futures = [
            executor.submit(
                make_reservation,
                app,
                tc['user_id'],
                tc['bus_id'],
                tc['seat_number'],
                tc['test_id']
            )
            for tc in test_cases
        ]
        
        # 結果を収集
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            update_stats(result)
            completed += 1
            
            # 進捗表示（10%ごと）
            if completed % (num_users // 10) == 0:
                progress = (completed / num_users) * 100
                log_message(f"   進捗: {progress:.1f}% ({completed}/{num_users})")
    
    total_time = time.time() - start_time
    
    # 結果の表示
    log_message("\n" + "=" * 80)
    log_message("📊 テスト結果")
    log_message("=" * 80)
    log_message(f"総実行時間: {total_time:.2f}秒")
    log_message(f"平均処理時間: {stats['total_time']/num_users:.3f}秒/予約")
    log_message(f"スループット: {num_users/total_time:.2f}予約/秒")
    log_message("")
    log_message(f"✅ 成功: {stats['success']}件 ({stats['success']/num_users*100:.1f}%)")
    log_message(f"❌ 失敗: {stats['failed']}件 ({stats['failed']/num_users*100:.1f}%)")
    log_message("")
    log_message(f"エラー内訳:")
    log_message(f"  🔒 ロックエラー: {stats['lock_errors']}件")
    log_message(f"  🔄 重複エラー: {stats['duplicate_errors']}件")
    log_message(f"  ⚠️  その他のエラー: {stats['other_errors']}件")
    
    # エラー詳細の表示（最初の10件）
    if stats['errors']:
        log_message("\n" + "-" * 80)
        log_message(f"エラー詳細（最初の10件）:")
        log_message("-" * 80)
        for i, error in enumerate(stats['errors'][:10]):
            log_message(f"{i+1}. [Test#{error['test_id']}] User:{error['user_id']}, "
                       f"Seat:{error['seat']}, Type:{error['error_type']}")
            log_message(f"   Error: {error['error'][:100]}")
    
    # データベースの最終状態を確認
    with app.app_context():
        final_count = Reservation.query.filter(
            Reservation.bus_id == bus_id_value
        ).count()
        log_message("\n" + "-" * 80)
        log_message(f"📋 最終的な予約数: {final_count}件")
        log_message("-" * 80)
        
        # 座席ごとの予約数を確認
        seat_counts = defaultdict(int)
        reservations = Reservation.query.filter(
            Reservation.bus_id == bus_id_value
        ).all()
        
        for res in reservations:
            seat_counts[res.seat_number] += 1
        
        # 重複予約がないか確認
        duplicates = {seat: count for seat, count in seat_counts.items() if count > 1}
        if duplicates:
            log_message("⚠️  警告: 重複予約が検出されました！")
            for seat, count in duplicates.items():
                log_message(f"   座席{seat}: {count}件の予約")
        else:
            log_message("✅ 重複予約なし: データベース整合性OK")
    
    log_message("=" * 80)
    log_message("🏁 テスト完了")
    log_message("=" * 80)

def main():
    """メイン処理"""
    import sys
    
    # デフォルト設定
    num_users = 500
    max_workers = 50
    test_mode = 'random_seats'
    
    # コマンドライン引数の処理
    if len(sys.argv) > 1:
        try:
            num_users = int(sys.argv[1])
        except ValueError:
            print(f"エラー: ユーザー数は整数で指定してください")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        try:
            max_workers = int(sys.argv[2])
        except ValueError:
            print(f"エラー: スレッド数は整数で指定してください")
            sys.exit(1)
    
    if len(sys.argv) > 3:
        test_mode = sys.argv[3]
        if test_mode not in ['same_seat', 'different_seats', 'random_seats']:
            print(f"エラー: テストモードは 'same_seat', 'different_seats', 'random_seats' のいずれかを指定してください")
            sys.exit(1)
    
    try:
        run_concurrent_test(num_users, max_workers, test_mode)
    except KeyboardInterrupt:
        print("\n\n⚠️  テストが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                       並行予約負荷テストツール                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

使用方法:
    python concurrent_reservation_test.py [ユーザー数] [スレッド数] [モード]

引数:
    ユーザー数: シミュレートするユーザー数（デフォルト: 500）
    スレッド数: 並行実行する最大スレッド数（デフォルト: 50）
    モード: テストモード（デフォルト: random_seats）
        - same_seat: 全員が同じ座席を予約（最悪ケース）
        - different_seats: 異なる座席を予約（通常ケース）
        - random_seats: ランダムに座席を選択（現実的ケース）

例:
    python concurrent_reservation_test.py 500 50 random_seats
    python concurrent_reservation_test.py 1000 100 same_seat
    python concurrent_reservation_test.py 100 10 different_seats

""")
    main()
