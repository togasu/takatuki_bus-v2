from flask import Flask, render_template, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import logging
import threading
import time
from dotenv import load_dotenv

load_dotenv()

# =========================
# Flask / SQLAlchemy 基本設定
# =========================
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# DBパス（driver DBは絶対パスbind）
base_dir = os.path.abspath(os.path.dirname(__file__))
driver_db_path = os.path.join(os.path.dirname(base_dir), 'driver', 'instance', 'driver.db')
driver_db_uri = driver_db_path.replace('\\', '/')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yoyaku_seki.db'
app.config['SQLALCHEMY_BINDS'] = {
    'db2': 'sqlite:///users.db',
    'driver_db': f'sqlite:///{driver_db_uri}',
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

STUDENT_API_URL = os.environ.get('STUDENT_API_URL', 'https://shuttlebus.kutc.kansai-u.ac.jp')
DRIVER_API_URL = os.environ.get('DRIVER_API_URL', 'http://driver:5002')
DEV_MODE = os.environ.get('DEV_MODE', '0').lower() in ('1', 'true', 'yes')

db = SQLAlchemy(app)

# =========================
# ログ設定（軽量）
# =========================
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
logger.info(f'Driver DB path: {driver_db_path}')
logger.info(f'Driver DB exists: {os.path.exists(driver_db_path)}')
logger.info(f'Development mode: {DEV_MODE}')

# =========================
# Models（元実装を維持）
# =========================
class Bus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    busid = db.Column(db.Integer, nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    ud = db.Column(db.Integer, nullable=False)
    bookable_time = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, nullable=False)

class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    bus_id = db.Column(db.Integer, nullable=False)

class Reservation(db.Model):
    __tablename__ = 'Reservation'
    id = db.Column(db.Integer, primary_key=True)
    seat_number = db.Column(db.Integer, nullable=False)
    bus_id = db.Column(db.Integer, db.ForeignKey('bus.id'), nullable=False)
    user_id = db.Column(db.String(50), nullable=False)
    approved = db.Column(db.Integer, nullable=False)
    reserved_time = db.Column(db.DateTime)

    __table_args__ = (
        db.UniqueConstraint('bus_id', 'seat_number', name='uq_bus_seat'),
    )

class User(db.Model):
    __bind_key__ = "db2"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), nullable=False)
    idm_univ = db.Column(db.String(20), nullable=False)
    idm_bus = db.Column(db.String(20), nullable=False)
    regist_now_time = db.Column(db.DateTime, nullable=False)

class User_Penalty(db.Model):
    __bind_key__ = "db2"
    __tablename__ = "user_penalty"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), nullable=False)
    end_time_of_usage_restriction = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    penalty_type = db.Column(db.String(50), default='manual', nullable=False)
    applied_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

class Penalty_Reservation(db.Model):
    __bind_key__ = "db2"
    __tablename__ = "penalty_reservation"
    id = db.Column(db.Integer, primary_key=True)
    penalty_id = db.Column(db.Integer, db.ForeignKey('user_penalty.id'), nullable=False)
    reservation_id = db.Column(db.Integer, nullable=False)
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
    ud = db.Column(db.Integer, nullable=False)

class BusCode(db.Model):
    __bind_key__ = 'driver_db'
    __tablename__ = 'bus_codes'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(6), unique=True, nullable=False, index=True)
    bus_id = db.Column(db.Integer, nullable=False)
    busid = db.Column(db.Integer, nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    ud = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)

# =========================
# DB 遅延初期化（元実装維持 + 呼び出し回数削減）
# =========================
_db_initialized = False
_db_lock = threading.Lock()

def ensure_db_initialized():
    global _db_initialized
    if _db_initialized:
        return
    with _db_lock:
        if _db_initialized:
            return
        with app.app_context():
            try:
                db.create_all()
                _db_initialized = True
                logger.info('Database initialized')
            except Exception as e:
                logger.warning(f'Database initialization warning: {e}')
                try:
                    db.create_all(bind_key=None)
                    db.create_all(bind_key='db2')
                    _db_initialized = True
                    logger.info('Main databases initialized (driver_db skipped)')
                except Exception as e2:
                    logger.error(f'Database initialization failed: {e2}')
                    raise

# =========================
# 音声（遅延 + キャッシュ）
# =========================
_mixer_initialized = False
_mixer_lock = threading.Lock()

def play_audio(filename: str) -> None:
    global _mixer_initialized
    try:
        with _mixer_lock:
            if not _mixer_initialized:
                from pygame import mixer  # 遅延
                mixer.init()
                _mixer_initialized = True
            else:
                from pygame import mixer  # 遅延
        mixer.music.load(filename)
        mixer.music.play(1, 0.0)
    except Exception as e:
        logger.warning(f"Audio playback failed: {e}")

# =========================
# NFC 読み取り（元実装維持）
# =========================
def get_id(delay: int):
    import nfc  # 遅延
    import binascii
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

# =========================
# NFC トリガー化：バックグラウンド待受
# 省電力/高速化：常時ポーリングではなく「最大待ち時間」だけブロック
# =========================
_nfc_state = {
    "status": "waiting",     # waiting / detected / device_error / expired / no_bus
    "idm": None,
    "updated_at": None,
}
_nfc_state_lock = threading.Lock()
_nfc_thread_started = False
_nfc_last_emit_idm = None  # 二重遷移防止

def _set_nfc_state(status: str, idm: str | None):
    with _nfc_state_lock:
        _nfc_state["status"] = status
        _nfc_state["idm"] = idm
        _nfc_state["updated_at"] = datetime.utcnow().isoformat()

def _get_latest_bus_record():
    # authテーブルの最新便
    return db.session.query(auth).order_by(auth.id.desc()).first()

def _compute_remaining_seconds(bus_departure_time: datetime) -> int:
    # 元実装と同じ：出発時刻 - now + 5分（=認証猶予）
    # +1秒は元実装の端数調整を踏襲
    # データベースのbus_departure_timeはJST（naive）なので、JSTで比較
    now_jst = datetime.now(ZoneInfo("Asia/Tokyo")).replace(tzinfo=None)
    sec = int((bus_departure_time - now_jst + timedelta(minutes=5)).total_seconds() + 1)
    return max(0, sec)

def nfc_worker_loop():
    """
    最新便を参照し、残り時間内だけNFC待ちをブロックする。
    - バス便が無い: no_bus
    - 猶予が0: expired
    - NFCデバイス無し等: device_error（get_idがNoneを返すだけなので厳密判定は難しいが、ログで追える）
    - 読めた: detected
    """
    global _nfc_last_emit_idm
    ensure_db_initialized()

    while True:
        try:
            with app.app_context():
                bus = _get_latest_bus_record()
                if not bus:
                    _set_nfc_state("no_bus", None)
                    time.sleep(1.0)
                    continue

                remaining = _compute_remaining_seconds(bus.departure_time)
                if remaining <= 0:
                    _set_nfc_state("expired", None)
                    time.sleep(1.0)
                    continue

                _set_nfc_state("waiting", None)

                # remaining 秒だけ待つ（カードが置かれれば即返る）
                idm = get_id(remaining)

                if idm:
                    # 同じカードを連続で拾った場合の二重遷移を抑制
                    if idm != _nfc_last_emit_idm:
                        _nfc_last_emit_idm = idm
                        _set_nfc_state("detected", idm)
                    # 少し待ってから次へ（リーダ連続読取を緩和）
                    time.sleep(0.8)
                else:
                    # タイムアウト or デバイスエラーの可能性
                    # ここで "device_error" に固定すると誤判定になるので waiting 継続に寄せる
                    _set_nfc_state("waiting", None)
                    time.sleep(0.2)

        except Exception as e:
            logger.error(f"NFC worker error: {e}")
            _set_nfc_state("device_error", None)
            time.sleep(1.0)

@app.before_request
def _ensure_started():
    # 最初のリクエストで DB 初期化 + NFC スレッド開始（起動高速化）
    global _nfc_thread_started
    ensure_db_initialized()
    if not _nfc_thread_started and not DEV_MODE:
        _nfc_thread_started = True
        t = threading.Thread(target=nfc_worker_loop, daemon=True)
        t.start()
        logger.info("NFC background worker started")
    elif DEV_MODE and not _nfc_thread_started:
        _nfc_thread_started = True
        logger.info("Development mode: NFC worker disabled")

# =========================
# Routes
# =========================
@app.route('/')
def home():
    ensure_db_initialized()
    bus = db.session.query(auth).order_by(auth.id.desc()).first()
    if not bus:
        logger.error("No bus data found")
        return redirect(url_for('auth_wait'))

    delay = _compute_remaining_seconds(bus.departure_time)
    number = int(os.environ.get('ID', 0))
    date = bus.departure_time.strftime('%H:%M')
    logger.info(f"{date}, {delay}")
    # auth_home.html 側は /auth/nfc-status を監視して /result/<idm> に飛ぶ想定
    return render_template('auth_home.html', delay=delay, number=number, date=date, dev_mode=DEV_MODE)

@app.route('/auth/nfc-status')
def auth_nfc_status():
    # 画面がポーリングして「detected」になったら /result/<idm> に遷移する
    if DEV_MODE:
        return jsonify({"status": "dev_mode", "idm": None, "updated_at": datetime.utcnow().isoformat()})
    with _nfc_state_lock:
        return jsonify(_nfc_state)

@app.route('/scan', methods=['POST'])
def scan():
    """
    互換維持用（元機能維持）
    - 明示的にPOSTされた場合のみ、残り時間ぶんだけNFC待ちする
    - auth_home.html で自動submitしないこと（あなたの現状はそれで暴発していた）
    """
    ensure_db_initialized()
    bus = db.session.query(auth).order_by(auth.id.desc()).first()
    if not bus:
        return redirect(url_for('auth_wait'))

    delay = _compute_remaining_seconds(bus.departure_time)
    idm = get_id(delay)
    return redirect(url_for('result', idm=idm) if idm else url_for('auth_wait'))

@app.route('/result/<idm>')
def result(idm):
    import requests  # 遅延
    ensure_db_initialized()
    number = int(os.environ.get('ID', 0))
    logger.info(f"IDM: {idm}")

    try:
        response = requests.get(
            f"{STUDENT_API_URL}/auth",
            json={'idm': idm, 'number': number},
            timeout=10
        )
        data = response.json()

        if response.status_code == 200:
            logger.info("Authentication success")
            seat_number = data['seat_number']
            reservation_id = data.get('reservation_id')

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

@app.route('/dev/manual-scan')
def dev_manual_scan():
    """開発モード：手動IDM入力画面"""
    if not DEV_MODE:
        return "Development mode is not enabled", 403
    ensure_db_initialized()
    bus = db.session.query(auth).order_by(auth.id.desc()).first()
    if not bus:
        return redirect(url_for('auth_wait'))
    number = int(os.environ.get('ID', 0))
    date = bus.departure_time.strftime('%H:%M')
    return render_template("dev_manual_scan.html", number=number, date=date)

@app.route('/dev/submit-idm', methods=['POST'])
def dev_submit_idm():
    """開発モード：手動IDM送信"""
    from flask import request
    if not DEV_MODE:
        return "Development mode is not enabled", 403
    idm = request.form.get('idm', '').strip().upper()
    if not idm:
        return redirect(url_for('dev_manual_scan'))
    logger.info(f"Development mode: Manual IDM input: {idm}")
    return redirect(url_for('result', idm=idm))

@app.route('/auth/code/input')
def auth_code_input():
    ensure_db_initialized()
    return render_template("auth_code_input.html")

@app.route('/auth/code/verify', methods=['POST'])
def auth_code_verify():
    import requests  # 遅延
    from flask import request
    ensure_db_initialized()

    code = request.form.get('code', '').strip()
    if not code:
        return render_template("auth_code_input.html", message='コードを入力してください', error=True)

    try:
        response = requests.post(
            f"{DRIVER_API_URL}/api/bus/verify-code",
            json={'code': code},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            bus_info = data['bus']
            departure_dt = datetime.fromisoformat(bus_info['departure_time'])

            new_bus = auth(
                busid=bus_info['busid'],
                departure_time=departure_dt,
                ud=bus_info['ud']
            )
            db.session.add(new_bus)
            db.session.commit()

            logger.info(f"Bus configured with code {code}: Bus{bus_info['busid']} at {departure_dt}")

            os.environ['ID'] = str(bus_info['busid'])
            return redirect(url_for('home'))

        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
            error_message = error_data.get('error', 'コード検証に失敗しました')
            logger.warning(f"Code verification failed: {code}, status: {response.status_code}")
            return render_template("auth_code_input.html", message=error_message, error=True)

    except requests.RequestException as e:
        logger.error(f"Error connecting to driver service: {e}")
        return render_template("auth_code_input.html", message='ドライバーシステムとの通信に失敗しました', error=True)
    except Exception as e:
        logger.error(f"Error setting bus from code: {e}")
        db.session.rollback()
        return render_template("auth_code_input.html", message='バス設定中にエラーが発生しました', error=True)

@app.route('/auth/data_get')
def auth_data_get():
    import requests  # 遅延
    ensure_db_initialized()
    try:
        number = int(os.environ.get('ID', 0))
        response = requests.get(
            f"{STUDENT_API_URL}/auth/getbus",
            json={'number': number},
            timeout=10
        )
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

# =========================
# main
# =========================
if __name__ == '__main__':
    logger.info('Auth system ready')
    # マイコン/ラズパイ前提：debug無効、threadedでI/O待ち（NFC待ち）に耐える
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
