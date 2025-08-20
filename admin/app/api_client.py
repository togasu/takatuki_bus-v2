import requests
import os
from flask import current_app

class AdminAPIClient:
    """管理者サービス用の内部API通信クライアント"""
    
    def __init__(self):
        self.admin_token = os.getenv('ADMIN_SERVICE_TOKEN', 'admin-secret-token-2024')
        self.api_key = os.getenv('API_SECRET_KEY', 'bus-system-api-key-2024')
        self.headers = {
            'X-Service-Auth': self.admin_token,
            'X-API-Key': self.api_key,
            'User-Agent': 'admin-service-client/1.0',
            'Content-Type': 'application/json'
        }
    
    def get_students(self):
        """学生一覧を取得"""
        try:
            response = requests.get(
                'http://student:5000/api/students',
                headers=self.headers,
                timeout=30
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            current_app.logger.error(f"Failed to get students: {e}")
            return None
    
    def create_student(self, student_data):
        """学生を作成"""
        try:
            response = requests.post(
                'http://student:5000/api/students',
                json=student_data,
                headers=self.headers,
                timeout=30
            )
            return response.json() if response.status_code == 201 else None
        except Exception as e:
            current_app.logger.error(f"Failed to create student: {e}")
            return None
    
    def get_buses(self):
        """バス一覧を取得"""
        try:
            response = requests.get(
                'http://student:5000/api/buses',
                headers=self.headers,
                timeout=30
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            current_app.logger.error(f"Failed to get buses: {e}")
            return None
    
    def get_drivers(self):
        """ドライバー一覧を取得"""
        try:
            response = requests.get(
                'http://driver:5000/api/drivers',
                headers=self.headers,
                timeout=30
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            current_app.logger.error(f"Failed to get drivers: {e}")
            return None
    
    def create_driver(self, driver_data):
        """ドライバーを作成"""
        try:
            response = requests.post(
                'http://driver:5000/api/drivers',
                json=driver_data,
                headers=self.headers,
                timeout=30
            )
            return response.json() if response.status_code == 201 else None
        except Exception as e:
            current_app.logger.error(f"Failed to create driver: {e}")
            return None

# シングルトンインスタンス
admin_api = AdminAPIClient()
