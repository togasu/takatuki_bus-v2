#!/usr/bin/env python3
"""
簡潔な予約シミュレーター

2分ごとにランダムで1-2件の予約を作成
"""

import sys
import time
import random
from datetime import datetime

# パスを追加
sys.path.append('/app')

# インポート
from app import create_app
from app.models.reservation import Reservation
from app.models.bus import Bus
from app.models.seat import Seat
from app.models.user import User
from app.database import db

def log(message):
    """ログ出力"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] 🎯 AutoSim: {message}")

def create_reservation():
    """1件の予約を作成"""
    try:
        app = create_app()
        with app.app_context():
            # ユーザーとバスを取得
            users = User.query.all()
            buses = Bus.query.filter_by(status=0).all()
            
            if not users or not buses:
                log("ユーザーまたはバスが不足")
                return False
            
            # ランダム選択
            user = random.choice(users)
            bus = random.choice(buses)
            
            # 未予約座席を探す
            reserved_seats = [r.seat_number for r in Reservation.query.filter_by(bus_id=bus.id).all()]
            available_seats = [s for s in Seat.query.filter_by(bus_id=bus.id).all() 
                              if s.number not in reserved_seats]
            
            if not available_seats:
                log(f"バス{bus.busid}に空席なし")
                return False
            
            seat = random.choice(available_seats)
            
            # 予約作成
            reservation = Reservation()
            reservation.seat_number = seat.number
            reservation.bus_id = bus.id
            reservation.user_id = user.id
            reservation.approved = random.choice([0, 1])
            reservation.reserved_time = datetime.now()
            
            db.session.add(reservation)
            db.session.commit()
            
            status = "承認済み" if reservation.approved == 1 else "未承認"
            log(f"✅ 予約: ユーザー{user.student_id} → バス{bus.busid} 座席{seat.number} ({status})")
            return True
            
    except Exception as e:
        log(f"❌ エラー: {e}")
        return False

def show_stats():
    """統計を表示"""
    try:
        app = create_app()
        with app.app_context():
            total = Reservation.query.count()
            approved = Reservation.query.filter_by(approved=1).count()
            pending = Reservation.query.filter_by(approved=0).count()
            log(f"📊 統計: 総{total}件, 承認済み{approved}件, 未承認{pending}件")
    except Exception as e:
        log(f"❌ 統計エラー: {e}")

def main():
    """メインループ"""
    log("🚀 シンプル予約シミュレーター開始")
    log("   - 2分サイクルで1-2件の予約作成")
    
    cycle = 0
    while True:
        try:
            cycle += 1
            log(f"🔄 サイクル {cycle} 開始")
            
            # 1-2件の予約を作成
            count = random.randint(1, 2)
            success = 0
            
            for i in range(count):
                if create_reservation():
                    success += 1
                time.sleep(random.randint(5, 15))  # 5-15秒の間隔
            
            log(f"📝 {success}/{count}件作成完了")
            show_stats()
            
            # 2分待機
            log("⏰ 2分待機...")
            time.sleep(120)
            
        except KeyboardInterrupt:
            log("🛑 停止シグナル受信")
            break
        except Exception as e:
            log(f"❌ メインループエラー: {e}")
            time.sleep(30)  # エラー時は30秒待機

    log("🏁 シミュレーター終了")

if __name__ == "__main__":
    main()