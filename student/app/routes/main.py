from flask import Blueprint, render_template, request, redirect, url_for
import configparser
import os
from datetime import datetime, timedelta
from ..models.bus import db, Bus
from ..models.reservation import Reservation
from ..utils.auth_utils import check_session

main_bp = Blueprint('main', __name__)

@main_bp.route('/personal')
def personal(): 
    token = request.cookies.get('token')
    data = check_session(token)
    if not data or not isinstance(data, dict) or data.get('flag') == False:
        return redirect(url_for('auth.top'))
    
    # adminユーザーの場合とstudentユーザーの場合で処理を分ける
    if data.get('type') == 'admin_user':
        # adminユーザーの場合
        username = data.get('username', 'Admin')
        user_full_name = request.cookies.get('user_full_name', f'Admin {username}')
        name = f"Admin ({username})"
        
        # adminユーザーは予約履歴なしでダッシュボードを表示
        personal_data = []
        print(f"Debug: Admin user accessing personal page - name={name}, username={username}")
    else:
        # 学生ユーザーの場合（既存のロジック）
        student_id = data.get('student_id')
        if not student_id or not isinstance(student_id, str):
            return redirect(url_for('auth.top'))
        
        # 学部生の場合
        if len(student_id) == 6:
            name = student_id[:2] + "-" + student_id[-4:]
        # 大学院生の場合
        elif len(student_id) > 2 and student_id[2] == "1":
            name = str(student_id[:2]) + "M" + str(student_id[4:])
        # 博士生の場合
        else:
            name = student_id[:2] + "D" + student_id[4:]
        
        user_full_name = request.cookies.get('user_full_name', '名前不明')
        username = user_full_name
        
        # 個人の情報取得
        bookedseat = db.session.query(Reservation).filter_by(user_id=student_id).order_by(Reservation.bus_id).all()
        print(f"予約検索: student_id={student_id}, 見つかった予約数={len(bookedseat)}")
        personal_data = []
        if bookedseat:
            print(bookedseat)
            for booked in bookedseat[:]:
                bus = db.session.query(Bus).filter_by(id=booked.bus_id).first()
                if bus:  # busが存在することを確認
                    dt = bus.departure_time.date()
                    if datetime.now().date() > dt:
                        bookedseat.remove(booked)
                    else:
                        personal_data.append({
                            "departure_time": str(bus.departure_time.strftime('%m/%d %H:%M')),
                            "seat_number": booked.seat_number,
                            "busid": bus.busid
                        })
                        print(f"dearture_time:{str(bus.departure_time.strftime('%m/%d %H:%M'))}, bus_id:{booked.bus_id}, seat_number:{booked.seat_number}")
    
    print(f"Debug: name={name}, user_full_name={user_full_name}")
    current_time = datetime.now()
    firstbus = db.session.query(Bus).filter(Bus.departure_time > current_time).order_by(Bus.departure_time).first()

    current = []  # 空席数
    
    if firstbus is not None:
        currentbuses = db.session.query(Bus).filter(Bus.departure_time >= firstbus.departure_time, Bus.status != 2).order_by(Bus.departure_time).limit(10).all()

        for currentbus in currentbuses:
            total_seats = currentbus.seats
            reserved_seats = db.session.query(Reservation).filter_by(bus_id=currentbus.id).count()
            available_seats = total_seats - reserved_seats
            print(f"最寄りのバス -busID: {currentbus.id}, departure_time: {currentbus.departure_time}, available_seatnumber: {available_seats}")
            current.append({
                "available_seats": available_seats,
                "departure_time": str(currentbus.departure_time.strftime('%m/%d %H:%M')),
                "busid": currentbus.busid
            })
            if(len(current) >= 5):
                break

    return render_template('personal.html', name=name, user_full_name=user_full_name, username=username, current=current, personal_data=personal_data)

@main_bp.route('/personal/tips')
def tips():
    try:
        config_ini = configparser.ConfigParser()
        # 設定ファイルのパスを修正
        import os
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'setting.ini')
        config_ini.read(config_path, encoding='utf-8')
        
        # 設定ファイルが読み込めない場合のデフォルトテキスト
        if config_ini.has_section('Personal') and config_ini.has_option('Personal', 'Text'):
            text = config_ini.get('Personal', 'Text').strip()
        else:
            text = "利用案内の情報を読み込んでいます..."
            
    except Exception as e:
        # エラーが発生した場合のデフォルトテキスト
        text = "利用案内の情報を読み込めませんでした。"
        print(f"Error reading config file: {e}")
    
    return render_template('tips.html', text=text)

@main_bp.route('/checknumber/<seatnumber>')
def checknumber(seatnumber):
    number = int(seatnumber)
    seat = []
    for i in range(1, 28):
        if i == number:
            seat.append('2')
        else:
            seat.append('0')
    return render_template('checkseatnumber.html', seat=seat)
