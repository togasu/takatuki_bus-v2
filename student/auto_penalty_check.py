#!/usr/bin/env python3
"""
自動ペナルティチェックバッチ処理
未承認予約が3つ以上の学生に対して自動ペナルティを適用
"""

import sys
import os

# Flaskアプリケーションのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.database import db
from app.models.user import User
from app.models.reservation import Reservation
from app.utils.penalty_manager import PenaltyManager
from datetime import datetime, timedelta
import logging

# ログの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('penalty_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_auto_penalties():
    """全学生の自動ペナルティをチェック"""
    app = create_app()
    
    with app.app_context():
        try:
            # 全学生を取得
            users = User.query.all()
            logger.info(f"チェック対象学生数: {len(users)}人")
            
            penalty_applied_count = 0
            
            for user in users:
                logger.info(f"学生 {user.student_id} のペナルティチェック開始")
                
                # 自動ペナルティチェック
                penalty_applied = PenaltyManager.check_and_apply_auto_penalty(user.student_id)
                
                if penalty_applied:
                    penalty_applied_count += 1
                    logger.info(f"学生 {user.student_id} に自動ペナルティを適用しました")
                else:
                    logger.debug(f"学生 {user.student_id} はペナルティ適用不要")
            
            logger.info(f"自動ペナルティチェック完了: {penalty_applied_count}件のペナルティを適用")
            return penalty_applied_count
            
        except Exception as e:
            logger.error(f"自動ペナルティチェック中にエラーが発生: {str(e)}")
            return -1

def check_expired_reservations():
    """期限切れの未承認予約をチェック"""
    app = create_app()
    
    with app.app_context():
        try:
            # 1時間以上前の未承認予約を取得
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            expired_reservations = db.session.query(Reservation).filter(
                Reservation.approved == 0,
                Reservation.reserved_time < one_hour_ago
            ).all()
            
            logger.info(f"期限切れ未承認予約数: {len(expired_reservations)}件")
            
            # 学生IDごとにグループ化
            student_reservations = {}
            for reservation in expired_reservations:
                if reservation.user_id not in student_reservations:
                    student_reservations[reservation.user_id] = []
                student_reservations[reservation.user_id].append(reservation)
            
            penalty_applied_count = 0
            
            # 各学生の未承認予約をチェック
            for user_id, reservations in student_reservations.items():
                # user_idから学生を特定
                user = User.query.filter_by(id=user_id).first()
                if user:
                    logger.info(f"学生 {user.student_id} の期限切れ予約: {len(reservations)}件")
                    
                    # 自動ペナルティチェック
                    penalty_applied = PenaltyManager.check_and_apply_auto_penalty(user.student_id)
                    
                    if penalty_applied:
                        penalty_applied_count += 1
                        logger.info(f"学生 {user.student_id} に期限切れによる自動ペナルティを適用")
            
            logger.info(f"期限切れ予約チェック完了: {penalty_applied_count}件のペナルティを適用")
            return penalty_applied_count
            
        except Exception as e:
            logger.error(f"期限切れ予約チェック中にエラーが発生: {str(e)}")
            return -1

def main():
    """メイン処理"""
    logger.info("=== 自動ペナルティチェックバッチ開始 ===")
    
    # 全学生の自動ペナルティチェック
    penalty_count = check_auto_penalties()
    
    # 期限切れ予約のチェック
    expired_count = check_expired_reservations()
    
    logger.info(f"=== 自動ペナルティチェックバッチ完了 ===")
    logger.info(f"適用されたペナルティ数: {penalty_count + expired_count}件")

if __name__ == "__main__":
    main()