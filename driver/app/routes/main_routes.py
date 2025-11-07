"""ドライバーシステムのメインルーティング（元のmain.py互換）"""

from flask import Blueprint, render_template, request, g
from datetime import datetime, timedelta
from app.utils.helper_functions import get_authenticated_user, hash_check, hash_login, verify_password, yukisaki
from app.models import Bus, Driver
from app.database import db
import logging
import json

logger = logging.getLogger('sojo-bus-log')

main_bp = Blueprint('main', __name__)


@main_bp.after_request
def apply_cookies(response):
    """responseなしでhashに追加を行うための補助関数"""
    if hasattr(g, 'cookies'):
        for key, value in g.cookies.items():
            response.set_cookie(key, value)
    return response


def gakusei(username):
    """学生番号のフォーマット"""
    if len(username) in [1, 2, 3, 4]:
        username = "driver" + username
    elif len(username) < 6:
        username = "使用不可"
    elif len(username) == 6:
        username = "情" + username[:2] + "-" + username[-4:]
    # 大学院生の場合
    elif str(username)[2] == "1":
        username = "情" + str(username[:2]) + "M" + str(username[4:])
    else:
        username = "情" + username[:2] + "D" + username[4:]
    return username


def topview(message):
    """topルーティングとloginregister以外で使うとき"""
    num = request.cookies.get('hashed_num')
    user = hash_check(num)
    if not user:
        return render_template('login.html')
    
    num = int(user[6])
    now = datetime.now()
    try:
        firstbus = db.session.query(Bus).filter(Bus.departure_time > datetime.now(), Bus.busid==num).first()
        if firstbus:
            firstbusdate = firstbus.departure_time
            ud = yukisaki(firstbus.ud)
            firstbus = {"busid": firstbus.busid, "departure_time": str(firstbus.departure_time.strftime('%m/%d %H:%M')), "ud": ud}
            firstbus = str(f"行き先|{firstbus['ud']}  出発時刻|{firstbus['departure_time']} {firstbus['busid']}号車")
        else:
            firstbus = "バスがありません"
    except:
        firstbus = "バスがありません"
    
    try:
        if 'firstbusdate' in locals():
            secoundbus = db.session.query(Bus).filter(Bus.departure_time > firstbusdate, Bus.busid==num).first()
            if secoundbus:
                ud = yukisaki(secoundbus.ud)
                secoundbus = {"busid": secoundbus.busid, "departure_time": str(secoundbus.departure_time.strftime('%m/%d %H:%M')), "ud": ud}
                secoundbus = str(f"行き先|{secoundbus['ud']}  出発時刻|{secoundbus['departure_time']} {secoundbus['busid']}号車")
            else:
                secoundbus = "バスがありません"
        else:
            secoundbus = "バスがありません"
    except:
        secoundbus = "バスがありません"
    
    return render_template('top.html', firstbus=firstbus, secoundbus=secoundbus, message=message)


@main_bp.route('/login')
def login():
    """ログイン画面"""
    return render_template('login.html')


@main_bp.route('/login/register', methods=['POST'])
def login_register():
    """ログイン処理"""
    username = request.form['username']
    password = request.form['password']
    print(f"login: {username},{password}")
    
    user = db.session.query(Driver).filter_by(username=username).first()
    if user:
        stored_password = user.password
        stored_salt = user.salt
        if not verify_password(stored_password, stored_salt, password):
            return render_template('login.html', message='パスワードが間違っています')
    else:
        return render_template('login.html', message='ユーザー名が間違っています')
    
    hashed_num = hash_login(username)
    print(f"hash : {hashed_num}")
    if hashed_num is None:
        return render_template('login.html', message='Hash化に失敗しました')
    
    try:
        firstbus = db.session.query(Bus).filter(Bus.departure_time > datetime.now(), Bus.busid == int(user.username[6])).first()
        if firstbus:
            firstbusdate = firstbus.departure_time
            ud = yukisaki(firstbus.ud)
            firstbus = {"busid": firstbus.busid, "departure_time": str(firstbus.departure_time.strftime('%m/%d %H:%M')), "ud": ud}
            firstbus = str(f"行き先|{firstbus['ud']}  出発時刻|{firstbus['departure_time']} {firstbus['busid']}号車")
        else:
            firstbus = "バスがありません"
            
        try:
            if 'firstbusdate' in locals():
                secoundbus = db.session.query(Bus).filter(Bus.departure_time > firstbusdate, Bus.busid == int(user.username[6])).first()
                if secoundbus:
                    ud = yukisaki(secoundbus.ud)
                    secoundbus = {"busid": secoundbus.busid, "departure_time": str(secoundbus.departure_time.strftime('%m/%d %H:%M')), "ud": ud}
                    secoundbus = str(f"行き先|{secoundbus['ud']}  出発時刻|{secoundbus['departure_time']} {secoundbus['busid']}号車")
                else:
                    secoundbus = "バスがありません"
            else:
                secoundbus = "バスがありません"
        except:
            secoundbus = "バスがありません"
        
        return render_template('top.html', firstbus=firstbus, secoundbus=secoundbus)
    except:
        return render_template('login.html', message='Hash化に失敗しました')


@main_bp.route('/login<num>')
def drivernumlogin(num):
    """運転手用の特殊ログイン"""
    username = 'driver' + str(num)
    try:
        user = db.session.query(Driver).filter_by(username=username).first()
        if not user:
            return render_template('login.html', message='ユーザー名が間違っています')
        hash_login(username)
        logger.info(f"success to login unten driver {num}")
        return topview('運転手用特殊ログインを行いました')
    except:
        pass
    return render_template('login.html', message='ユーザーログインに失敗しました')


@main_bp.route('/top')
def top():
    """topページ"""
    try:
        hashed_num = request.cookies.get('hashed_num')
        try:
            user = hash_check(hashed_num)
            if not user:
                return render_template('login.html')
            
            try:
                firstbus = db.session.query(Bus).filter(Bus.departure_time > datetime.now(), Bus.busid == int(user[6])).first()
                if firstbus:
                    firstbusdate = firstbus.departure_time
                    ud = yukisaki(firstbus.ud)
                    firstbus = {"busid": firstbus.busid, "departure_time": str(firstbus.departure_time.strftime('%m/%d %H:%M')), "ud": ud}
                    firstbus = str(f"行き先|{firstbus['ud']}  出発時刻|{firstbus['departure_time']} {firstbus['busid']}号車")
                else:
                    firstbus = "バスがありません"
            except:
                firstbus = "バスがありません"
            
            try:
                if 'firstbusdate' in locals():
                    secoundbus = db.session.query(Bus).filter(Bus.departure_time > firstbusdate, Bus.busid == int(user[6])).first()
                    if secoundbus:
                        ud = yukisaki(secoundbus.ud)
                        secoundbus = {"busid": secoundbus.busid, "departure_time": str(secoundbus.departure_time.strftime('%m/%d %H:%M')), "ud": ud}
                        secoundbus = str(f"行き先|{secoundbus['ud']}  出発時刻|{secoundbus['departure_time']} {secoundbus['busid']}号車")
                    else:
                        secoundbus = "バスがありません"
                else:
                    secoundbus = "バスがありません"
            except:
                secoundbus = "バスがありません"
            
            return render_template('top.html', firstbus=firstbus, secoundbus=secoundbus)
        except:
            print("error")
    except:
        pass
    return render_template('login.html')


@main_bp.route('/bus')
def bus():
    """バスの運行便設定選択画面"""
    hashed_num = request.cookies.get('hashed_num')
    if hashed_num:
        user = hash_check(hashed_num)
        if user:
            driver_obj = db.session.query(Driver).filter_by(username=user).first()
            if driver_obj:
                number = driver_obj.number
                now = datetime.now()
                busdate = db.session.query(Bus).filter(Bus.departure_time > now, Bus.busid == number).order_by(Bus.departure_time).limit(5).all()
                print(busdate)
                bus_date = []
                for bus in busdate:
                    bus_date.append({
                        "id": bus.id,
                        "busid": bus.busid,
                        "departure_time": str(bus.departure_time.strftime('%m/%d %H:%M')),
                        "seats": bus.seats,
                        "ud": bus.ud
                    })
                return render_template('bus.html', bus_date=bus_date, number=number)
    return render_template('login.html')


@main_bp.route('/bus/register')
def bus_register():
    """バスの運行便設定"""
    hashed_num = request.cookies.get('hashed_num')
    if hashed_num:
        user = hash_check(hashed_num)
        if user:
            user_obj = Driver.query.filter_by(username=user).first()
            if user_obj:
                id = request.args.get('id')
                if not id:
                    return render_template('bus_register.html', message='バスIDと出発時刻を選択してください')
                print(id)
                businfo = db.session.query(Bus).filter_by(id=id).first()
                if businfo:
                    bus = {
                        "id": businfo.id,
                        "busid": businfo.busid,
                        "departure_time": str(businfo.departure_time.strftime('%Y/%m/%d %H:%M')),
                        "seats": businfo.seats,
                        "ud": businfo.ud
                    }
                    departure_time = bus["departure_time"]
                    bus_id = bus["busid"]
                    with open(f'../yoyaku_system/bus{bus_id}.json', 'w') as file:
                        json.dump(bus, file)
                        logger.info(f"success to register unten bus {bus_id}, departure_time {departure_time} bus_id {bus_id}")
                    return render_template('bus_register.html', bus_id=bus_id, departure_time=departure_time)
    return render_template('login.html')