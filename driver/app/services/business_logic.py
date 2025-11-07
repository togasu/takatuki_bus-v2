"""ドライバーシステムのビジネスロジック"""

from datetime import datetime, timedelta
from app.models import Bus, Seat, Reservation, Driver, QA
from app.database import db
from app.utils.helper_functions import yukisaki, gakusei
import json
import logging

logger = logging.getLogger('sojo-bus-log')


class BusService:
    """バス関連のビジネスロジック"""
    
    @staticmethod
    def get_upcoming_buses(bus_number, limit=5):
        """指定した号車の今後のバス便を取得"""
        now = datetime.now()
        return db.session.query(Bus).filter(
            Bus.departure_time > now,
            Bus.busid == bus_number
        ).order_by(Bus.departure_time).limit(limit).all()
    
    @staticmethod
    def get_next_bus(bus_number):
        """指定した号車の次のバス便を取得"""
        now = datetime.now()
        return db.session.query(Bus).filter(
            Bus.departure_time > now,
            Bus.busid == bus_number
        ).first()
    
    @staticmethod
    def get_second_bus(bus_number, first_bus_time):
        """指定した号車の2番目のバス便を取得"""
        return db.session.query(Bus).filter(
            Bus.departure_time > first_bus_time,
            Bus.busid == bus_number
        ).first()
    
    @staticmethod
    def register_bus_operation(bus_info):
        """バス運行情報を登録"""
        bus_id = bus_info["busid"]
        departure_time = bus_info["departure_time"]
        
        with open(f'../yoyaku_system/bus{bus_id}.json', 'w') as file:
            json.dump(bus_info, file)
            logger.info(f"success to register unten bus {bus_id}, departure_time {departure_time} bus_id {bus_id}")
    
    @staticmethod
    def get_buses_by_date_and_direction(date, ud):
        """日付と方向でバス便を取得"""
        today = datetime.now().date()
        nextday = today + timedelta(days=1)
        
        buses = []
        if ud == "高槻キャンパス":
            if date == today:
                buses = db.session.query(Bus).filter_by(ud=0).filter(
                    Bus.departure_time > today, 
                    Bus.departure_time < nextday
                ).all()
            elif date == nextday:
                buses = db.session.query(Bus).filter_by(ud=0).filter(
                    Bus.departure_time > nextday, 
                    Bus.departure_time < datetime.now() + timedelta(days=2)
                ).all()
        elif ud == "高槻駅":
            if date == today:
                buses = db.session.query(Bus).filter_by(ud=1).filter(
                    Bus.departure_time > today, 
                    Bus.departure_time < nextday
                ).all()
            elif date == nextday:
                buses = db.session.query(Bus).filter_by(ud=1).filter(
                    Bus.departure_time > nextday, 
                    Bus.departure_time < datetime.now() + timedelta(days=2)
                ).all()
        
        return buses


class SeatService:
    """座席関連のビジネスロジック"""
    
    @staticmethod
    def get_seats_with_reservations(bus_id):
        """指定したバスの座席と予約情報を取得"""
        seatall = db.session.query(Seat).filter_by(bus_id=bus_id).all()
        seats = []
        
        for seat in seatall:
            reserved = db.session.query(Reservation).filter_by(
                seat_number=seat.number, 
                bus_id=bus_id
            ).first()
            
            if reserved:
                seats.append({
                    "number": seat.number,
                    "reserved": 1,
                    "approved": reserved.approved,
                    "username": gakusei(str(reserved.user_id))
                })
            else:
                seats.append({
                    "number": seat.number,
                    "reserved": 0,
                    "approved": 0,
                    "username": "none"
                })
        
        return seats
    
    @staticmethod
    def approve_reservations(bus_id, seat_ids):
        """座席の予約を承認"""
        not_allowed = []
        
        for seat_id in seat_ids:
            seat = db.session.query(Seat).filter_by(number=seat_id, bus_id=bus_id).first()
            if seat:
                reserved = db.session.query(Reservation).filter_by(
                    seat_number=seat.number, 
                    bus_id=bus_id
                ).first()
                
                if reserved:
                    if reserved.approved == 1:
                        not_allowed.append(seat_id)
                    else:
                        reserved.approved = 1
                        logger.info(f"success to approve reservation: bus_id {bus_id}, seat {seat_id}")
                        db.session.add(reserved)
        
        db.session.commit()
        return not_allowed


class DriverService:
    """ドライバー関連のビジネスロジック"""
    
    @staticmethod
    def get_driver_by_username(username):
        """ユーザー名でドライバーを取得"""
        return db.session.query(Driver).filter_by(username=username).first()
    
    @staticmethod
    def create_driver_buses_info(user):
        """ドライバーのバス情報を作成"""
        try:
            user_number = int(user[6])
            firstbus = BusService.get_next_bus(user_number)
            
            if firstbus:
                firstbusdate = firstbus.departure_time
                ud = yukisaki(firstbus.ud)
                firstbus_info = {
                    "busid": firstbus.busid, 
                    "departure_time": str(firstbus.departure_time.strftime('%m/%d %H:%M')), 
                    "ud": ud
                }
                firstbus_str = str(f"行き先|{firstbus_info['ud']}  出発時刻|{firstbus_info['departure_time']} {firstbus_info['busid']}号車")
                
                secondbus = BusService.get_second_bus(user_number, firstbusdate)
                if secondbus:
                    ud = yukisaki(secondbus.ud)
                    secondbus_info = {
                        "busid": secondbus.busid, 
                        "departure_time": str(secondbus.departure_time.strftime('%m/%d %H:%M')), 
                        "ud": ud
                    }
                    secondbus_str = str(f"行き先|{secondbus_info['ud']}  出発時刻|{secondbus_info['departure_time']} {secondbus_info['busid']}号車")
                else:
                    secondbus_str = "バスがありません"
            else:
                firstbus_str = "バスがありません"
                secondbus_str = "バスがありません"
                
            return firstbus_str, secondbus_str
        except:
            return "バスがありません", "バスがありません"


class QAService:
    """Q&A関連のビジネスロジック"""
    
    @staticmethod
    def get_all_qa():
        """全てのQ&Aを取得"""
        qa_list = []
        for qa in db.session.query(QA).all():
            qa_list.append({
                "question": qa.question, 
                "answer": qa.answer
            })
        return qa_list