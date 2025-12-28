from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime,timedelta
import json,nfc,binascii,requests,time,os, logging
import numpy as np
from scipy.io import wavfile
from pygame import mixer
from pathlib import Path
from functools import partial

app = Flask(__name__)
app.secret_key = '0000'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yoyaku_seki.db'
app.config['SQLALCHEMY_BINDS'] = {'db2':'sqlite:///users.db'}
API_URL = "http://shuttlebus.kutc.kansai-u.ac.jp:49155"
#API_URL = "http://localhost:5000"
db = SQLAlchemy(app)

#ログ設定
logger = logging.getLogger('auth-log')
logger.setLevel(10)
sh = logging.StreamHandler()
logger.addHandler(sh)
fh = logging.FileHandler('auth.log')
logger.addHandler(fh)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
sh.setFormatter(formatter)
fh.setFormatter(formatter)
logger.info('stating auth')

class Bus(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	busid = db.Column(db.Integer, nullable=False)
	departure_time = db.Column(db.DateTime, nullable=False)
	seats = db.Column(db.Integer,nullable=False)
	ud = db.Column(db.Integer,nullable=False)  #上りなら0、下りなら1
	bookable_time = db.Column(db.Integer,nullable=False)

class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    bus_id = db.Column(db.Integer, nullable=False) # Bus.idを入れている
    '''user_id = db.Column(db.String(100), nullable=True)'''
    reservations = db.relationship('Reservation', backref='seat', lazy=True)

class Reservation(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	'''person_name = db.Column(db.String(50), nullable=False)'''
	seat_number = db.Column(db.Integer, db.ForeignKey('seat.number'), nullable=False)
	bus_id = db.Column(db.Integer, db.ForeignKey('bus.id'), nullable=False)
	user_id = db.Column(db.Integer, nullable=False)
	approved = db.Column(db.Integer,nullable=False)

class User(db.Model):
	__bind_key__ = "db2"
	id = db.Column(db.Integer, primary_key=True)
	student_id = db.Column(db.String(20), nullable=False)
	idm_univ = db.Column(db.String(20), nullable=False)
	idm_bus = db.Column(db.String(20), nullable=False)
	regist_now_time = db.Column(db.DateTime,nullable=False)

class auth(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	busid = db.Column(db.Integer, nullable=False)
	departure_time = db.Column(db.DateTime, nullable=False)
	ud = db.Column(db.Integer,nullable=False)  #上りなら0、下りなら1

with app.app_context():
    db.create_all()


@app.route('/')
def home():
	bus = db.session.query(auth).order_by(auth.id.desc()).first()
	print(bus.id)
	delay = (bus.departure_time - datetime.now() + timedelta(minutes=5)).total_seconds() + 1
	delay = int(delay)
	print(delay)
	number = int(os.environ['ID'])
	date = bus.departure_time.time()
	date = date.strftime('%H:%M')
	logger.info(f"{date}, {delay}")
	return render_template('auth_home.html',delay=delay,number=number,date=date)

@app.route('/scan',methods=['POST'])
def scan():
	bus = db.session.query(auth).order_by(auth.id.desc()).first()
	delay = (bus.departure_time - datetime.now() + timedelta(minutes=5)).total_seconds() + 1
	delay = int(delay)
	idm = get_id(delay)
	if idm is not None:
		return redirect(url_for('result',idm=idm))
	else:
		return redirect(url_for('auth_wait'))
	'''try:
		print(idm)
		if idm == TimeoutError:
			return redirect(url_for('auth_wait'))
		else:
			return redirect(url_for('result',idm=idm))
	except:
		print("timeout")'''

@app.route('/result/<idm>')
def result(idm):
	number = int(os.environ['ID'])
	logger.info(f"{idm}")

	print(number)
	response = requests.get(f"{API_URL}/auth", json={'idm' : idm,'number' : number})
	status_code = response.status_code
	print(status_code)
	if status_code == 200:
		print(f"success")
		data = response.json()
		seat_number = data['seat_number']
		return redirect(url_for('auth_success',seat_number = seat_number))
	elif status_code == 403:
		data = response.json()
		bus_number = data['bus_number']
		logger.info(f"failed, id is different")
		return redirect(url_for('auth_iddifferent',bus_id = int(os.environ['id']), id=bus_number))
	
	elif status_code == 401:
		data = response.json()
		logger.info("failed, your card is not registed")
		return redirect(url_for('auth_failed', status_code=status_code))

	else:
		return redirect(url_for('auth_failed',status_code=status_code))

@app.route('/success/<seat_number>')
def auth_success(seat_number):
	try:
		logger.info("success")
		seat = seat_number
		mixer.init()
		mixer.music.load("My Song 2.wav")
		mixer.music.play(1,0.0)
		return render_template("auth_success.html",seat_number=seat)
	except Exception as e:
		logger.info(f"mystery failed:{e}")

@app.route('/failed/<status_code>')
def auth_failed(status_code):
	logger.info("fail")
	try:
		status = int(status_code)
		logger.info("failed")
		mixer.init()
		mixer.music.load("My Song 3.wav")
		mixer.music.play(1,0.0)
		print(status)
		if status == 401:
			return render_template("auth_notcard.html")
		else:
			logger.info("auth failed")
			return render_template("auth_failed.html")
	except Exception as e:
		mixer.init()
		mixer.music.load("My Song 3.wav")
		mixer.music.play(1,0.0)
		logger.info(f"mystery error :{e}")
		return render_template("auth_failed.html")

@app.route('/failed/iddifferent/<id>')
def auth_iddifferent(id):
	logger.info("iddifferent")
	try:
		mixer.init()
		mixer.music.load("My Song 3.wav")
		mixer.music.play(1,0.0)
		return render_template("auth_iddifferent.html",bus_id = int(os.environ['ID']), id = id)

	except Exception as e:
		mixer.init()
		mixer.music.load("My Song 3.wav")
		mixer.music.play(1,0.0)
		logger.info(f"mystery error :{e}")
		return render_template("auth_failed.html")

@app.route('/auth/wait')
def auth_wait():
	return render_template("auth_wait.html")

@app.route('/auth/data_get')
def auth_data_get():
	try:
		number = int(os.environ['ID'])
		response = requests.get(f"{API_URL}/auth/getbus",json={'number' : number})
		data = response.json()
		print(data)
		new_bus = auth(busid = data['id'],departure_time = datetime.strptime(data['departure_time'],'%Y/%m/%d %H:%M'),ud = data['ud'])
		db.session.add(new_bus)
		db.session.commit()
		return redirect(url_for('home'))

	except Exception as e:
		print(f"Error:{e}")
		return redirect(url_for('auth_wait'))


def get_id(delay):
	def afrer(n, started):
		t = time.time() - started
		elapsed_seconds = int(t)
		return elapsed_seconds > n

	try:
		with nfc.ContactlessFrontend('usb') as clf:  # リーダーの接続確認
			started = time.time()
			wait_s= delay
			tag = clf.connect(rdwr={'on-connect': lambda tag: False},terminate=partial(afrer, wait_s, started))
			idm = binascii.hexlify(tag.identifier).upper()
			idm = idm.decode()
			return idm
	except Exception as e:
		print("NFC読み取りエラー:", e)
		return None

'''			
@app.errorhandler(Exception)
def handle_exception(error):
	logger.info(f"Error:{str(error)}")
'''

if __name__ == '__main__':
    app.run(port=8000)