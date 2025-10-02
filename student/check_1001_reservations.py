#!/usr/bin/env python3
"""
1001号車の予約件数を確認するスクリプト
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
from app import create_app
from app.database import db
from app.models.bus import Bus
from app.models.reservation import Reservation

def check_1001_reservations():
    app = create_app()
    with app.app_context():
        bus = Bus.query.filter_by(busid=1001).first()
        if not bus:
            print("1001号車が見つかりません")
            return
        count = Reservation.query.filter_by(bus_id=bus.id).count()
        print(f"1001号車の予約件数: {count}")

if __name__ == "__main__":
    check_1001_reservations()
