from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import requests
import logging

# ログ設定
logger = logging.getLogger('data-get')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

engine1 = create_engine('sqlite:///instance/users.db', echo=False)
engine2 = create_engine('sqlite:///instance/yoyaku_seki.db',echo = False)
#engine = create_engine('sqlite:///instance/users.db',echo = True)

Base1 = declarative_base()
Base2 = declarative_base()

Session1 = sessionmaker(bind=engine1)
session1 = Session1() 

Session2 = sessionmaker(bind=engine2)
session2 = Session2()

class User(Base1):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    student_id = Column(String(20), nullable=False)
    idm_univ = Column(String(20), nullable=False)
    idm_bus = Column(String(20), nullable=False)
    regist_now_time = Column(DateTime, nullable=False)  # 登録された日時
    def __repr__(self):
        return f"<User {self.id}, {self.student_id}, {self.idm_univ}, {self.idm_bus}>"

class User_Penalty(Base1):
    __tablename__ = "user_penalty"
    id = Column(Integer, primary_key=True)
    student_id = Column(String(20), nullable=False)
    end_time_of_usage_restriction = Column(DateTime, nullable=False)
    reason = Column(String(200), nullable=False)
    penalty_type = Column(String(50), default='manual', nullable=False)
    applied_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Integer, default=1, nullable=False)  # SQLiteではBooleanの代わりにIntegerを使用

class Penalty_Reservation(Base1):
    """ペナルティに関連する予約情報"""
    __tablename__ = "penalty_reservation"
    id = Column(Integer, primary_key=True)
    penalty_id = Column(Integer, ForeignKey('user_penalty.id'), nullable=False)
    reservation_id = Column(Integer, nullable=False)
    student_id = Column(String(20), nullable=False)
    bus_id = Column(Integer, nullable=False)
    seat_number = Column(Integer, nullable=False)
    reserved_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class LastSemester_user(Base1):
    __tablename__ = 'last_semester_user'
    id = Column(Integer, primary_key=True)
    student_id = Column(String(20), nullable=False)
    idm_univ = Column(String(20), nullable=False)
    idm_bus = Column(String(20), nullable=False)
    regist_now_time = Column(DateTime, nullable=False)

class Bus(Base2):
    __tablename__ = 'bus'
    id = Column(Integer, primary_key=True)
    busid = Column(Integer, nullable=False)
    departure_time = Column(DateTime, nullable=False)
    seats = Column(Integer, nullable=False)
    ud = Column(Integer, nullable=False)  # 上りなら0、下りなら1
    bookable_time = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False)  # 0は通常、1はキャンセル待ち、2は出発後

class Seat(Base2):
    __tablename__ = 'seat'
    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)
    bus_id = Column(Integer, nullable=False)  # Bus.idを入れている

class Reservation(Base2):
    __tablename__ = 'Reservation'  # テーブル名を大文字に
    id = Column(Integer, primary_key=True)
    seat_number = Column(Integer, nullable=False)
    bus_id = Column(Integer, ForeignKey('bus.id'), nullable=False)
    user_id = Column(String(50), nullable=False)  # String型に変更
    approved = Column(Integer, nullable=False)
    reserved_time = Column(DateTime)

Base1.metadata.create_all(engine1)
Base2.metadata.create_all(engine2)


def get_bus(session, bus_data):
    """Busデータをバッチ処理で登録"""
    if not bus_data:
        return
    
    buses = []
    for bus in bus_data:
        try:
            new_bus = Bus(
                id=bus['id'],
                busid=bus['busid'],
                departure_time=datetime.strptime(bus['departure_time'], '%Y/%m/%d %H:%M:%S'),
                seats=bus['seats'],
                ud=bus['ud'],
                bookable_time=bus['bookable_time'],
                status=bus.get('status', 0)  # デフォルト値を0
            )
            buses.append(new_bus)
        except (KeyError, ValueError) as e:
            logger.error(f"Bus data error: {e} - {bus}")
            continue
    
    if buses:
        try:
            session.bulk_save_objects(buses)
            session.commit()
            logger.info(f"Added {len(buses)} buses")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save buses: {e}")

def get_seat(session, seat_data):
    """Seatデータをバッチ処理で登録"""
    if not seat_data:
        return
    
    seats = []
    for seat in seat_data:
        try:
            new_seat = Seat(
                id=seat['id'],
                number=seat['number'],
                bus_id=seat['bus_id']
            )
            seats.append(new_seat)
        except KeyError as e:
            logger.error(f"Seat data error: {e} - {seat}")
            continue
    
    if seats:
        try:
            session.bulk_save_objects(seats)
            session.commit()
            logger.info(f"Added {len(seats)} seats")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save seats: {e}")

def get_reservation(session, reservation_data):
    """Reservationデータをバッチ処理で登録"""
    if not reservation_data:
        return
    
    reservations = []
    for reservation in reservation_data:
        try:
            new_reservation = Reservation(
                id=reservation['id'],
                seat_number=reservation['seat_number'],
                bus_id=reservation['bus_id'],
                user_id=str(reservation['user_id']),
                approved=reservation['approved'],
                reserved_time=reservation.get('reserved_time')
            )
            reservations.append(new_reservation)
        except KeyError as e:
            logger.error(f"Reservation data error: {e} - {reservation}")
            continue
    
    if reservations:
        try:
            session.bulk_save_objects(reservations)
            session.commit()
            logger.info(f"Added {len(reservations)} reservations")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save reservations: {e}")

def get_user(session, user_data):
    """Userデータをバッチ処理で登録"""
    if not user_data:
        return
    
    users = []
    for user in user_data:
        try:
            new_user = User(
                id=user['id'],
                student_id=user['student_id'],
                idm_univ=user['idm_univ'],
                idm_bus=user['idm_bus'],
                regist_now_time=user['regist_now_time']
            )
            users.append(new_user)
        except KeyError as e:
            logger.error(f"User data error: {e} - {user}")
            continue
    
    if users:
        try:
            session.bulk_save_objects(users)
            session.commit()
            logger.info(f"Added {len(users)} users")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save users: {e}")

def get_user_penalty(session, penalty_data):
    """User_Penaltyデータをバッチ処理で登録"""
    if not penalty_data:
        return
    
    penalties = []
    for penalty in penalty_data:
        try:
            new_penalty = User_Penalty(
                id=penalty['id'],
                student_id=penalty['student_id'],
                end_time_of_usage_restriction=penalty['end_time_of_usage_restriction'],
                reason=penalty['reason'],
                penalty_type=penalty.get('penalty_type', 'manual'),
                applied_time=penalty.get('applied_time', datetime.utcnow()),
                is_active=penalty.get('is_active', 1)
            )
            penalties.append(new_penalty)
        except KeyError as e:
            logger.error(f"Penalty data error: {e} - {penalty}")
            continue
    
    if penalties:
        try:
            session.bulk_save_objects(penalties)
            session.commit()
            logger.info(f"Added {len(penalties)} penalties")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save penalties: {e}")

def get_penalty_reservation(session, penalty_res_data):
    """Penalty_Reservationデータをバッチ処理で登録"""
    if not penalty_res_data:
        return
    
    penalty_reservations = []
    for pr in penalty_res_data:
        try:
            new_pr = Penalty_Reservation(
                id=pr['id'],
                penalty_id=pr['penalty_id'],
                reservation_id=pr['reservation_id'],
                student_id=pr['student_id'],
                bus_id=pr['bus_id'],
                seat_number=pr['seat_number'],
                reserved_time=pr['reserved_time'],
                created_at=pr.get('created_at', datetime.utcnow())
            )
            penalty_reservations.append(new_pr)
        except KeyError as e:
            logger.error(f"Penalty reservation data error: {e} - {pr}")
            continue
    
    if penalty_reservations:
        try:
            session.bulk_save_objects(penalty_reservations)
            session.commit()
            logger.info(f"Added {len(penalty_reservations)} penalty reservations")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save penalty reservations: {e}")

def get_last_semester_user(session, last_semester_data):
    """LastSemester_userデータをバッチ処理で登録"""
    if not last_semester_data:
        return
    
    last_users = []
    for user in last_semester_data:
        try:
            new_user = LastSemester_user(
                id=user['id'],
                student_id=user['student_id'],
                idm_univ=user['idm_univ'],
                idm_bus=user['idm_bus'],
                regist_now_time=user['regist_now_time']
            )
            last_users.append(new_user)
        except KeyError as e:
            logger.error(f"Last semester user data error: {e} - {user}")
            continue
    
    if last_users:
        try:
            session.bulk_save_objects(last_users)
            session.commit()
            logger.info(f"Added {len(last_users)} last semester users")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save last semester users: {e}")

# メイン処理
if __name__ == '__main__':
    API_URL = "http://ogilab.kutc.kansai-u.ac.jp:3090"
    
    try:
        logger.info("Fetching data from API...")
        response = requests.get(f"{API_URL}/data_get", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # データの存在チェック
        bus_data = data.get('Bus_list', [])
        seat_data = data.get('Seat_list', [])
        reservation_data = data.get('Reservation_list', [])
        user_data = data.get('User_list', [])
        penalty_data = data.get('User_Penalty_list', [])
        penalty_res_data = data.get('Penalty_Reservation_list', [])
        last_semester_data = data.get('LastSemester_user_list', [])
        
        logger.info(f"Received: {len(bus_data)} buses, {len(seat_data)} seats, "
                   f"{len(reservation_data)} reservations, {len(user_data)} users, "
                   f"{len(penalty_data)} penalties, {len(penalty_res_data)} penalty reservations, "
                   f"{len(last_semester_data)} last semester users")
        
        # データ更新
        get_bus(session2, bus_data)
        get_seat(session2, seat_data)
        get_reservation(session2, reservation_data)
        get_user(session1, user_data)
        get_user_penalty(session1, penalty_data)
        get_penalty_reservation(session1, penalty_res_data)
        get_last_semester_user(session1, last_semester_data)
        
        logger.info("Data synchronization completed")
        
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        session1.close()
        session2.close()
        logger.info("Sessions closed")
