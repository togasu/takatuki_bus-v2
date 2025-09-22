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
    
    def get_student_by_id(self, student_id):
        """特定の学生情報を取得"""
        try:
            response = requests.get(
                f'http://student:5000/api/students/{student_id}',
                headers=self.headers,
                timeout=30
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            current_app.logger.error(f"Failed to get student {student_id}: {e}")
            return None
    
    def update_student(self, student_id, student_data):
        """学生情報を更新"""
        try:
            response = requests.put(
                f'http://student:5000/api/students/{student_id}',
                json=student_data,
                headers=self.headers,
                timeout=30
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            current_app.logger.error(f"Failed to update student {student_id}: {e}")
            return None
    
    def delete_student(self, student_id):
        """学生を削除"""
        try:
            response = requests.delete(
                f'http://student:5000/api/students/{student_id}',
                headers=self.headers,
                timeout=30
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            current_app.logger.error(f"Failed to delete student {student_id}: {e}")
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
    
    def get_driver_by_id(self, driver_id):
        """特定のドライバー情報を取得"""
        try:
            response = requests.get(
                f'http://driver:5000/api/drivers/{driver_id}',
                headers=self.headers,
                timeout=30
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            current_app.logger.error(f"Failed to get driver {driver_id}: {e}")
            return None
    
    def update_driver(self, driver_id, driver_data):
        """ドライバー情報を更新"""
        try:
            response = requests.put(
                f'http://driver:5000/api/drivers/{driver_id}',
                json=driver_data,
                headers=self.headers,
                timeout=30
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            current_app.logger.error(f"Failed to update driver {driver_id}: {e}")
            return None
    
    def delete_driver(self, driver_id):
        """ドライバーを削除"""
        try:
            response = requests.delete(
                f'http://driver:5000/api/drivers/{driver_id}',
                headers=self.headers,
                timeout=30
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            current_app.logger.error(f"Failed to delete driver {driver_id}: {e}")
            return None

    # 学生管理API
    def get_all_students(self, page=1, per_page=20):
        """全学生一覧を取得"""
        try:
            params = {'page': page, 'per_page': per_page}
            response = requests.get(
                'http://student:5000/api/management/all_students',
                params=params,
                headers=self.headers,
                timeout=30
            )
            
            # JSONレスポンスのパースを試行
            try:
                return response.json()
            except ValueError as json_error:
                current_app.logger.error(f"JSON parse error for get all students: {json_error}")
                current_app.logger.error(f"Response status: {response.status_code}")
                current_app.logger.error(f"Response content: {response.text[:200]}")
                return {
                    'success': False, 
                    'message': f'学生サービスから無効なレスポンスが返されました（ステータス: {response.status_code}）'
                }
        except requests.exceptions.ConnectTimeout:
            current_app.logger.error("Connection timeout for get all students")
            return {'success': False, 'message': '学生サービスへの接続がタイムアウトしました'}
        except requests.exceptions.ConnectionError:
            current_app.logger.error("Connection error for get all students")
            return {'success': False, 'message': '学生サービスに接続できませんでした'}
        except Exception as e:
            current_app.logger.error(f"Failed to get all students: {e}")
            return {'success': False, 'message': f'通信エラー: {str(e)}'}
    
    def search_student(self, student_id=None, username=None):
        """学生を検索"""
        try:
            params = {}
            if student_id:
                params['student_id'] = student_id
            elif username:
                params['username'] = username
            
            response = requests.get(
                'http://student:5000/api/management/search_student',
                params=params,
                headers=self.headers,
                timeout=30
            )
            return response.json() if response.status_code == 200 else response.json()
        except Exception as e:
            current_app.logger.error(f"Failed to search student: {e}")
            return {'success': False, 'message': f'通信エラー: {str(e)}'}
    
    def delete_student_account(self, student_id):
        """学生アカウントを削除"""
        try:
            response = requests.delete(
                'http://student:5000/api/management/delete_student',
                json={'student_id': student_id},
                headers=self.headers,
                timeout=30
            )
            return response.json()
        except Exception as e:
            current_app.logger.error(f"Failed to delete student {student_id}: {e}")
            return {'success': False, 'message': f'通信エラー: {str(e)}'}
    
    def clear_student_penalty(self, student_id):
        """学生のペナルティを解除"""
        try:
            response = requests.post(
                'http://student:5000/api/management/clear_penalty',
                json={'student_id': student_id},
                headers=self.headers,
                timeout=30
            )
            
            # レスポンスの状態コードをチェック
            if response.status_code == 404:
                return {'success': False, 'message': 'ペナルティ解除APIが見つかりません'}
            elif response.status_code == 400:
                return {'success': False, 'message': 'リクエストデータが不正です'}
            elif response.status_code == 500:
                return {'success': False, 'message': '学生サービス側でエラーが発生しました'}
            
            # JSONレスポンスのパースを試行
            try:
                return response.json()
            except ValueError as json_error:
                current_app.logger.error(f"JSON parse error for clear penalty {student_id}: {json_error}")
                current_app.logger.error(f"Response status: {response.status_code}")
                current_app.logger.error(f"Response content: {response.text[:200]}")
                return {
                    'success': False, 
                    'message': f'学生サービスから無効なレスポンスが返されました（ステータス: {response.status_code}）'
                }
                
        except requests.exceptions.ConnectTimeout:
            current_app.logger.error(f"Connection timeout for clear penalty: {student_id}")
            return {'success': False, 'message': '学生サービスへの接続がタイムアウトしました'}
        except requests.exceptions.ConnectionError:
            current_app.logger.error(f"Connection error for clear penalty: {student_id}")
            return {'success': False, 'message': '学生サービスに接続できませんでした'}
        except Exception as e:
            current_app.logger.error(f"Failed to clear penalty for student {student_id}: {e}")
            return {'success': False, 'message': f'通信エラー: {str(e)}'}
    
    def apply_student_penalty(self, student_id, reason=None):
        """学生にペナルティを付与"""
        try:
            payload = {'student_id': student_id}
            if reason:
                payload['reason'] = reason
            
            response = requests.post(
                'http://student:5000/api/management/apply_penalty',
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            # レスポンスの状態コードをチェック
            if response.status_code == 404:
                return {'success': False, 'message': 'ペナルティ付与APIが見つかりません（学生サービスの設定を確認してください）'}
            elif response.status_code == 400:
                return {'success': False, 'message': 'リクエストデータが不正です'}
            elif response.status_code == 500:
                return {'success': False, 'message': '学生サービス側でエラーが発生しました'}
            
            # JSONレスポンスのパースを試行
            try:
                return response.json()
            except ValueError as json_error:
                current_app.logger.error(f"JSON parse error for student {student_id}: {json_error}")
                current_app.logger.error(f"Response status: {response.status_code}")
                current_app.logger.error(f"Response content: {response.text[:200]}")
                return {
                    'success': False, 
                    'message': f'学生サービスから無効なレスポンスが返されました（ステータス: {response.status_code}）'
                }
                
        except requests.exceptions.ConnectTimeout:
            current_app.logger.error(f"Connection timeout for apply penalty: {student_id}")
            return {'success': False, 'message': '学生サービスへの接続がタイムアウトしました'}
        except requests.exceptions.ConnectionError:
            current_app.logger.error(f"Connection error for apply penalty: {student_id}")
            return {'success': False, 'message': '学生サービスに接続できませんでした'}
        except Exception as e:
            current_app.logger.error(f"Failed to apply penalty for student {student_id}: {e}")
            return {'success': False, 'message': f'通信エラー: {str(e)}'}

    def get_student_reservations(self, student_id):
        """学生の予約情報を取得"""
        try:
            response = requests.get(
                f'http://student:5000/api/management/student_reservations/{student_id}',
                headers=self.headers,
                timeout=30
            )
            return response.json() if response.status_code == 200 else response.json()
        except Exception as e:
            current_app.logger.error(f"Failed to get reservations for student {student_id}: {e}")
            return {'success': False, 'message': f'通信エラー: {str(e)}'}

# シングルトンインスタンス
admin_api = AdminAPIClient()
