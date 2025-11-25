"""Student Service API クライアント"""

import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger('sojo-bus-log')


class StudentServiceClient:
    """Student service とのAPI通信を行うクライアント"""
    
    def __init__(self, base_url: str = 'http://student:5000'):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def get_upcoming_buses_by_number(self, bus_number: int, limit: int = 5) -> List[Dict]:
        """指定した号車番号の今後のバス便を取得（departure_timeが現在時刻より後）"""
        try:
            # まず全バスを取得
            response = self.session.get(f"{self.base_url}/api/management/buses")
            response.raise_for_status()
            all_buses = response.json()
            
            # フィルタリング: 該当の号車で、出発時刻が未来のもの
            now = datetime.now()
            upcoming_buses = [
                bus for bus in all_buses
                if bus.get('busid') == bus_number 
                and bus.get('departure_time')
                and datetime.fromisoformat(bus['departure_time']) > now
            ]
            
            # 出発時刻でソート
            upcoming_buses.sort(key=lambda x: x['departure_time'])
            
            return upcoming_buses[:limit]
        except requests.RequestException as e:
            logger.error(f"Failed to get upcoming buses from student service: {e}")
            return []
    
    def get_buses_by_number_and_time(self, bus_number: int, limit: int = 5) -> List[Dict]:
        """指定した号車番号の今後のバス便を取得"""
        try:
            params = {
                'bus_number': bus_number,
                'limit': limit,
                'from_time': datetime.now().isoformat()
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