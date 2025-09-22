from flask import Blueprint, render_template, jsonify, request, make_response
from ..utils.decorators import admin_required
from ..database import db
from ..models.user import User
try:
    import numpy as np
    import pandas as pd
except ImportError:
    # NumPyやPandasがない場合は標準ライブラリで代替
    np = None
    pd = None

from datetime import datetime, timedelta
import json
import io
import csv
import random

bp = Blueprint('statistics', __name__, url_prefix='/admin')

@bp.route('/statistics')
@admin_required
def statistics():
    """統計情報ページを表示"""
    return render_template('statistics.html')

@bp.route('/statistics/data')
@admin_required
def get_statistics_data():
    """統計データを取得"""
    try:
        # ユーザー数の統計
        total_users = User.query.count()
        
        # 日別ユーザー登録数（過去30日）
        daily_registrations = []
        for i in range(29, -1, -1):
            date = datetime.now() - timedelta(days=i)
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            count = User.query.filter(
                User.created_at >= start_date,
                User.created_at <= end_date
            ).count()
            
            daily_registrations.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        
        # 移動平均を計算 (NumPyがあれば使用、なければ手動計算)
        window_size = 7
        moving_avg_data = []
        
        if np and len(daily_registrations) >= window_size:
            dates_array = [item['date'] for item in daily_registrations]
            counts_array = [item['count'] for item in daily_registrations]
            
            # 手動で移動平均を計算
            for i in range(window_size - 1, len(counts_array)):
                window_data = counts_array[i - window_size + 1:i + 1]
                avg = sum(window_data) / len(window_data)
                moving_avg_data.append({
                    'date': dates_array[i],
                    'moving_avg': float(avg)
                })
        
        # ユーザータイプ別統計
        user_types = {
            'admin': User.query.filter_by(role='admin').count(),
            'driver': User.query.filter_by(role='driver').count(),
            'student': User.query.filter_by(role='student').count()
        }
        
        # アクティブユーザー統計（過去7日間にログインしたユーザー）
        week_ago = datetime.now() - timedelta(days=7)
        active_users = User.query.filter(
            User.last_login >= week_ago
        ).count() if hasattr(User, 'last_login') else 0
        
        statistics_data = {
            'summary': {
                'total_users': total_users,
                'active_users': active_users,
                'user_types': user_types
            },
            'daily_registrations': daily_registrations,
            'moving_average': moving_avg_data,
            'chart_data': {
                'labels': [item['date'] for item in daily_registrations],
                'datasets': [
                    {
                        'label': '日別ユーザー登録数',
                        'data': [item['count'] for item in daily_registrations],
                        'borderColor': 'rgb(75, 192, 192)',
                        'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                        'tension': 0.1
                    }
                ]
            }
        }
        
        if moving_avg_data:
            statistics_data['chart_data']['datasets'].append({
                'label': '7日移動平均',
                'data': [None] * (window_size - 1) + [item['moving_avg'] for item in moving_avg_data],
                'borderColor': 'rgb(255, 99, 132)',
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'tension': 0.1
            })
        
        return jsonify(statistics_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/statistics/export')
@admin_required
def export_statistics():
    """統計データをCSVでエクスポート"""
    try:
        # 統計データを取得
        daily_registrations = []
        for i in range(29, -1, -1):
            date = datetime.now() - timedelta(days=i)
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            count = User.query.filter(
                User.created_at >= start_date,
                User.created_at <= end_date
            ).count()
            
            daily_registrations.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        
        # CSVデータを作成
        output = io.StringIO()
        writer = csv.writer(output)
        
        # ヘッダー
        writer.writerow(['日付', 'ユーザー登録数'])
        
        # データ
        for item in daily_registrations:
            writer.writerow([item['date'], item['count']])
        
        # レスポンスを作成
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=statistics_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/statistics/realtime-data')
@admin_required
def get_realtime_data():
    """リアルタイム統計データを取得"""
    try:
        # リアルタイムで変化するデータを生成（サンプル）
        current_time = datetime.now()
        
        # シミュレートされたリアルタイムデータ
        realtime_data = {
            'timestamp': current_time.isoformat(),
            'active_connections': random.randint(10, 50),
            'memory_usage': random.uniform(30, 80),
            'cpu_usage': random.uniform(10, 60),
            'request_per_minute': random.randint(50, 200)
        }
        
        return jsonify(realtime_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500