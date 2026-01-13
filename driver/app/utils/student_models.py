"""Student サービスのモデルへの参照を提供するモジュール"""

import sys
import os

# Student serviceのpathを追加
student_service_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'student')
if student_service_path not in sys.path:
    sys.path.insert(0, student_service_path)

try:
    from app.models.bus import Bus
    from app.models.seat import Seat 
    from app.models.reservation import Reservation
    
    # Student サービスのデータベースインスタンスも参照
    from app.database import db as student_db
    
except ImportError as e:
    print(f"Warning: Could not import from student service: {e}")
    # フォールバック用の空クラス定義
    class Bus:
        pass
    class Seat:
        pass  
    class Reservation:
        pass
    student_db = None

__all__ = ['Bus', 'Seat', 'Reservation', 'student_db']