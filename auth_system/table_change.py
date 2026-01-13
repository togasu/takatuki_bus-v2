from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import logging

# ログ設定
logger = logging.getLogger('table-change')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

engine1 = create_engine('sqlite:///instance/users.db', echo=False)
engine2 = create_engine('sqlite:///instance/yoyaku_seki.db',echo = True)
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
    regist_now_time = Column(DateTime, nullable=False)
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
    is_active = Column(Integer, default=1, nullable=False)

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

def migrate_data():
    """
    データベーステーブルのマイグレーション
    古いテーブル構造から新しい構造にデータを移行
    """
    logger.info("Starting table migration...")
    
    # 例: regist_now_timeカラムがない古いUserテーブルからのマイグレーション
    # 必要に応じてコメントアウトを解除して使用
    
    """
    # Userテーブルのマイグレーション例
    try:
        # 古いテーブル（regist_now_timeなし）からデータ取得
        old_users = session1.execute(
            "SELECT id, student_id, idm_univ, idm_bus FROM old_user_table"
        ).fetchall()
        
        users = []
        for old_user in old_users:
            new_user = User(
                id=old_user[0],
                student_id=old_user[1],
                idm_univ=old_user[2],
                idm_bus=old_user[3],
                regist_now_time=datetime.now()
            )
            users.append(new_user)
        
        if users:
            session1.bulk_save_objects(users)
            session1.commit()
            logger.info(f"Migrated {len(users)} users")
    except Exception as e:
        session1.rollback()
        logger.error(f"User migration failed: {e}")
    """
    
    """
    # Busテーブルのマイグレーション例（bookable_time, statusカラム追加）
    try:
        old_buses = session2.query(Bus).filter(Bus.bookable_time == None).all()
        
        for bus in old_buses:
            bus.bookable_time = 30  # デフォルト値
            bus.status = 0  # デフォルト値
        
        session2.commit()
        logger.info(f"Migrated {len(old_buses)} buses")
    except Exception as e:
        session2.rollback()
        logger.error(f"Bus migration failed: {e}")
    """
    
    """
    # Reservationテーブルのマイグレーション例（approvedカラム追加）
    try:
        old_reservations = session2.query(Reservation).filter(Reservation.approved == None).all()
        
        for reservation in old_reservations:
            reservation.approved = 0  # デフォルト値（未認証）
            reservation.user_id = str(reservation.user_id)  # String型に変換
        
        session2.commit()
        logger.info(f"Migrated {len(old_reservations)} reservations")
    except Exception as e:
        session2.rollback()
        logger.error(f"Reservation migration failed: {e}")
    """
    
    logger.info("Migration completed")

if __name__ == '__main__':
    try:
        migrate_data()
    except Exception as e:
        logger.error(f"Migration error: {e}")
    finally:
        session1.close()
        session2.close()
        logger.info("Sessions closed")