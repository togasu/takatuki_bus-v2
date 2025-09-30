#!/usr/bin/env python3
"""
統計情報取得API
adminサービスからの統計データ要求に対応
"""

from flask import Blueprint, request, jsonify
from ..database import db
from ..models.user import User
from ..models.reservation import Reservation
from ..models.cancel import Cancel
from ..models.bus import Bus
from ..models.seat import Seat
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_
import logging

# ログの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

statistics_api_bp = Blueprint('statistics_api', __name__, url_prefix='/api/statistics')

@statistics_api_bp.route('/user_registrations', methods=['GET'])
def get_user_registration_statistics():
    """学期期間中における登録者の推移を取得（1日単位）"""
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # デフォルト期間（学期期間: 4月〜1月）
        if not start_date_str:
            current_year = datetime.now().year
            if datetime.now().month >= 4:
                start_date = datetime(current_year, 4, 1)
            else:
                start_date = datetime(current_year-1, 4, 1)
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        
        if not end_date_str:
            current_year = datetime.now().year
            if datetime.now().month >= 4:
                end_date = datetime(current_year+1, 1, 31)
            else:
                end_date = datetime(current_year, 1, 31)
        else:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        # 日別の登録者数を取得
        daily_data = []
        cumulative_count = 0
        current_date = start_date
        
        while current_date <= end_date:
            # その日の登録者数を取得
            day_start = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = current_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            daily_count = User.query.filter(
                and_(
                    User.regist_now_time >= day_start,
                    User.regist_now_time <= day_end
                )
            ).count()
            
            cumulative_count += daily_count
            
            daily_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': daily_count,
                'cumulative': cumulative_count
            })
            
            current_date += timedelta(days=1)
        
        # Chart.js用のデータフォーマット
        chart_data = {
            'labels': [item['date'] for item in daily_data],
            'datasets': [
                {
                    'label': '日別登録者数',
                    'data': [item['count'] for item in daily_data],
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'tension': 0.1,
                    'yAxisID': 'y'
                },
                {
                    'label': '累積登録者数',
                    'data': [item['cumulative'] for item in daily_data],
                    'borderColor': 'rgb(255, 99, 132)',
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                    'tension': 0.1,
                    'yAxisID': 'y1'
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'total_registrations': cumulative_count,
            'daily_data': daily_data,
            'chart_data': chart_data
        })
        
    except Exception as e:
        logger.error(f"Error getting user registration statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'ユーザー登録統計の取得に失敗しました: {str(e)}'
        }), 500

@statistics_api_bp.route('/bus_reservations', methods=['GET'])
def get_bus_reservation_statistics():
    """バス予約時間統計を取得"""
    try:
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        granularity = request.args.get('granularity', '1min')  # 1min, 1hour, 1day, 1week
        
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # 時間の粒度に応じて集計
        if granularity == '1min':
            # 1分単位で1日を横幅とする
            reservation_data = get_reservation_data_by_minute(target_date)
            chart_title = f'{date_str} バス予約時間（1分単位）'
        elif granularity == '1hour':
            # 1時間単位で1日を横幅とする
            reservation_data = get_reservation_data_by_hour(target_date)
            chart_title = f'{date_str} バス予約時間（1時間単位）'
        elif granularity == '1day':
            # 1日単位で1月を横幅とする
            reservation_data = get_reservation_data_by_day(target_date)
            chart_title = f'{target_date.strftime("%Y-%m")} バス予約（1日単位）'
        elif granularity == '1week':
            # 7日単位で全期間を横幅とする
            reservation_data = get_reservation_data_by_week(target_date)
            chart_title = f'バス予約統計（週単位）'
        else:
            return jsonify({
                'success': False,
                'message': f'無効な粒度指定: {granularity}'
            }), 400
        
        return jsonify({
            'success': True,
            'date': date_str,
            'granularity': granularity,
            'chart_title': chart_title,
            'reservation_data': reservation_data['data'],
            'chart_data': reservation_data['chart_data']
        })
        
    except Exception as e:
        logger.error(f"Error getting bus reservation statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'バス予約統計の取得に失敗しました: {str(e)}'
        }), 500

@statistics_api_bp.route('/bus_boardings', methods=['GET'])
def get_bus_boarding_statistics():
    """バス乗車時刻統計を取得（approved=1の予約データを利用）"""
    try:
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        granularity = request.args.get('granularity', '1min')
        
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # 乗車データ（approved=1の予約）を取得
        if granularity == '1min':
            boarding_data = get_boarding_data_by_minute(target_date)
            chart_title = f'{date_str} バス乗車時間（1分単位）'
        elif granularity == '1hour':
            boarding_data = get_boarding_data_by_hour(target_date)
            chart_title = f'{date_str} バス乗車時間（1時間単位）'
        elif granularity == '1day':
            boarding_data = get_boarding_data_by_day(target_date)
            chart_title = f'{target_date.strftime("%Y-%m")} バス乗車（1日単位）'
        elif granularity == '1week':
            boarding_data = get_boarding_data_by_week(target_date)
            chart_title = f'バス乗車統計（週単位）'
        else:
            return jsonify({
                'success': False,
                'message': f'無効な粒度指定: {granularity}'
            }), 400
        
        return jsonify({
            'success': True,
            'date': date_str,
            'granularity': granularity,
            'chart_title': chart_title,
            'boarding_data': boarding_data['data'],
            'chart_data': boarding_data['chart_data']
        })
        
    except Exception as e:
        logger.error(f"Error getting bus boarding statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'バス乗車統計の取得に失敗しました: {str(e)}'
        }), 500

@statistics_api_bp.route('/cancellations', methods=['GET'])
def get_cancellation_statistics():
    """キャンセル時刻統計を取得"""
    try:
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        granularity = request.args.get('granularity', '1min')
        
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # キャンセルデータを取得
        if granularity == '1min':
            cancellation_data = get_cancellation_data_by_minute(target_date)
            chart_title = f'{date_str} キャンセル時間（1分単位）'
        elif granularity == '1hour':
            cancellation_data = get_cancellation_data_by_hour(target_date)
            chart_title = f'{date_str} キャンセル時間（1時間単位）'
        else:
            return jsonify({
                'success': False,
                'message': f'キャンセル統計では{granularity}は対応していません'
            }), 400
        
        return jsonify({
            'success': True,
            'date': date_str,
            'granularity': granularity,
            'chart_title': chart_title,
            'cancellation_data': cancellation_data['data'],
            'chart_data': cancellation_data['chart_data']
        })
        
    except Exception as e:
        logger.error(f"Error getting cancellation statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'キャンセル統計の取得に失敗しました: {str(e)}'
        }), 500

@statistics_api_bp.route('/realtime', methods=['GET'])
def get_realtime_statistics():
    """リアルタイム統計データを取得"""
    try:
        current_time = datetime.now()
        today = current_time.date()
        
        # 今日のアクティブな予約数
        active_reservations = Reservation.query.join(Bus).filter(
            func.date(Bus.departure_time) == today,
            Bus.departure_time > current_time
        ).count()
        
        # 今日の承認待ち予約数
        pending_reservations = Reservation.query.join(Bus).filter(
            func.date(Bus.departure_time) == today,
            Reservation.approved == 0
        ).count()
        
        # 今日のバス総数
        total_buses_today = Bus.query.filter(
            func.date(Bus.departure_time) == today
        ).count()
        
        # 現在の乗車予定者数（今後1時間以内の出発便）
        one_hour_later = current_time + timedelta(hours=1)
        current_passengers = Reservation.query.join(Bus).filter(
            Bus.departure_time >= current_time,
            Bus.departure_time <= one_hour_later,
            Reservation.approved == 1
        ).count()
        
        # 今日のキャンセル数
        cancellations_today = Cancel.query.filter(
            func.date(Cancel.cancel_time) == today
        ).count()
        
        return jsonify({
            'success': True,
            'timestamp': current_time.isoformat(),
            'active_reservations': active_reservations,
            'pending_reservations': pending_reservations,
            'total_buses_today': total_buses_today,
            'current_passengers': current_passengers,
            'cancellations_today': cancellations_today,
            'system_status': 'operational'
        })
        
    except Exception as e:
        logger.error(f"Error getting realtime statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'リアルタイム統計の取得に失敗しました: {str(e)}'
        }), 500

# ヘルパー関数群
def get_reservation_data_by_minute(target_date):
    """1分単位の予約データを取得"""
    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = datetime.combine(target_date, datetime.max.time())
    
    # 1分毎のデータ配列を作成（00:00-23:59）
    minute_data = {}
    for hour in range(24):
        for minute in range(60):
            time_key = f"{hour:02d}:{minute:02d}"
            minute_data[time_key] = 0
    
    # 予約データを取得して集計
    reservations = Reservation.query.filter(
        and_(
            Reservation.reserved_time >= day_start,
            Reservation.reserved_time <= day_end
        )
    ).all()
    
    for reservation in reservations:
        if reservation.reserved_time:
            time_key = reservation.reserved_time.strftime('%H:%M')
            if time_key in minute_data:
                minute_data[time_key] += 1
    
    # Chart.js用のデータを準備
    labels = list(minute_data.keys())
    data_values = list(minute_data.values())
    
    return {
        'data': [{'time': k, 'count': v} for k, v in minute_data.items()],
        'chart_data': {
            'labels': labels,
            'datasets': [{
                'label': '予約数',
                'data': data_values,
                'borderColor': 'rgb(54, 162, 235)',
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'tension': 0.1
            }]
        }
    }

def get_reservation_data_by_hour(target_date):
    """1時間単位の予約データを取得"""
    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = datetime.combine(target_date, datetime.max.time())
    
    hour_data = {}
    for hour in range(24):
        time_key = f"{hour:02d}:00"
        hour_data[time_key] = 0
    
    reservations = Reservation.query.filter(
        and_(
            Reservation.reserved_time >= day_start,
            Reservation.reserved_time <= day_end
        )
    ).all()
    
    for reservation in reservations:
        if reservation.reserved_time:
            time_key = f"{reservation.reserved_time.hour:02d}:00"
            hour_data[time_key] += 1
    
    labels = list(hour_data.keys())
    data_values = list(hour_data.values())
    
    return {
        'data': [{'time': k, 'count': v} for k, v in hour_data.items()],
        'chart_data': {
            'labels': labels,
            'datasets': [{
                'label': '予約数',
                'data': data_values,
                'borderColor': 'rgb(54, 162, 235)',
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'tension': 0.1
            }]
        }
    }

def get_reservation_data_by_day(target_date):
    """1日単位で1月間の予約データを取得"""
    # 月の開始と終了日を計算
    month_start = target_date.replace(day=1)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)
    
    daily_data = {}
    current_date = month_start
    while current_date <= month_end:
        daily_data[current_date.strftime('%Y-%m-%d')] = 0
        current_date += timedelta(days=1)
    
    # データベースから月間の予約データを取得
    month_start_dt = datetime.combine(month_start, datetime.min.time())
    month_end_dt = datetime.combine(month_end, datetime.max.time())
    
    reservations = Reservation.query.filter(
        and_(
            Reservation.reserved_time >= month_start_dt,
            Reservation.reserved_time <= month_end_dt
        )
    ).all()
    
    for reservation in reservations:
        if reservation.reserved_time:
            date_key = reservation.reserved_time.strftime('%Y-%m-%d')
            if date_key in daily_data:
                daily_data[date_key] += 1
    
    labels = list(daily_data.keys())
    data_values = list(daily_data.values())
    
    return {
        'data': [{'time': k, 'count': v} for k, v in daily_data.items()],
        'chart_data': {
            'labels': labels,
            'datasets': [{
                'label': '予約数',
                'data': data_values,
                'borderColor': 'rgb(54, 162, 235)',
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'tension': 0.1
            }]
        }
    }

def get_reservation_data_by_week(target_date):
    """7日単位で週間の予約データを取得"""
    # 学期期間を設定（4月〜1月）
    current_year = target_date.year
    if target_date.month >= 4:
        semester_start = date(current_year, 4, 1)
        semester_end = date(current_year + 1, 1, 31)
    else:
        semester_start = date(current_year - 1, 4, 1)
        semester_end = date(current_year, 1, 31)
    
    # 週単位でデータを集計
    weekly_data = {}
    current_date = semester_start
    
    while current_date <= semester_end:
        # その週の開始日（月曜日）を取得
        week_start = current_date - timedelta(days=current_date.weekday())
        week_key = week_start.strftime('%Y-%m-%d')
        
        if week_key not in weekly_data:
            weekly_data[week_key] = 0
        
        current_date += timedelta(days=7)
    
    # データベースから学期間の予約データを取得
    semester_start_dt = datetime.combine(semester_start, datetime.min.time())
    semester_end_dt = datetime.combine(semester_end, datetime.max.time())
    
    reservations = Reservation.query.filter(
        and_(
            Reservation.reserved_time >= semester_start_dt,
            Reservation.reserved_time <= semester_end_dt
        )
    ).all()
    
    for reservation in reservations:
        if reservation.reserved_time:
            reservation_date = reservation.reserved_time.date()
            week_start = reservation_date - timedelta(days=reservation_date.weekday())
            week_key = week_start.strftime('%Y-%m-%d')
            if week_key in weekly_data:
                weekly_data[week_key] += 1
    
    labels = list(weekly_data.keys())
    data_values = list(weekly_data.values())
    
    return {
        'data': [{'time': k, 'count': v} for k, v in weekly_data.items()],
        'chart_data': {
            'labels': labels,
            'datasets': [{
                'label': '予約数',
                'data': data_values,
                'borderColor': 'rgb(54, 162, 235)',
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'tension': 0.1
            }]
        }
    }

def get_boarding_data_by_minute(target_date):
    """1分単位の乗車データ（approved=1）を取得"""
    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = datetime.combine(target_date, datetime.max.time())
    
    minute_data = {}
    for hour in range(24):
        for minute in range(60):
            time_key = f"{hour:02d}:{minute:02d}"
            minute_data[time_key] = 0
    
    # 承認済み予約（乗車済み）を取得
    boardings = Reservation.query.join(Bus).filter(
        and_(
            func.date(Bus.departure_time) == target_date,
            Reservation.approved == 1
        )
    ).all()
    
    for boarding in boardings:
        if boarding.bus and boarding.bus.departure_time:
            time_key = boarding.bus.departure_time.strftime('%H:%M')
            if time_key in minute_data:
                minute_data[time_key] += 1
    
    labels = list(minute_data.keys())
    data_values = list(minute_data.values())
    
    return {
        'data': [{'time': k, 'count': v} for k, v in minute_data.items()],
        'chart_data': {
            'labels': labels,
            'datasets': [{
                'label': '乗車数',
                'data': data_values,
                'borderColor': 'rgb(255, 99, 132)',
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'tension': 0.1
            }]
        }
    }

def get_boarding_data_by_hour(target_date):
    """1時間単位の乗車データを取得"""
    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = datetime.combine(target_date, datetime.max.time())
    
    hour_data = {}
    for hour in range(24):
        time_key = f"{hour:02d}:00"
        hour_data[time_key] = 0
    
    boardings = Reservation.query.join(Bus).filter(
        and_(
            func.date(Bus.departure_time) == target_date,
            Reservation.approved == 1
        )
    ).all()
    
    for boarding in boardings:
        if boarding.bus and boarding.bus.departure_time:
            time_key = f"{boarding.bus.departure_time.hour:02d}:00"
            hour_data[time_key] += 1
    
    labels = list(hour_data.keys())
    data_values = list(hour_data.values())
    
    return {
        'data': [{'time': k, 'count': v} for k, v in hour_data.items()],
        'chart_data': {
            'labels': labels,
            'datasets': [{
                'label': '乗車数',
                'data': data_values,
                'borderColor': 'rgb(255, 99, 132)',
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'tension': 0.1
            }]
        }
    }

def get_boarding_data_by_day(target_date):
    """1日単位で1月間の乗車データを取得"""
    month_start = target_date.replace(day=1)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)
    
    daily_data = {}
    current_date = month_start
    while current_date <= month_end:
        daily_data[current_date.strftime('%Y-%m-%d')] = 0
        current_date += timedelta(days=1)
    
    boardings = Reservation.query.join(Bus).filter(
        and_(
            func.date(Bus.departure_time) >= month_start,
            func.date(Bus.departure_time) <= month_end,
            Reservation.approved == 1
        )
    ).all()
    
    for boarding in boardings:
        if boarding.bus and boarding.bus.departure_time:
            date_key = boarding.bus.departure_time.strftime('%Y-%m-%d')
            if date_key in daily_data:
                daily_data[date_key] += 1
    
    labels = list(daily_data.keys())
    data_values = list(daily_data.values())
    
    return {
        'data': [{'time': k, 'count': v} for k, v in daily_data.items()],
        'chart_data': {
            'labels': labels,
            'datasets': [{
                'label': '乗車数',
                'data': data_values,
                'borderColor': 'rgb(255, 99, 132)',
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'tension': 0.1
            }]
        }
    }

def get_boarding_data_by_week(target_date):
    """7日単位で週間の乗車データを取得"""
    current_year = target_date.year
    if target_date.month >= 4:
        semester_start = date(current_year, 4, 1)
        semester_end = date(current_year + 1, 1, 31)
    else:
        semester_start = date(current_year - 1, 4, 1)
        semester_end = date(current_year, 1, 31)
    
    weekly_data = {}
    current_date = semester_start
    
    while current_date <= semester_end:
        week_start = current_date - timedelta(days=current_date.weekday())
        week_key = week_start.strftime('%Y-%m-%d')
        
        if week_key not in weekly_data:
            weekly_data[week_key] = 0
        
        current_date += timedelta(days=7)
    
    boardings = Reservation.query.join(Bus).filter(
        and_(
            func.date(Bus.departure_time) >= semester_start,
            func.date(Bus.departure_time) <= semester_end,
            Reservation.approved == 1
        )
    ).all()
    
    for boarding in boardings:
        if boarding.bus and boarding.bus.departure_time:
            boarding_date = boarding.bus.departure_time.date()
            week_start = boarding_date - timedelta(days=boarding_date.weekday())
            week_key = week_start.strftime('%Y-%m-%d')
            if week_key in weekly_data:
                weekly_data[week_key] += 1
    
    labels = list(weekly_data.keys())
    data_values = list(weekly_data.values())
    
    return {
        'data': [{'time': k, 'count': v} for k, v in weekly_data.items()],
        'chart_data': {
            'labels': labels,
            'datasets': [{
                'label': '乗車数',
                'data': data_values,
                'borderColor': 'rgb(255, 99, 132)',
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'tension': 0.1
            }]
        }
    }

def get_cancellation_data_by_minute(target_date):
    """1分単位のキャンセルデータを取得"""
    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = datetime.combine(target_date, datetime.max.time())
    
    minute_data = {}
    for hour in range(24):
        for minute in range(60):
            time_key = f"{hour:02d}:{minute:02d}"
            minute_data[time_key] = 0
    
    cancellations = Cancel.query.filter(
        and_(
            Cancel.cancel_time >= day_start,
            Cancel.cancel_time <= day_end
        )
    ).all()
    
    for cancellation in cancellations:
        if cancellation.cancel_time:
            time_key = cancellation.cancel_time.strftime('%H:%M')
            if time_key in minute_data:
                minute_data[time_key] += 1
    
    labels = list(minute_data.keys())
    data_values = list(minute_data.values())
    
    return {
        'data': [{'time': k, 'count': v} for k, v in minute_data.items()],
        'chart_data': {
            'labels': labels,
            'datasets': [{
                'label': 'キャンセル数',
                'data': data_values,
                'borderColor': 'rgb(255, 205, 86)',
                'backgroundColor': 'rgba(255, 205, 86, 0.2)',
                'tension': 0.1
            }]
        }
    }

def get_cancellation_data_by_hour(target_date):
    """1時間単位のキャンセルデータを取得"""
    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = datetime.combine(target_date, datetime.max.time())
    
    hour_data = {}
    for hour in range(24):
        time_key = f"{hour:02d}:00"
        hour_data[time_key] = 0
    
    cancellations = Cancel.query.filter(
        and_(
            Cancel.cancel_time >= day_start,
            Cancel.cancel_time <= day_end
        )
    ).all()
    
    for cancellation in cancellations:
        if cancellation.cancel_time:
            time_key = f"{cancellation.cancel_time.hour:02d}:00"
            hour_data[time_key] += 1
    
    labels = list(hour_data.keys())
    data_values = list(hour_data.values())
    
    return {
        'data': [{'time': k, 'count': v} for k, v in hour_data.items()],
        'chart_data': {
            'labels': labels,
            'datasets': [{
                'label': 'キャンセル数',
                'data': data_values,
                'borderColor': 'rgb(255, 205, 86)',
                'backgroundColor': 'rgba(255, 205, 86, 0.2)',
                'tension': 0.1
            }]
        }
    }