#!/usr/bin/env python3
"""
Student サービス用のテストバス・座席作成スクリプト
デバッグ用のバスと座席データを作成します
"""

import sys
import os
from datetime import datetime, timedelta

# Flaskアプリケーションのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.database import db
from app.models.bus import Bus
from app.models.seat import Seat

def create_debug_buses():
    """デバッグ用のバスと座席を作成"""
    app = create_app()
    
    with app.app_context():
        try:
            # 現在時刻を基準にした出発時刻を設定
            base_time = datetime.utcnow()
            
            # デバッグ用バスのデータ（busidは1～4の号車番号）
            debug_buses = [
                {
                    'busid': 1,  # 1号車
                    'departure_time': base_time + timedelta(hours=2),  # 2時間後
                    'seats': 27,
                    'ud': 0,  # 上り
                    'bookable_time': 60,  # 予約可能時間（分）
                    'status': 0  # アクティブ
                },
                {
                    'busid': 2,  # 2号車
                    'departure_time': base_time + timedelta(hours=4),  # 4時間後
                    'seats': 27,
                    'ud': 1,  # 下り
                    'bookable_time': 60,
                    'status': 0
                },
                {
                    'busid': 3,  # 3号車
                    'departure_time': base_time + timedelta(hours=6),  # 6時間後
                    'seats': 27,
                    'ud': 0,  # 上り
                    'bookable_time': 90,
                    'status': 0
                },
                {
                    'busid': 4,  # 4号車
                    'departure_time': base_time + timedelta(hours=8),  # 8時間後
                    'seats': 27,
                    'ud': 1,  # 下り
                    'bookable_time': 90,
                    'status': 0
                },
                {
                    'busid': 1,  # 1号車（翌日）
                    'departure_time': base_time + timedelta(days=1),  # 翌日
                    'seats': 27,
                    'ud': 0,  # 上り
                    'bookable_time': 120,
                    'status': 0
                },
                {
                    'busid': 2,  # 2号車（翌日）
                    'departure_time': base_time + timedelta(days=1, hours=2),  # 翌日2時間後
                    'seats': 27,
                    'ud': 1,  # 下り
                    'bookable_time': 120,
                    'status': 0
                }
            ]
            
            created_buses_count = 0
            created_seats_count = 0
            
            for bus_data in debug_buses:
                # 既存バスの確認（同じbusidと出発時刻の組み合わせ）
                existing_bus = Bus.query.filter(
                    Bus.busid == bus_data['busid'],
                    Bus.departure_time == bus_data['departure_time']
                ).first()
                
                if existing_bus:
                    departure_str = bus_data['departure_time'].strftime('%Y-%m-%d %H:%M')
                    print(f"⚠️  バス ({bus_data['busid']}号車 {departure_str}発) は既に存在します")
                    continue
                
                # 新しいバスを作成
                new_bus = Bus(
                    busid=bus_data['busid'],
                    departure_time=bus_data['departure_time'],
                    seats=bus_data['seats'],
                    ud=bus_data['ud'],
                    bookable_time=bus_data['bookable_time'],
                    status=bus_data['status']
                )
                
                db.session.add(new_bus)
                db.session.flush()  # IDを取得するため
                
                created_buses_count += 1
                direction = "上り" if bus_data['ud'] == 0 else "下り"
                print(f"✅ デバッグバス作成: {bus_data['busid']}号車 ({direction}, {bus_data['seats']}席)")
                
                # バスの座席を作成
                for seat_number in range(1, bus_data['seats'] + 1):
                        new_seat = Seat(
                            number=seat_number,
                            bus_id=new_bus.id
                        )
                        db.session.add(new_seat)
                        created_seats_count += 1
                
                print(f"   └ 座席 {bus_data['seats']} 席を作成")
            
            if created_buses_count > 0:
                db.session.commit()
                print(f"\n🎉 {created_buses_count}台のデバッグバスと{created_seats_count}席の座席を作成しました！")
                print("📝 作成されたバス:")
                for bus_data in debug_buses:
                    direction = "上り" if bus_data['ud'] == 0 else "下り"
                    departure_str = bus_data['departure_time'].strftime('%Y-%m-%d %H:%M')
                    print(f"   - {bus_data['busid']}号車: {direction} ({departure_str}出発, {bus_data['seats']}席)")
            else:
                print("ℹ️  新規作成されたバスはありません")
                
        except Exception as e:
            print(f"❌ エラーが発生しました: {str(e)}")
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    create_debug_buses()
