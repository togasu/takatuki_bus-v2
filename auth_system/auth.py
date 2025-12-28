from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os, logging

# 高速起動のため、重いライブラリは遅延インポート
# nfc, pygameは実際に使用する時にインポート

app = Flask(__name__)
app.secret_key = '0000'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yoyaku_seki.db'
app.config['SQLALCHEMY_BINDS'] = {'db2':'sqlite:///users.db'}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # オーバーヘッド削減
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

STUDENT_API_URL = os.environ.get('STUDENT_API_URL', 'http://shuttlebus.kutc.kansai-u.ac.jp')
db = SQLAlchemy(app)

# ログ設定（簡素化）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('auth.log')
    ]
)
logger = logging.getLogger('auth-log')
logger.info('Starting auth system')

class Bus(db.Model):
	"""
	バス便モデル
	
	重要な属性:
	- id: バス便の一意のID（データベース自動生成、例: 1, 2, 3...）
	- busid: バスの号車番号（1～4の固定値、運転手番号と対応）
	
	同じbusid（号車）でも、異なる出発時刻のバス便は別のid（バス便ID）を持ちます。
	例: 1号車が1日に3便運行する場合、busid=1でid=1,10,20のような3つのレコードができます。
	"""
	id = db.Column(db.Integer, primary_key=True)
	busid = db.Column(db.Integer, nullable=False) # バスの号車（運転手番号と同じ）１～４までしか割り当てられない
	departure_time = db.Column(db.DateTime, nullable=False)
	seats = db.Column(db.Integer, nullable=False)
	ud = db.Column(db.Integer, nullable=False)  # 上りなら0、下りなら1
	bookable_time = db.Column(db.Integer, nullable=False)  # デフォルト0,予約可能時間に合わせて変更
	status = db.Column(db.Integer, nullable=False) # 0は通常、1はキャンセル待ち（現在機能中止）、2は出発後

class Seat(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	number = db.Column(db.Integer, nullable=False)
	bus_id = db.Column(db.Integer, nullable=False)  # Bus.idを入れている
	# reservations relationshipを削除（外部キー制約がないため）

class Reservation(db.Model):
	__tablename__ = 'Reservation'  # テーブル名を指定
	id = db.Column(db.Integer, primary_key=True)
	seat_number = db.Column(db.Integer, nullable=False)  # 外部キー制約を削除（numberは主キーではないため）
	bus_id = db.Column(db.Integer, db.ForeignKey('bus.id'), nullable=False)
	user_id = db.Column(db.String(50), nullable=False)  # admin/driver対応のため文字列型に変更
	approved = db.Column(db.Integer, nullable=False)  # 0なら未認証(デフォルト)、1なら認証済み
	reserved_time = db.Column(db.DateTime)
	
	# 一意制約: 同じバスの同じ座席に複数の予約を防ぐ
	__table_args__ = (
		db.UniqueConstraint('bus_id', 'seat_number', name='uq_bus_seat'),
	)

class User(db.Model):
	__bind_key__ = "db2"
	id = db.Column(db.Integer, primary_key=True)
	student_id = db.Column(db.String(20), nullable=False)
	idm_univ = db.Column(db.String(20), nullable=False)
	idm_bus = db.Column(db.String(20), nullable=False)
	regist_now_time = db.Column(db.DateTime, nullable=False)  # 登録された日時

class User_Penalty(db.Model):
	__bind_key__ = "db2"
	__tablename__ = "user_penalty"
	id = db.Column(db.Integer, primary_key=True)
	student_id = db.Column(db.String(20), nullable=False)  # String型に変更
	end_time_of_usage_restriction = db.Column(db.DateTime, nullable=False)  # 必須フィールドに変更
	reason = db.Column(db.String(200), nullable=False)  # 利用制限の理由
	penalty_type = db.Column(db.String(50), default='manual', nullable=False)  # auto, manual
	applied_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # ペナルティ適用日時
	is_active = db.Column(db.Boolean, default=True, nullable=False)  # ペナルティ有効フラグ

class Penalty_Reservation(db.Model):
	"""ペナルティに関連する予約情報"""
	__bind_key__ = "db2"
	__tablename__ = "penalty_reservation"
	id = db.Column(db.Integer, primary_key=True)
	penalty_id = db.Column(db.Integer, db.ForeignKey('user_penalty.id'), nullable=False)
	reservation_id = db.Column(db.Integer, nullable=False)  # 該当する予約ID
	student_id = db.Column(db.String(20), nullable=False)
	bus_id = db.Column(db.Integer, nullable=False)
	seat_number = db.Column(db.Integer, nullable=False)
	reserved_time = db.Column(db.DateTime, nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class LastSemester_user(db.Model):
	__bind_key__ = "db2"
	id = db.Column(db.Integer, primary_key=True)
	student_id = db.Column(db.String(20), nullable=False)
	idm_univ = db.Column(db.String(20), nullable=False)
	idm_bus = db.Column(db.String(20), nullable=False)
	regist_now_time = db.Column(db.DateTime, nullable=False)

class auth(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	busid = db.Column(db.Integer, nullable=False)
	departure_time = db.Column(db.DateTime, nullable=False)
	ud = db.Column(db.Integer, nullable=False)  # 上りなら0、下りなら1

# データベース初期化フラグ
_db_initialized = False

def ensure_db_initialized():
	"""データベースが初期化されていることを保証（遅延初期化）"""
	global _db_initialized
	if not _db_initialized:
		with app.app_context():
			db.create_all()
			_db_initialized = True
			logger.info('Database initialized')


@app.route('/')
def home():
	ensure_db_initialized()
	bus = db.session.query(auth).order_by(auth.id.desc()).first()
	if not bus:
		logger.error("No bus data found")
		return redirect(url_for('auth_wait'))
	
	delay = int((bus.departure_time - datetime.now() + timedelta(minutes=5)).total_seconds() + 1)
	number = int(os.environ.get('ID', 0))
	date = bus.departure_time.strftime('%H:%M')
	logger.info(f"{date}, {delay}")
	return render_template('auth_home.html', delay=delay, number=number, date=date)

@app.route('/scan', methods=['POST'])
def scan():
	ensure_db_initialized()
	bus = db.session.query(auth).order_by(auth.id.desc()).first()
	if not bus:
		return redirect(url_for('auth_wait'))
	
	delay = int((bus.departure_time - datetime.now() + timedelta(minutes=5)).total_seconds() + 1)
	idm = get_id(delay)
	return redirect(url_for('result', idm=idm) if idm else url_for('auth_wait'))

@app.route('/result/<idm>')
def result(idm):
	import requests  # 遅延インポート
	ensure_db_initialized()
	number = int(os.environ.get('ID', 0))
	logger.info(f"IDM: {idm}")
	
	try:
		# studentサービスでIDm認証
		response = requests.get(f"{STUDENT_API_URL}/auth", json={'idm': idm, 'number': number}, timeout=10)
		data = response.json()
		
		if response.status_code == 200:
			logger.info("Authentication success")
			seat_number = data['seat_number']
			reservation_id = data.get('reservation_id')
			
			# studentサービスに認証完了を通知（approved=1に更新）
			if reservation_id:
				try:
					approve_response = requests.post(
						f"{STUDENT_API_URL}/auth/approve",
						json={'reservation_id': reservation_id, 'bus_number': number},
						timeout=5
					)
					if approve_response.status_code == 200:
						logger.info(f"Reservation {reservation_id} approved in student service")
					else:
						logger.warning(f"Failed to approve reservation {reservation_id}: {approve_response.status_code}")
				except requests.RequestException as e:
					logger.warning(f"Failed to notify approval to student service: {e}")
			
			return redirect(url_for('auth_success', seat_number=seat_number))
			
		elif response.status_code == 403:
			logger.info("Bus ID mismatch")
			return redirect(url_for('auth_iddifferent', bus_id=number, id=data.get('bus_number', 'unknown')))
			
		elif response.status_code == 401:
			logger.info("Card not registered")
			return redirect(url_for('auth_failed', status_code=401))
		else:
			return redirect(url_for('auth_failed', status_code=response.status_code))
			
	except requests.RequestException as e:
		logger.error(f"API request failed: {e}")
		return redirect(url_for('auth_failed', status_code=500))

# 音声ミキサーのキャッシュ
_mixer_initialized = False

def play_audio(filename):
	"""音声再生（遅延インポートとキャッシュ）"""
	global _mixer_initialized
	try:
		if not _mixer_initialized:
			from pygame import mixer
			mixer.init()
			_mixer_initialized = True
		else:
			from pygame import mixer
		mixer.music.load(filename)
		mixer.music.play(1, 0.0)
	except Exception as e:
		logger.warning(f"Audio playback failed: {e}")

@app.route('/success/<seat_number>')
def auth_success(seat_number):
	logger.info("Authentication successful")
	play_audio("My Song 2.wav")
	return render_template("auth_success.html", seat_number=seat_number)

@app.route('/failed/<status_code>')
def auth_failed(status_code):
	logger.info(f"Authentication failed: {status_code}")
	play_audio("My Song 3.wav")
	template = "auth_notcard.html" if int(status_code) == 401 else "auth_failed.html"
	return render_template(template)

@app.route('/failed/iddifferent/<id>')
def auth_iddifferent(id):
	logger.info("Bus ID mismatch")
	play_audio("My Song 3.wav")
	return render_template("auth_iddifferent.html", bus_id=int(os.environ.get('ID', 0)), id=id)

@app.route('/auth/wait')
def auth_wait():
	return render_template("auth_wait.html")

@app.route('/auth/data_get')
def auth_data_get():
	import requests  # 遅延インポート
	ensure_db_initialized()
	try:
		number = int(os.environ.get('ID', 0))
		# studentサービスからバス情報を取得
		response = requests.get(f"{STUDENT_API_URL}/auth/getbus", json={'number': number}, timeout=10)
		response.raise_for_status()
		data = response.json()
		
		new_bus = auth(
			busid=data['id'],
			departure_time=datetime.strptime(data['departure_time'], '%Y/%m/%d %H:%M'),
			ud=data['ud']
		)
		db.session.add(new_bus)
		db.session.commit()
		logger.info(f"Bus data updated from student service: {data['id']}")
		return redirect(url_for('home'))
		
	except (requests.RequestException, KeyError, ValueError) as e:
		logger.error(f"Failed to get bus data from student service: {e}")
		db.session.rollback()
		return redirect(url_for('auth_wait'))


def get_id(delay):
	"""NFCカードからIDmを読み取る"""
	import nfc
	import binascii
	import time
	from functools import partial
	
	def after(n, started):
		return int(time.time() - started) > n

	try:
		with nfc.ContactlessFrontend('usb') as clf:
			started = time.time()
			tag = clf.connect(
				rdwr={'on-connect': lambda tag: False},
				terminate=partial(after, delay, started)
			)
			if tag:
				return binascii.hexlify(tag.identifier).decode().upper()
			return None
	except Exception as e:
		logger.error(f"NFC read error: {e}")
		return None

if __name__ == '__main__':
	logger.info('Auth system ready')
	# プロダクションモードで起動（デバッグモードは無効）
	app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)