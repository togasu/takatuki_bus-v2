#!/usr/bin/env python3
"""
自動予約シミュレーター

10分ごとにランダムで予約を作成し、5分後にランダムで承認済みにする検証スクリプト
統計データの動作確認とリアルタイム更新のテストに使用
"""

import random
import time
import threading
import signal
import sys
from datetime import datetime, timedelta
from app import create_app
from app.models.reservation import Reservation
from app.models.bus import Bus
from app.models.seat import Seat
from app.models.user import User
from app.database import db

def now_jst():
    """JST時刻を取得（フォールバック実装）"""
    return datetime.now()

class ReservationSimulator:
    def __init__(self):
        self.app = create_app()
        self.running = False
        self.pending_approvals = []  # 5分後に承認予定のリスト
        
    def log(self, message):
        """ログ出力"""
        timestamp = now_jst().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] 🎯 Simulator: {message}")
        
    def get_available_users(self):
        """利用可能なユーザー一覧を取得"""
        with self.app.app_context():
            users = User.query.filter(
                User.student_id.like('23009%')  # テスト用ユーザー
            ).all()
            return users
            
    def get_available_buses_and_seats(self):
        """利用可能なバスと座席を取得"""
        with self.app.app_context():
            buses = Bus.query.filter(
                Bus.status == 0  # 運行中のバス（0=運行中）
            ).all()
            
            available_seats = []
            for bus in buses:
                # 予約可能な座席を取得
                seats = Seat.query.filter(
                    Seat.bus_id == bus.id
                ).all()
                
                for seat in seats:
                    # 既に予約されていない座席のみ
                    existing_reservation = Reservation.query.filter(
                        Reservation.seat_number == seat.number,
                        Reservation.bus_id == bus.id
                    ).first()
                    
                    if not existing_reservation:
                        available_seats.append({
                            'bus': bus,
                            'seat': seat
                        })
            
            return available_seats
            
    def create_random_reservation(self):
        """ランダムで予約を作成"""
        try:
            with self.app.app_context():
                users = self.get_available_users()
                available_seats = self.get_available_buses_and_seats()
                
                if not users or not available_seats:
                    self.log("利用可能なユーザーまたは座席がありません")
                    return None
                    
                # ランダム選択
                user = random.choice(users)
                seat_info = random.choice(available_seats)
                bus = seat_info['bus']
                seat = seat_info['seat']
                
                # 予約作成（初期状態は未承認）
                reservation = Reservation()
                reservation.seat_number = seat.number
                reservation.bus_id = bus.id
                reservation.user_id = user.id
                reservation.approved = 0  # 未承認状態
                reservation.reserved_time = now_jst()
                
                db.session.add(reservation)
                db.session.commit()
                
                self.log(f"✅ 予約作成: {user.student_id} → バス{bus.busid} 座席{seat.number}")
                
                # 5分後の承認用にスケジュール
                approval_time = now_jst() + timedelta(minutes=5)
                self.pending_approvals.append({
                    'reservation_id': reservation.id,
                    'approval_time': approval_time,
                    'student_id': user.student_id,
                    'bus_name': f"バス{bus.busid}",
                    'seat_number': seat.number
                })
                
                return reservation
                
        except Exception as e:
            self.log(f"❌ 予約作成エラー: {e}")
            return None
            
    def process_pending_approvals(self):
        """5分後の承認処理"""
        current_time = now_jst()
        completed_approvals = []
        
        for approval in self.pending_approvals:
            if current_time >= approval['approval_time']:
                try:
                    with self.app.app_context():
                        reservation = Reservation.query.get(approval['reservation_id'])
                        if reservation and reservation.approved == 0:
                            # ランダムで承認するかどうか決定（80%の確率で承認）
                            if random.random() < 0.8:
                                reservation.approved = 1
                                db.session.commit()
                                
                                self.log(f"🚌 承認完了: {approval['student_id']} → {approval['bus_name']} 座席{approval['seat_number']}")
                            else:
                                self.log(f"⏰ 承認見送り: {approval['student_id']} → {approval['bus_name']} 座席{approval['seat_number']}")
                                
                        completed_approvals.append(approval)
                        
                except Exception as e:
                    self.log(f"❌ 承認処理エラー: {e}")
                    completed_approvals.append(approval)
        
        # 完了した承認予定を削除
        for approval in completed_approvals:
            self.pending_approvals.remove(approval)
            
    def create_random_cancellation(self):
        """ランダムでキャンセルを作成（削除）"""
        try:
            with self.app.app_context():
                # 今日の未承認予約を取得
                reservations = Reservation.query.filter(
                    Reservation.approved == 0
                ).all()
                
                if not reservations:
                    return None
                    
                # ランダムでキャンセル（20%の確率）
                if random.random() < 0.2 and reservations:
                    reservation = random.choice(reservations)
                    
                    user = User.query.get(reservation.user_id)
                    bus = Bus.query.get(reservation.bus_id)
                    
                    # 予約を削除（キャンセル扱い）
                    db.session.delete(reservation)
                    db.session.commit()
                    
                    self.log(f"❌ キャンセル: {user.student_id if user else 'Unknown'} → バス{bus.busid if bus else 'Unknown'} 座席{reservation.seat_number}")
                    return reservation
                    
        except Exception as e:
            self.log(f"❌ キャンセル処理エラー: {e}")
            return None
            
    def run_cycle(self):
        """1サイクルの実行（予約作成 + 承認処理 + キャンセル処理）"""
        self.log("🔄 新しいサイクル開始")
        
        # 1. 5分後の承認処理
        self.process_pending_approvals()
        
        # 2. 新しい予約作成（1-3件）
        reservation_count = random.randint(1, 3)
        for _ in range(reservation_count):
            self.create_random_reservation()
            time.sleep(random.uniform(1, 3))  # 予約間に少し間隔を空ける
            
        # 3. ランダムキャンセル
        self.create_random_cancellation()
        
        # 4. 統計情報を表示
        with self.app.app_context():
            active_reservations = Reservation.query.filter(
                Reservation.approved == 0
            ).count()
            
            approved_reservations = Reservation.query.filter(
                Reservation.approved == 1
            ).count()
            
            pending_approvals = len(self.pending_approvals)
            
            self.log(f"📊 統計: 未承認予約{active_reservations}件, 承認済み{approved_reservations}件, 承認予定{pending_approvals}件")
            
    def start(self):
        """シミュレーター開始"""
        self.running = True
        self.log("🚀 予約シミュレーター開始")
        self.log("   - 2分ごとに1-3件の予約を作成")
        self.log("   - 予約の80%が5分後に承認")
        self.log("   - 20%の確率でランダムキャンセル")
        self.log("   - Ctrl+C で停止")
        
        try:
            while self.running:
                self.run_cycle()
                
                # 2分待機（デバッグ時は短縮可能）
                wait_time = 120  # 2分 = 120秒
                # デバッグ用: 環境変数でサイクル時間を短縮可能
                import os
                debug_cycle = os.environ.get('SIMULATOR_CYCLE_SECONDS')
                if debug_cycle:
                    wait_time = int(debug_cycle)
                    self.log(f"⚡ デバッグモード: {wait_time}秒サイクル")
                
                for i in range(wait_time):
                    if not self.running:
                        break
                    time.sleep(1)
                    
                    # 30秒ごとに承認処理をチェック
                    if i % 30 == 0:
                        self.process_pending_approvals()
                        
        except KeyboardInterrupt:
            self.log("🛑 キーボード割り込みを受信")
        finally:
            self.running = False
            self.log("🏁 予約シミュレーター停止")
            
    def stop(self):
        """シミュレーター停止"""
        self.running = False

def signal_handler(signum, frame):
    """シグナルハンドラー"""
    print("\n🛑 停止シグナルを受信しました...")
    simulator.stop()
    sys.exit(0)

if __name__ == "__main__":
    simulator = ReservationSimulator()
    
    # シグナルハンドラーを設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        simulator.start()
    except Exception as e:
        print(f"❌ シミュレーターエラー: {e}")
        sys.exit(1)