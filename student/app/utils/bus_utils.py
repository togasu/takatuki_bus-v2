from datetime import datetime
from flask import current_app
from ..models.bus import db, Bus
from ..models.seat import Seat

def add_bus_and_seats(ud, bus_time_object, new_busid):
    """kanriで入力されたものをテーブルに入れている"""
    with current_app.app_context():
        print(bus_time_object)

        # バスの正席処理　proj_takatukibusの荻野先生の過去発言参照
        max_seat = 27

        # 新しいバスを作成
        new_bus = Bus(busid=new_busid, departure_time=bus_time_object, seats=max_seat, ud=ud, bookable_time=0)
        db.session.add(new_bus)
        db.session.commit()

        nwbid = Bus.query.filter_by(id=new_bus.id).first()
        # バスに関連する22個のシートを作成
        for seat_number in range(1, max_seat + 1):
            new_seat = Seat(number=seat_number, bus_id=nwbid.id)
            db.session.add(new_seat)
            db.session.commit()
        return nwbid.id
