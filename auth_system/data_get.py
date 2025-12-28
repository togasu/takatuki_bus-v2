from sqlalchemy import create_engine,Column,Integer,String,DateTime,Sequence,ForeignKey,and_ ,or_,func
from sqlalchemy.orm import sessionmaker,declarative_base,relationship
from datetime import datetime,timedelta
import requests,json,time

engine1 = create_engine('sqlite:///instance/users.db',echo = False)
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
    regist_now_time = Column(DateTime,nullable=False)
    def __repr__(self):
        return f"<User {self.id}, {self.student_id}, {self.idm_univ}, {self.idm_bus}>"

class Bus(Base2):
    __tablename__ = 'bus'
    id = Column(Integer, primary_key=True)
    busid = Column(Integer, nullable=False)
    departure_time = Column(DateTime, nullable=False)
    seats = Column(Integer,nullable=False)
    ud = Column(Integer,nullable=False)  #上りなら0、下りなら1
    bookable_time = Column(Integer,nullable=False)

class Seat(Base2):
    __tablename__ = 'seat'
    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)
    bus_id = Column(Integer, nullable=False) # Bus.idを入れている
    '''user_id = db.Column(db.String(100), nullable=True)'''
    reservations = relationship('Reservation', backref='seat', lazy=True)

class Reservation(Base2):
    __tablename__ = 'reservation'
    id =Column(Integer, primary_key=True)
    '''person_name = db.Column(db.String(50), nullable=False)'''
    seat_number = Column(Integer, ForeignKey('seat.number'), nullable=False)
    bus_id = Column(Integer, ForeignKey('bus.id'), nullable=False)
    user_id = Column(Integer, nullable=False)
    approved = Column(Integer,nullable=False)

Base1.metadata.create_all(engine1)
Base2.metadata.create_all(engine2)


def get_bus(Bus_data):
    if Bus_data:
        for bus in Bus_data:
                #bus['departure_time']=bus['departure_time'].strftime('%Y/%m/%d %H:%M:%S')
                new_bus = Bus(id=bus['id'],busid=bus['busid'],departure_time=datetime.strptime(bus['departure_time'],'%Y/%m/%d %H:%M:%S'),seats=bus['seats'],ud=bus['ud'],bookable_time=bus['bookable_time'])
                try:
                    session2.add(new_bus)
                    session2.commit()
                except Exception as e:
                    session2.rollback()
                    print("Error",e)

def get_seat(Seat_data):
    if Seat_data:
        for seat in Seat_data[:]:
            try:
                new_reservation = Seat(id=seat['id'],number=seat['number'],bus_id=seat['bus_id'])
                session2.add(new_reservation)
                session2.commit() 
            except Exception as e:
                session2.rollback()
                print("Error",e)

def get_reservation(Reservation_data):
    if Reservation_data:
        for reservation in Reservation_data[:]:
            print(reservation)
            try:
                new_reservation = Reservation(id=reservation['id'],seat_number=reservation['seat_number'],bus_id=reservation['bus_id'],user_id=reservation['user_id'],approved=reservation['approved'])
                session2.add(new_reservation)
                session2.commit() 
            except Exception as e:
                session2.rollback()
                print("Error",e)

def get_user(User_data):
    if User:
        for user in User_data[:]:
            try:
                new_user = User(id=user['id'],student_id=user['student_id'],idm_univ=user['idm_univ'],idm_bus=user['idm_bus'],regist_now_time=user['regist_now_time'])
                session1.add(new_user)
                session1.commit()
            except Exception as e:
                session1.rollback()
                print("Error",e)

API_URL = "http://ogilab.kutc.kansai-u.ac.jp:3090"
response = requests.get(f"{API_URL}/data_get")
data = response.json()
print(data)
Bus_data = data['Bus_list']
Reservation_data = data['Reservation_list']
User_data = data['User_list']
Seat_data = data['Seat_list']
get_bus(Bus_data)
print(Reservation_data)
get_seat(Seat_data)
get_reservation(Reservation_data)
User_data= data['User_list']
get_user(User_data)

session1.close()
session2.close()
