#!/usr/bin/env python3
"""
ペナルティ管理システム
自動ペナルティの適用と管理者による手動ペナルティの管理
"""

from datetime import datetime, timedelta, time
from sqlalchemy import and_, desc
from ..database import db
from ..models.user import User, User_Penalty, Penalty_Reservation
from ..models.reservation import Reservation
import logging

logger = logging.getLogger(__name__)

class PenaltyManager:
    """ペナルティ管理クラス"""
    
    @staticmethod
    def check_and_apply_auto_penalty(student_id):
        """
        学生の未乗車（approved=0）予約をチェックして、
        3つ以上の場合は自動ペナルティを適用
        """
        try:
            # 学籍番号からユーザーを取得
            user = User.query.filter_by(student_id=student_id).first()
            if not user:
                logger.error(f"User with student_id {student_id} not found")
                return False
            
            # 現在アクティブなペナルティがあるかチェック
            active_penalty = User_Penalty.query.filter(
                and_(
                    User_Penalty.student_id == student_id,
                    User_Penalty.is_active == True,
                    User_Penalty.end_time_of_usage_restriction > datetime.utcnow()
                )
            ).first()
            
            if active_penalty:
                logger.info(f"Student {student_id} already has active penalty")
                return False
            
            # 最後のペナルティ解除日時を取得（不乗車の場合のみ）
            last_penalty_end = None
            last_no_show_penalty = User_Penalty.query.filter(
                and_(
                    User_Penalty.student_id == student_id,
                    User_Penalty.penalty_type == 'auto',
                    User_Penalty.reason.like('%未乗車%')
                )
            ).order_by(desc(User_Penalty.end_time_of_usage_restriction)).first()
            
            if last_no_show_penalty:
                last_penalty_end = last_no_show_penalty.end_time_of_usage_restriction
            
            # 最後のペナルティ解除以降のapproved=0の予約を取得
            query = Reservation.query.filter(
                and_(
                    Reservation.user_id == student_id,  # user.idではなくstudent_idを使用
                    Reservation.approved == 0
                )
            )
            
            if last_penalty_end:
                query = query.filter(Reservation.reserved_time > last_penalty_end)
            
            unapproved_reservations = query.order_by(Reservation.reserved_time).all()
            
            logger.info(f"Student {student_id} has {len(unapproved_reservations)} unapproved reservations")
            
            # 3つ以上の未乗車がある場合、ペナルティを適用
            if len(unapproved_reservations) >= 3:
                return PenaltyManager.apply_auto_penalty(student_id, unapproved_reservations)
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking auto penalty for student {student_id}: {str(e)}")
            return False
    
    @staticmethod
    def apply_auto_penalty(student_id, unapproved_reservations):
        """自動ペナルティを適用"""
        try:
            # ペナルティ終了時間を設定（2週間後の22:00）
            penalty_start = datetime.utcnow()
            penalty_end_date = penalty_start + timedelta(days=14)
            penalty_end = datetime.combine(
                penalty_end_date.date(), 
                time(22, 0, 0)  # 22:00
            )
            
            # ペナルティレコードを作成
            penalty = User_Penalty(
                student_id=student_id,
                end_time_of_usage_restriction=penalty_end,
                reason="未乗車が3回以上",
                penalty_type='auto',
                applied_time=penalty_start,
                is_active=True
            )
            
            db.session.add(penalty)
            db.session.flush()  # IDを取得するため
            
            # 関連する予約情報を記録
            for reservation in unapproved_reservations:
                penalty_reservation = Penalty_Reservation(
                    penalty_id=penalty.id,
                    reservation_id=reservation.id,
                    student_id=student_id,
                    bus_id=reservation.bus_id,
                    seat_number=reservation.seat_number,
                    reserved_time=reservation.reserved_time
                )
                db.session.add(penalty_reservation)
            
            db.session.commit()
            
            logger.info(f"Auto penalty applied to student {student_id} until {penalty_end}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying auto penalty to student {student_id}: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def apply_manual_penalty(student_id, reason, end_time=None):
        """管理者による手動ペナルティを適用"""
        try:
            # 既存のアクティブなペナルティをチェック
            active_penalty = User_Penalty.query.filter(
                and_(
                    User_Penalty.student_id == student_id,
                    User_Penalty.is_active == True,
                    User_Penalty.end_time_of_usage_restriction > datetime.utcnow()
                )
            ).first()
            
            if active_penalty:
                return {
                    'success': False,
                    'message': '既にアクティブなペナルティが存在します'
                }
            
            # 終了時間が指定されていない場合、デフォルト（2週間後の22:00）を設定
            if not end_time:
                penalty_start = datetime.utcnow()
                penalty_end_date = penalty_start + timedelta(days=14)
                end_time = datetime.combine(
                    penalty_end_date.date(),
                    time(22, 0, 0)
                )
            
            # ペナルティレコードを作成
            penalty = User_Penalty(
                student_id=student_id,
                end_time_of_usage_restriction=end_time,
                reason=reason,
                penalty_type='manual',
                applied_time=datetime.utcnow(),
                is_active=True
            )
            
            db.session.add(penalty)
            db.session.commit()
            
            logger.info(f"Manual penalty applied to student {student_id}: {reason}")
            return {
                'success': True,
                'message': 'ペナルティを適用しました',
                'penalty_id': penalty.id
            }
            
        except Exception as e:
            logger.error(f"Error applying manual penalty to student {student_id}: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'message': f'ペナルティ適用中にエラーが発生しました: {str(e)}'
            }
    
    @staticmethod
    def clear_penalty(student_id, clear_time=None):
        """ペナルティを解除"""
        try:
            # アクティブなペナルティを取得
            active_penalty = User_Penalty.query.filter(
                and_(
                    User_Penalty.student_id == student_id,
                    User_Penalty.is_active == True
                )
            ).first()
            
            if not active_penalty:
                return {
                    'success': False,
                    'message': 'アクティブなペナルティが見つかりません'
                }
            
            # 解除時間を設定（指定されていない場合は即時）
            if clear_time:
                active_penalty.end_time_of_usage_restriction = clear_time
            else:
                active_penalty.end_time_of_usage_restriction = datetime.utcnow()
                active_penalty.is_active = False
            
            db.session.commit()
            
            logger.info(f"Penalty cleared for student {student_id}")
            return {
                'success': True,
                'message': 'ペナルティを解除しました'
            }
            
        except Exception as e:
            logger.error(f"Error clearing penalty for student {student_id}: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'message': f'ペナルティ解除中にエラーが発生しました: {str(e)}'
            }
    
    @staticmethod
    def get_student_penalty_status(student_id):
        """学生のペナルティ状況を取得"""
        try:
            # 現在アクティブなペナルティを取得
            active_penalty = User_Penalty.query.filter(
                and_(
                    User_Penalty.student_id == student_id,
                    User_Penalty.is_active == True,
                    User_Penalty.end_time_of_usage_restriction > datetime.utcnow()
                )
            ).first()
            
            if not active_penalty:
                return {
                    'has_penalty': False,
                    'penalty': None,
                    'related_reservations': []
                }
            
            # 関連する予約情報を取得
            related_reservations = []
            if active_penalty.penalty_type == 'auto':
                penalty_reservations = Penalty_Reservation.query.filter(
                    Penalty_Reservation.penalty_id == active_penalty.id
                ).all()
                
                for pr in penalty_reservations:
                    # バス情報を取得
                    from app.models.bus import Bus
                    bus = Bus.query.get(pr.bus_id)
                    
                    reservation_info = {
                        'reservation_id': pr.reservation_id,
                        'bus_id': pr.bus_id,
                        'busid': bus.busid if bus else f"バス{pr.bus_id}",
                        'departure_time': bus.departure_time.strftime('%Y-%m-%d %H:%M') if bus and bus.departure_time else '不明',
                        'seat_number': pr.seat_number,
                        'reserved_time': pr.reserved_time.strftime('%Y-%m-%d %H:%M') if pr.reserved_time else '不明'
                    }
                    related_reservations.append(reservation_info)
            
            return {
                'has_penalty': True,
                'penalty': {
                    'id': active_penalty.id,
                    'reason': active_penalty.reason,
                    'penalty_type': active_penalty.penalty_type,
                    'applied_time': active_penalty.applied_time,
                    'end_time': active_penalty.end_time_of_usage_restriction,
                    'is_active': active_penalty.is_active
                },
                'related_reservations': related_reservations
            }
            
        except Exception as e:
            logger.error(f"Error getting penalty status for student {student_id}: {str(e)}")
            return {
                'has_penalty': False,
                'penalty': None,
                'related_reservations': [],
                'error': str(e)
            }
    
    @staticmethod
    def get_unapproved_reservations_count(student_id, since_date=None):
        """未乗車予約の数を取得"""
        try:
            # 学籍番号からユーザーIDを取得
            user = User.query.filter_by(student_id=student_id).first()
            if not user:
                return 0
                
            query = Reservation.query.filter(
                and_(
                    Reservation.user_id == student_id,  # user.idではなくstudent_idを使用
                    Reservation.approved == 0
                )
            )
            
            if since_date:
                query = query.filter(Reservation.reserved_time > since_date)
            
            count = query.count()
            return count
            
        except Exception as e:
            logger.error(f"Error getting unapproved reservations count for student {student_id}: {str(e)}")
            return 0