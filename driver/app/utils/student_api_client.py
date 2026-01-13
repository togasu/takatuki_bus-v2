"""Student Service API クライアント"""

import requests
import logging
import os
from typing import List, Dict, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger('sojo-bus-log')


class StudentServiceClient:
    """Student service とのAPI通信を行うクライアント"""
    
    def __init__(self, base_url: str = 'http://student:5000'):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        # 内部API認証用のヘッダーを設定
        self.admin_token = os.getenv('ADMIN_SERVICE_TOKEN', 'admin-secret-token-2024')
        self.api_key = os.getenv('API_SECRET_KEY', 'bus-system-api-key-2024')
        self.session.headers.update({
            'X-Service-Auth': self.admin_token,
            'X-API-Key': self.api_key,
            'User-Agent': 'driver-service-client/1.0',
            'Content-Type': 'application/json'
        })
    
    def get_all_upcoming_buses(self, limit: int = 5) -> List[Dict]:
        """全ての今後のバス便を取得（departure_timeが現在時刻より後）
        
        注意: データベースにはJSTの時刻がタイムゾーン情報なしで保存されているため、
        比較時もJSTを使用する必要があります。
        """
        try:
            # まず全バスを取得
            response = self.session.get(f"{self.base_url}/api/management/buses")
            response.raise_for_status()
            all_buses = response.json()
            
            # フィルタリング: 出発時刻が未来のもの
            # データベースにはJSTがnaiveで保存されているため、JSTで比較
            now_jst = datetime.now(ZoneInfo("Asia/Tokyo")).replace(tzinfo=None)
            upcoming_buses = [
                bus for bus in all_buses
                if bus.get('departure_time')
                and datetime.fromisoformat(bus['departure_time']) > now_jst
            ]
            
            # 出発時刻でソート
            upcoming_buses.sort(key=lambda x: x['departure_time'])
            
            logger.info(f"Current JST: {now_jst.strftime('%Y-%m-%d %H:%M:%S')}, Found {len(upcoming_buses)} upcoming buses")
            return upcoming_buses[:limit]
        except requests.RequestException as e:
            logger.error(f"Failed to get upcoming buses from student service: {e}")
            return []
    
    def get_upcoming_buses_by_number(self, bus_number: int, limit: int = 5) -> List[Dict]:
        """指定した号車番号の今後のバス便を取得（departure_timeが現在時刻より後）
        
        注: busidはバスの号車番号（1～4）です。
        ドライバーは全てのバスから運行便を選択できるため、このメソッドの使用は推奨されません。
        代わりに get_all_upcoming_buses() を使用してください。
        """
        # 後方互換性のため、全てのバスを返す
        logger.warning(f"get_upcoming_buses_by_number is deprecated. Use get_all_upcoming_buses instead.")
        return self.get_all_upcoming_buses(limit)
    
    def get_buses_by_number_and_time(self, bus_number: int, limit: int = 5) -> List[Dict]:
        """指定した号車番号の今後のバス便を取得"""
        try:
            # データベースがJSTで保存されているため、JSTを使用
            now_jst = datetime.now(ZoneInfo("Asia/Tokyo")).replace(tzinfo=None)
            params = {
                'bus_number': bus_number,
                'limit': limit,
                'from_time': now_jst.isoformat()
            }
            response = self.session.get(f"{self.base_url}/api/buses", params=params)
            response.raise_for_status()
            return response.json().get('buses', [])
        except requests.RequestException as e:
            logger.error(f"Failed to get buses from student service: {e}")
            return []
    
    def get_bus_by_id(self, bus_id: int) -> Optional[Dict]:
        """バスIDで特定のバス便を取得"""
        try:
            # 全バスを取得してIDでフィルタ
            response = self.session.get(f"{self.base_url}/api/management/buses")
            response.raise_for_status()
            all_buses = response.json()
            
            for bus in all_buses:
                if bus.get('id') == bus_id:
                    return bus
            
            return None
        except requests.RequestException as e:
            logger.error(f"Failed to get bus {bus_id} from student service: {e}")
            return None
    
    def get_seats_with_reservations(self, bus_id: int) -> List[Dict]:
        """指定したバスの座席と予約情報を取得"""
        try:
            response = self.session.get(f"{self.base_url}/api/buses/{bus_id}/seats")
            response.raise_for_status()
            return response.json().get('seats', [])
        except requests.RequestException as e:
            logger.error(f"Failed to get seats for bus {bus_id} from student service: {e}")
            return []
    
    def approve_reservations(self, bus_id: int, seat_ids: List[str]) -> Dict:
        """座席の予約を承認"""
        try:
            data = {
                'bus_id': bus_id,
                'seat_ids': seat_ids,
                'action': 'approve'
            }
            response = self.session.post(f"{self.base_url}/api/reservations/approve", json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to approve reservations for bus {bus_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_buses_by_date_and_direction(self, date: str, direction: str) -> List[Dict]:
        """日付と方向でバス便を取得"""
        try:
            params = {
                'date': date,
                'direction': direction
            }
            response = self.session.get(f"{self.base_url}/api/buses/search", params=params)
            response.raise_for_status()
            return response.json().get('buses', [])
        except requests.RequestException as e:
            logger.error(f"Failed to search buses: {e}")
            return []


# グローバルクライアントインスタンス
student_client = None

def get_student_client() -> StudentServiceClient:
    """Student Service クライアントのシングルトンインスタンスを取得"""
    global student_client
    if student_client is None:
        student_client = StudentServiceClient()
    return student_client

def init_student_client(base_url: str = 'http://student:5000'):
    """Student Service クライアントを初期化"""
    global student_client
    student_client = StudentServiceClient(base_url)
    return student_client