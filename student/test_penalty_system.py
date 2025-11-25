#!/usr/bin/env python3
"""
ペナルティシステムのテストスクリプト
新しいペナルティ機能の動作確認
"""

import sys
import os

# Flaskアプリケーションのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.database import db
from app.models.user import User, User_Penalty
from app.models.reservation import Reservation
from app.utils.penalty_manager import PenaltyManager
from datetime import datetime, timedelta, time
import logging

# ログの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_penalty_manager():
    """PenaltyManagerのテスト"""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("=== PenaltyManagerテスト開始 ===")
            
            # テスト学生の確認
            test_student_id = '230092'
            user = User.query.filter_by(student_id=test_student_id).first()
            
            if not user:
                logger.error(f"テスト学生 {test_student_id} が見つかりません")
                return False
            
            logger.info(f"テスト学生: {test_student_id}")
            
            # 1. 現在のペナルティ状況を確認
            logger.info("--- 1. ペナルティ状況確認 ---")
            penalty_status = PenaltyManager.get_student_penalty_status(test_student_id)
            logger.info(f"ペナルティ状況: {penalty_status}")
            
            # 2. 未承認予約数を確認
            logger.info("--- 2. 未承認予約数確認 ---")
            unapproved_count = PenaltyManager.get_unapproved_reservations_count(test_student_id)
            logger.info(f"未承認予約数: {unapproved_count}")
            
            # 3. 手動ペナルティテスト
            logger.info("--- 3. 手動ペナルティテスト ---")
            if not penalty_status['has_penalty']:
                # ペナルティがない場合、手動ペナルティを適用
                end_time = datetime.utcnow() + timedelta(minutes=5)  # 5分後に終了
                result = PenaltyManager.apply_manual_penalty(
                    test_student_id, 
                    "テスト用手動ペナルティ", 
                    end_time
                )
                logger.info(f"手動ペナルティ適用結果: {result}")
                
                # 適用後の状況確認
                penalty_status = PenaltyManager.get_student_penalty_status(test_student_id)
                logger.info(f"適用後ペナルティ状況: {penalty_status}")
            else:
                logger.info("既にペナルティが適用されています")
            
            # 4. ペナルティ解除テスト
            logger.info("--- 4. ペナルティ解除テスト ---")
            if penalty_status['has_penalty']:
                result = PenaltyManager.clear_penalty(test_student_id)
                logger.info(f"ペナルティ解除結果: {result}")
                
                # 解除後の状況確認
                penalty_status = PenaltyManager.get_student_penalty_status(test_student_id)
                logger.info(f"解除後ペナルティ状況: {penalty_status}")
            
            logger.info("=== PenaltyManagerテスト完了 ===")
            return True
            
        except Exception as e:
            logger.error(f"テスト中にエラーが発生: {str(e)}")
            return False

def test_auto_penalty():
    """自動ペナルティのテスト"""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("=== 自動ペナルティテスト開始 ===")
            
            test_student_id = '230092'
            
            # テスト用未承認予約を作成
            logger.info("--- テスト用未承認予約作成 ---")
            
            # 既存の未承認予約をチェック
            existing_count = PenaltyManager.get_unapproved_reservations_count(test_student_id)
            logger.info(f"既存の未承認予約数: {existing_count}")
            
            if existing_count < 3:
                # 3つ未満の場合、テスト用予約を追加
                needed_count = 3 - existing_count
                logger.info(f"{needed_count}個のテスト用予約を作成します")
                
                for i in range(needed_count):
                    test_reservation = Reservation(
                        seat_number=i + 1,
                        bus_id=1,
                        user_id=test_student_id,
                        approved=0,
                        reserved_time=datetime.utcnow() - timedelta(hours=2)  # 2時間前
                    )
                    db.session.add(test_reservation)
                
                db.session.commit()
                logger.info(f"{needed_count}個のテスト用予約を作成しました")
            
            # 自動ペナルティチェック
            logger.info("--- 自動ペナルティチェック ---")
            penalty_applied = PenaltyManager.check_and_apply_auto_penalty(test_student_id)
            logger.info(f"自動ペナルティ適用結果: {penalty_applied}")
            
            # 結果確認
            penalty_status = PenaltyManager.get_student_penalty_status(test_student_id)
            logger.info(f"最終ペナルティ状況: {penalty_status}")
            
            logger.info("=== 自動ペナルティテスト完了 ===")
            return True
            
        except Exception as e:
            logger.error(f"自動ペナルティテスト中にエラーが発生: {str(e)}")
            db.session.rollback()
            return False

def cleanup_test_data():
    """テストデータのクリーンアップ"""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("=== テストデータクリーンアップ開始 ===")
            
            test_student_id = '230092'
            
            # テスト用ペナルティを削除
            test_penalties = User_Penalty.query.filter_by(student_id=test_student_id).all()
            for penalty in test_penalties:
                if 'テスト' in penalty.reason:
                    db.session.delete(penalty)
                    logger.info(f"テスト用ペナルティを削除: {penalty.reason}")
            
            # テスト用予約を削除（座席番号1-3の予約）
            test_reservations = Reservation.query.filter(
                Reservation.user_id == test_student_id,
                Reservation.seat_number.in_([1, 2, 3]),
                Reservation.approved == 0
            ).all()
            
            for reservation in test_reservations:
                db.session.delete(reservation)
                logger.info(f"テスト用予約を削除: 座席{reservation.seat_number}")
            
            db.session.commit()
            logger.info("=== テストデータクリーンアップ完了 ===")
            return True
            
        except Exception as e:
            logger.error(f"クリーンアップ中にエラーが発生: {str(e)}")
            db.session.rollback()
            return False

def main():
    """メイン処理"""
    print("ペナルティシステムテスト")
    print("1. PenaltyManagerテスト")
    print("2. 自動ペナルティテスト")
    print("3. テストデータクリーンアップ")
    print("4. 終了")
    
    while True:
        choice = input("\n選択してください (1-4): ")
        
        if choice == '1':
            if test_penalty_manager():
                print("✅ PenaltyManagerテストが完了しました")
            else:
                print("❌ PenaltyManagerテストが失敗しました")
        elif choice == '2':
            if test_auto_penalty():
                print("✅ 自動ペナルティテストが完了しました")
            else:
                print("❌ 自動ペナルティテストが失敗しました")
        elif choice == '3':
            if cleanup_test_data():
                print("✅ テストデータをクリーンアップしました")
            else:
                print("❌ クリーンアップが失敗しました")
        elif choice == '4':
            print("終了します")
            break
        else:
            print("無効な選択です")

if __name__ == "__main__":
    main()