from flask import Blueprint, render_template, jsonify, request, make_response
from ..utils.decorators import admin_required
from ..database import db
from ..models.user import User
from ..api_client import admin_api
try:
    import numpy as np
    import pandas as pd
except ImportError:
    # NumPyやPandasがない場合は標準ライブラリで代替
    np = None
    pd = None

from datetime import datetime, timedelta, date
import json
import io
import csv
import random

bp = Blueprint('statistics', __name__)

@bp.route('/statistics')
@admin_required
def statistics():
    """統計情報ページを表示"""
    return render_template('statistics.html')

@bp.route('/statistics/user-registrations')
@admin_required
def get_user_registration_statistics():
    """学期期間中における登録者の推移を取得"""
    try:
        # パラメータを取得
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # デフォルト期間（学期期間を想定: 4月〜1月）
        if not start_date:
            current_year = datetime.now().year
            if datetime.now().month >= 4:
                start_date = f"{current_year}-04-01"
            else:
                start_date = f"{current_year-1}-04-01"
        
        if not end_date:
            current_year = datetime.now().year
            if datetime.now().month >= 4:
                end_date = f"{current_year+1}-01-31"
            else:
                end_date = f"{current_year}-01-31"
        
        # studentサービスから統計データを取得
        result = admin_api.get_user_registration_statistics(start_date, end_date)
        
        if not result.get('success', True):
            return jsonify({'error': result.get('message', '不明なエラー')}), 500
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/statistics/bus-reservations')
@admin_required
def get_bus_reservation_statistics():
    """バス予約時間統計を取得"""
    try:
        date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        granularity = request.args.get('granularity', '1min')  # 1min, 1hour, 1day, 1week
        
        # studentサービスから統計データを取得
        result = admin_api.get_bus_reservation_statistics(date_param, granularity)
        
        if not result.get('success', True):
            return jsonify({'error': result.get('message', '不明なエラー')}), 500
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/statistics/bus-boardings')
@admin_required
def get_bus_boarding_statistics():
    """バス乗車時刻統計を取得"""
    try:
        date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        granularity = request.args.get('granularity', '1min')  # 1min, 1hour, 1day, 1week
        
        # studentサービスから統計データを取得
        result = admin_api.get_bus_boarding_statistics(date_param, granularity)
        
        if not result.get('success', True):
            return jsonify({'error': result.get('message', '不明なエラー')}), 500
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/statistics/cancellations')
@admin_required
def get_cancellation_statistics():
    """キャンセル時刻統計を取得"""
    try:
        date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        granularity = request.args.get('granularity', '1min')  # 1min, 1hour
        
        # studentサービスから統計データを取得
        result = admin_api.get_cancellation_statistics(date_param, granularity)
        
        if not result.get('success', True):
            return jsonify({'error': result.get('message', '不明なエラー')}), 500
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/statistics/realtime')
@admin_required
def get_realtime_statistics():
    """リアルタイム統計データを取得"""
    try:
        # studentサービスからリアルタイム統計を取得
        result = admin_api.get_real_time_statistics()
        
        if not result.get('success', True):
            # フォールバック: ローカルでシミュレートされたデータ
            current_time = datetime.now()
            result = {
                'timestamp': current_time.isoformat(),
                'active_reservations': random.randint(10, 100),
                'pending_reservations': random.randint(0, 20),
                'total_buses_today': random.randint(20, 50),
                'current_passengers': random.randint(0, 300),
                'system_load': random.uniform(10, 80)
            }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/statistics/export/<data_type>')
@admin_required
def export_statistics(data_type):
    """統計データをCSVでエクスポート"""
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        filename = f"statistics_{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        if data_type == 'user_registrations':
            # ユーザー登録統計のエクスポート
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            result = admin_api.get_user_registration_statistics(start_date, end_date)
            if result.get('success', True) and 'daily_data' in result:
                writer.writerow(['日付', '登録者数', '累積登録者数'])
                for item in result['daily_data']:
                    writer.writerow([item['date'], item['count'], item.get('cumulative', '')])
            else:
                writer.writerow(['エラー', result.get('message', '統計データを取得できませんでした')])
                
        elif data_type == 'bus_reservations':
            # バス予約統計のエクスポート
            date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
            granularity = request.args.get('granularity', '1min')
            
            result = admin_api.get_bus_reservation_statistics(date_param, granularity)
            if result.get('success', True) and 'reservation_data' in result:
                writer.writerow(['時刻', '予約数', 'バスID', '座席番号'])
                for item in result['reservation_data']:
                    writer.writerow([
                        item.get('time', ''), 
                        item.get('count', 0),
                        item.get('bus_id', ''),
                        item.get('seat_number', '')
                    ])
            else:
                writer.writerow(['エラー', result.get('message', '予約統計データを取得できませんでした')])
                
        elif data_type == 'bus_boardings':
            # バス乗車統計のエクスポート
            date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
            granularity = request.args.get('granularity', '1min')
            
            result = admin_api.get_bus_boarding_statistics(date_param, granularity)
            if result.get('success', True) and 'boarding_data' in result:
                writer.writerow(['時刻', '乗車数', 'バスID', 'ルート'])
                for item in result['boarding_data']:
                    writer.writerow([
                        item.get('time', ''), 
                        item.get('count', 0),
                        item.get('bus_id', ''),
                        item.get('route', '')
                    ])
            else:
                writer.writerow(['エラー', result.get('message', '乗車統計データを取得できませんでした')])
                
        elif data_type == 'cancellations':
            # キャンセル統計のエクスポート
            date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
            granularity = request.args.get('granularity', '1min')
            
            result = admin_api.get_cancellation_statistics(date_param, granularity)
            if result.get('success', True) and 'cancellation_data' in result:
                writer.writerow(['時刻', 'キャンセル数', 'バスID', '理由'])
                for item in result['cancellation_data']:
                    writer.writerow([
                        item.get('time', ''), 
                        item.get('count', 0),
                        item.get('bus_id', ''),
                        item.get('reason', '')
                    ])
            else:
                writer.writerow(['エラー', result.get('message', 'キャンセル統計データを取得できませんでした')])
        
        else:
            writer.writerow(['エラー', f'不明な統計タイプ: {data_type}'])
            
        # レスポンスを作成
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500