from sqlalchemy import create_engine,Column,Integer,String,DateTime,Sequence,ForeignKey,and_ ,or_,func
from sqlalchemy.orm import sessionmaker,declarative_base,relationship
from datetime import datetime,timedelta
import requests,json,time

engine1 = create_engine('sqlite:///instance/users.db',echo = False)
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
    def __repr__(self):
        return f"<User {self.id}, {self.student_id}, {self.idm_univ}, {self.idm_bus}>"
    
class New_User(Base1):
    __tablename__ = 'new_user'
    id = Column(Integer, primary_key=True)
    student_id = Column(String(20), nullable=False)
    idm_univ = Column(String(20), nullable=False)
    idm_bus = Column(String(20), nullable=False)
    regist_now_time = Column(DateTime,nullable=False)
    def __repr__(self):
        return f"<User {self.id}, {self.student_id}, {self.idm_univ}, {self.idm_bus}>"

class Bus(Base2):
    __tablename__ = 'bus'
    id = Column(Integer, primary_key=True)
    busid = Column(Integer, nullable=False)
    departure_time = Column(DateTime, nullable=False)
    seats = Column(Integer,nullable=False)
    ud = Column(Integer,nullable=False)  #上りなら0、下りなら1

class New_Bus(Base2):
    __tablename__ = 'new_bus'
    id = Column(Integer, primary_key=True)
    busid = Column(Integer, nullable=False)
    departure_time = Column(DateTime, nullable=False)
    seats = Column(Integer,nullable=False)
    ud = Column(Integer,nullable=False)  #上りなら0、下りなら1
    bookable_time = Column(Integer,nullable=False)

class Seat(Base2):
    __tablename__ = 'seat'
    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)
    bus_id = Column(Integer, nullable=False) # Bus.idを入れている
    '''user_id = db.Column(db.String(100), nullable=True)'''
    reservations = relationship('Reservation', backref='seat', lazy=True)

class Reservation(Base2):
    __tablename__ = 'reservation'
    id =Column(Integer, primary_key=True)
    '''person_name = db.Column(db.String(50), nullable=False)'''
    seat_number = Column(Integer, ForeignKey('seat.number'), nullable=False)
    bus_id = Column(Integer, ForeignKey('bus.id'), nullable=False)
    user_id = Column(Integer, nullable=False)

class New_Reservation(Base2):
    __tablename__ = 'new_reservation'
    id =Column(Integer, primary_key=True)
    '''person_name = db.Column(db.String(50), nullable=False)'''
    seat_number = Column(Integer, ForeignKey('seat.number'), nullable=False)
    bus_id = Column(Integer, ForeignKey('bus.id'), nullable=False)
    user_id = Column(Integer, nullable=False)
    approved = Column(Integer,nullable=False)

Base1.metadata.create_all(engine1)
Base2.metadata.create_all(engine2)

'''Reservation_data = session2.query(Reservation).order_by(Reservation.id).all()
try:
    for reservation in Reservation_data:
        new_reservation = New_Reservation(id=reservation.id,seat_number=reservation.seat_number,bus_id=reservation.bus_id,user_id=reservation.user_id,approved=0)
        session2.add(new_reservation)
        session2.commit()
except:
    session2.rollback()

Bus_data = session2.query(Bus).order_by(Bus.id).all()
try:
    for bus in Bus_data:
        new_bus=New_Bus(id=bus.id,busid=bus.busid,departure_time=bus.departure_time,seats=bus.seats,ud=bus.ud,bookable_time=30)
        session2.add(new_bus)
        session2.commit()
except:
    session2.rollback()

session2.close()'''

User_data = session1.query(User).order_by(User.id).all()
try:
    for user in User_data:
        new_user = New_User(id=user.id,student_id=user.student_id,idm_univ=user.idm_univ,idm_bus=user.idm_bus,regist_now_time=datetime.now())
        session1.add(new_user)
        session1.commit()
except:
    session1.rollback()

session1.close()