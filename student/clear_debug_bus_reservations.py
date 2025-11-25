#!/usr/bin/env python3
"""
デバッグバスの予約を全て削除し、全席空席状態にするスクリプト
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
from app import create_app
from app.database import db
from app.models.bus import Bus
from app.models.reservation import Reservation

def clear_debug_bus_reservations():
    app = create_app()
    with app.app_context():
        debug_busids = [1001, 1002, 1003, 1004, 1005, 1006]
        buses = Bus.query.filter(Bus.busid.in_(debug_busids)).all()
        bus_ids = [bus.id for bus in buses]
        deleted_count = 0
        if bus_ids:
            deleted_count = Reservation.query.filter(Reservation.bus_id.in_(bus_ids)).delete(synchronize_session=False)
            db.session.commit()
        print(f"{deleted_count} 件の予約を削除しました（全席空席化）")

if __name__ == "__main__":
    clear_debug_bus_reservations()
