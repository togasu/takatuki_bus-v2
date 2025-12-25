#!/usr/bin/env python3
"""
シンプル予約シミュレーター

2分ごとに1-3件の予約を作成し、統計データの動作確認をする
"""

import sys
import time
import random
from datetime import datetime
import signal

sys.path.append('/app')
from app import create_app
from app.models.reservation import Reservation
from app.models.bus import Bus
from app.models.seat import Seat
from app.models.user import User
from app.database import db

class SimpleReservationSimulator:
    def __init__(self):
        self.app = create_app()
        self.running = False
        
    def log(self, message):
        """ログ出力"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] 🎯 SimpleSimulator: {message}")
        
    def create_random_reservation(self):
        """ランダムで予約を作成"""
        try:
            with self.app.app_context():
                users = User.query.all()
                buses = Bus.query.filter_by(status=0).all()  # 運行中のバス
                
                if not users or not buses:
                    self.log("利用可能なユーザーまたはバスがありません")
                    return False
                
                # ランダム選択
                user = random.choice(users)
                bus = random.choice(buses)
                
                # そのバスの未予約座席を取得
                reserved_seats = [r.seat_number for r in Reservation.query.filter_by(bus_id=bus.id).all()]
                available_seats = Seat.query.filter(
                    Seat.bus_id == bus.id,
                    ~Seat.number.in_(reserved_seats)
                ).all()
                
                if not available_seats:
                    self.log(f"バス{bus.busid}に利用可能な座席がありません")
                    return False
                
                seat = random.choice(available_seats)
                
                # 予約作成
                reservation = Reservation()
                reservation.seat_number = seat.number
                reservation.bus_id = bus.id
                reservation.user_id = user.student_id  # user.idではなくstudent_idを使用
                reservation.approved = random.choice([0, 1])  # ランダムで承認状態
                reservation.reserved_time = datetime.now()
                
                db.session.add(reservation)
                db.session.commit()
                
                status = "承認済み" if reservation.approved == 1 else "未承認"
                self.log(f"✅ 予約作成: ユーザー{user.student_id} → バス{bus.busid} 座席{seat.number} ({status})")
                return True
                
        except Exception as e:
            self.log(f"❌ 予約作成エラー: {e}")
            return False
            
    def show_statistics(self):
        """統計情報を表示"""
        try:
            with self.app.app_context():
                total = Reservation.query.count()
                approved = Reservation.query.filter_by(approved=1).count()
                pending = Reservation.query.filter_by(approved=0).count()
                
                self.log(f"📊 統計: 総予約{total}件, 承認済み{approved}件, 未承認{pending}件")
                
        except Exception as e:
            self.log(f"❌ 統計取得エラー: {e}")
            
    def run_cycle(self):
        """1サイクルの実行"""
        self.log("🔄 新サイクル開始")
        
        # 1-3件の予約を作成
        count = random.randint(1, 3)
        success_count = 0
        
        for i in range(count):
            if self.create_random_reservation():
                success_count += 1
            time.sleep(1)  # 1秒待機
            
        self.log(f"✅ {success_count}/{count}件の予約を作成")
        self.show_statistics()
        
    def start(self):
        """シミュレーター開始"""
        self.running = True
        self.log("🚀 シンプル予約シミュレーター開始")
        self.log("   - 2分ごとに1-3件の予約を作成")
        self.log("   - Ctrl+C で停止")
        
        try:
            while self.running:
                self.run_cycle()
                
                # 2分待機
                for i in range(120):  # 120秒 = 2分
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            self.log("🛑 キーボード割り込みを受信")
        finally:
            self.running = False
            self.log("🏁 シミュレーター停止")
            
    def stop(self):
        """シミュレーター停止"""
        self.running = False

# グローバル変数
simulator = None

def signal_handler(signum, frame):
    """シグナルハンドラー"""
    global simulator
    if simulator:
        simulator.stop()
    sys.exit(0)

if __name__ == "__main__":
    simulator = SimpleReservationSimulator()
    
    # シグナルハンドラーを設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        simulator.start()
    except Exception as e:
        print(f"❌ シミュレーターエラー: {e}")
        sys.exit(1)