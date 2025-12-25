"""ドライバーシステムのメインルーティング（元のmain.py互換）"""

from flask import Blueprint, render_template, request, g
from datetime import datetime, timedelta
from app.utils.helper_functions import get_authenticated_user, hash_check, hash_login, verify_password, yukisaki, gakusei
from app.utils.student_api_client import get_student_client
from app.models import Driver
from app.database import db
import logging
import json

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)


@main_bp.after_request
def apply_cookies(response):
    """responseなしでhashに追加を行うための補助関数"""
    if hasattr(g, 'cookies'):
        for key, value in g.cookies.items():
            response.set_cookie(key, value)
    return response


def get_next_two_buses(bus_number=None):
    """次の2つのバスを取得（全てのバスから）
    
    Args:
        bus_number: 後方互換性のため残していますが使用されません
    """
    try:
        client = get_student_client()
        buses = client.get_all_upcoming_buses(limit=2)
        
        firstbus = "バスがありません"
        secondbus = "バスがありません"
        
        if len(buses) > 0:
            bus_data = buses[0]
            departure_dt = datetime.fromisoformat(bus_data['departure_time'])
            ud = yukisaki(bus_data['ud'])
            firstbus = f"行き先|{ud}  出発時刻|{departure_dt.strftime('%m/%d %H:%M')} {bus_data['busid']}番"
        
        if len(buses) > 1:
            bus_data = buses[1]
            departure_dt = datetime.fromisoformat(bus_data['departure_time'])
            ud = yukisaki(bus_data['ud'])
            secondbus = f"行き先|{ud}  出発時刻|{departure_dt.strftime('%m/%d %H:%M')} {bus_data['busid']}番"
        
        return firstbus, secondbus
    except Exception as e:
        logger.error(f"Error getting next buses: {e}")
        return "バスがありません", "バスがありません"


def topview(message):
    """topルーティングとloginregister以外で使うとき"""
    # Redis優先で認証ユーザーを取得
    user = get_authenticated_user()
    if not user:
        return render_template('login.html')

    # usernameからバス番号を抽出（例: driver1 -> 1）
    try:
        bus_number = int(user.replace('driver', ''))
    except (ValueError, AttributeError):
        logger.error(f"Invalid username format: {user}")
        return render_template('login.html', message='ユーザー名の形式が正しくありません')

    firstbus, secondbus = get_next_two_buses(bus_number)
    return render_template('top.html', firstbus=firstbus, secoundbus=secondbus, message=message)


@main_bp.route('/login')
def login():
    """ログイン画面"""
    return render_template('login.html')


@main_bp.route('/login/register', methods=['POST'])
def login_register():
    """ログイン処理"""
    username = request.form['username']
    password = request.form['password']
    logger.info(f"Login attempt: {username}")
    
    user = db.session.query(Driver).filter_by(username=username).first()
    if user:
        stored_password = user.password
        stored_salt = user.salt
        if not verify_password(stored_password, stored_salt, password):
            return render_template('login.html', message='パスワードが間違っています')
    else:
        return render_template('login.html', message='ユーザー名が間違っています')
    
    hashed_num = hash_login(username)
    logger.info(f"Hash generated: {hashed_num}")
    logger.info(f"g.cookies: {getattr(g, 'cookies', {})}")
    if hashed_num is None:
        return render_template('login.html', message='Hash化に失敗しました')
    
    # usernameからバス番号を抽出
    try:
        bus_number = int(username.replace('driver', ''))
        firstbus, secondbus = get_next_two_buses(bus_number)
        response = render_template('top.html', firstbus=firstbus, secoundbus=secondbus)
        logger.info(f"Login successful for {username}, cookies will be set via after_request")
        return response
    except Exception as e:
        logger.error(f"Error in login_register: {e}")
        return render_template('login.html', message='ログイン処理中にエラーが発生しました')


@main_bp.route('/login<num>')
def drivernumlogin(num):
    """運転手用の特殊ログイン - MACアドレス認証必須"""
    from app.utils.device_auth import validate_device_access, get_client_mac_address
    
    username = 'driver' + str(num)
    
    # まずMACアドレスが取得できるか確認
    mac_address = get_client_mac_address()
    
    # MACアドレスが取得できない場合は、デバイス登録ページを表示
    if not mac_address:
        logger.info(f"No device MAC found for {username}, showing device registration page")
        return render_template('device_register.html', 
                             driver_number=num,
                             message='初回アクセス: デバイスIDを設定してください')
    
    try:
        # ユーザー存在確認
        user = db.session.query(Driver).filter_by(username=username).first()
        if not user:
            logger.warning(f"Login attempt for non-existent user: {username}")
            return render_template('login.html', message='ユーザー名が間違っています')
        
        # デバイス認証
        success, message, device = validate_device_access(user.id, mac_address)
        if not success:
            logger.warning(f"Device authentication failed for {username}: {message}")
            return render_template('login.html', 
                                 message=f'デバイス認証失敗: {message}',
                                 error_detail='このデバイスは登録されていません。管理者にデバイス登録を依頼してください。')
        
        # 認証成功 - ログイン処理
        hash_login(username)
        logger.info(f"Device login successful - User: {username}, Device: {device.device_name}")
        return topview(f'運転手用特殊ログインを行いました（デバイス: {device.device_name}）')
        
    except Exception as e:
        logger.error(f"Error in drivernumlogin: {e}", exc_info=True)
        return render_template('login.html', message='ログイン処理中にエラーが発生しました')
    
    return render_template('login.html', message='ユーザーログインに失敗しました')


@main_bp.route('/top')
def top():
    """topページ"""
    try:
        # Redis優先で認証ユーザーを取得
        user = get_authenticated_user()
        if not user:
            return render_template('login.html')
        
        # usernameからバス番号を抽出
        try:
            bus_number = int(user.replace('driver', ''))
            firstbus, secondbus = get_next_two_buses(bus_number)
            return render_template('top.html', firstbus=firstbus, secoundbus=secondbus)
        except Exception as e:
            logger.error(f"Error in top route: {e}")
            return render_template('login.html', message='エラーが発生しました')
    except Exception as e:
        logger.error(f"Unexpected error in top route: {e}")
        return render_template('login.html')


@main_bp.route('/bus')
def bus():
    """バスの運行便設定選択画面"""
    # Redis優先で認証ユーザーを取得
    user = get_authenticated_user()
    
    logger.info(f"Bus route accessed - Authenticated user: {user}")
    logger.info(f"Cookies received: {dict(request.cookies)}")
    
    if user:
            driver_obj = db.session.query(Driver).filter_by(username=user).first()
            if driver_obj:
                number = driver_obj.number
                
                # Student ServiceのAPIクライアントを使用して全てのバス情報を取得
                client = get_student_client()
                buses = client.get_all_upcoming_buses(limit=10)  # 10便まで表示
                
                logger.info(f"Retrieved {len(buses)} upcoming buses for driver {number}")
                
                bus_date = []
                for bus_data in buses:
                    try:
                        # ISO形式の日時をパース
                        departure_dt = datetime.fromisoformat(bus_data['departure_time'])
                        bus_date.append({
                            "id": bus_data['id'],
                            "busid": bus_data['busid'],
                            "departure_time": departure_dt.strftime('%m/%d %H:%M'),
                            "seats": bus_data['seats'],
                            "ud": bus_data['ud']
                        })
                    except Exception as e:
                        logger.error(f"Error parsing bus data: {e}")
                        continue
                
                return render_template('bus.html', bus_date=bus_date, number=number)
    return render_template('login.html')


@main_bp.route('/bus/register')
def bus_register():
    """バスの運行便設定"""
    # Redis優先で認証ユーザーを取得
    user = get_authenticated_user()
    if user:
            user_obj = Driver.query.filter_by(username=user).first()
            if user_obj:
                bus_id = request.args.get('id')
                if not bus_id:
                    return render_template('bus_register.html', message='バスIDと出発時刻を選択してください')
                
                logger.info(f"Registering bus with ID: {bus_id}")
                
                # Student ServiceのAPIクライアントを使用してバス情報を取得
                client = get_student_client()
                businfo = client.get_bus_by_id(int(bus_id))
                
                if businfo:
                    try:
                        # ISO形式の日時をパース
                        departure_dt = datetime.fromisoformat(businfo['departure_time'])
                        bus = {
                            "id": businfo['id'],
                            "busid": businfo['busid'],
                            "departure_time": departure_dt.strftime('%Y/%m/%d %H:%M'),
                            "seats": businfo['seats'],
                            "ud": businfo['ud']
                        }
                        departure_time = bus["departure_time"]
                        bus_number = bus["busid"]
                        
                        # JSONファイルに保存（互換性のため）
                        with open(f'../yoyaku_system/bus{bus_number}.json', 'w') as file:
                            json.dump(bus, file)
                            logger.info(f"Success to register bus {bus_number}, departure_time {departure_time}")
                        
                        return render_template('bus_register.html', bus_id=bus_number, departure_time=departure_time)
                    except Exception as e:
                        logger.error(f"Error processing bus data: {e}")
                        return render_template('bus_register.html', message='バス情報の処理に失敗しました')
                else:
                    logger.warning(f"Bus not found with ID: {bus_id}")
                    return render_template('bus_register.html', message='指定されたバスが見つかりませんでした')
    return render_template('login.html')