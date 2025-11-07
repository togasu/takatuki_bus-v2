from ..database import db
from ..models.semester import Semester, SemesterTransition
from ..models.user import User, LastSemester_user
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class SemesterManager:
    """学期管理クラス"""
    
    @staticmethod
    def get_active_semester():
        """アクティブな学期を取得"""
        return Semester.query.filter_by(is_active=True).first()
    
    @staticmethod
    def get_current_semester():
        """現在の日付に基づいて該当する学期を取得"""
        today = datetime.now().date()
        return Semester.query.filter(
            Semester.start_date <= today,
            Semester.end_date >= today
        ).first()
    
    @staticmethod
    def create_semester(name, start_date, end_date, is_active=False):
        """新しい学期を作成"""
        try:
            # 日付が文字列の場合は日付オブジェクトに変換
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # 既存の学期と重複チェック
            overlapping = Semester.query.filter(
                db.or_(
                    db.and_(Semester.start_date <= start_date, Semester.end_date >= start_date),
                    db.and_(Semester.start_date <= end_date, Semester.end_date >= end_date),
                    db.and_(Semester.start_date >= start_date, Semester.end_date <= end_date)
                )
            ).first()
            
            if overlapping:
                logger.warning(f"学期期間が重複しています: {overlapping.name}")
                return None, f"学期期間が既存の学期「{overlapping.name}」と重複しています"
            
            # アクティブな学期がある場合、既存をinactiveにする
            if is_active:
                Semester.query.filter_by(is_active=True).update({'is_active': False})
            
            semester = Semester(
                name=name,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active
            )
            
            db.session.add(semester)
            db.session.commit()
            
            logger.info(f"学期を作成しました: {name} ({start_date} - {end_date})")
            return semester, "学期を正常に作成しました"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"学期作成エラー: {str(e)}")
            return None, f"学期作成に失敗しました: {str(e)}"
    
    @staticmethod
    def activate_semester(semester_id):
        """指定した学期をアクティブにする"""
        try:
            # 既存のアクティブな学期を無効化
            Semester.query.filter_by(is_active=True).update({'is_active': False})
            
            # 指定した学期をアクティブにする
            semester = Semester.query.get(semester_id)
            if not semester:
                return False, "指定された学期が見つかりません"
            
            semester.is_active = True
            db.session.commit()
            
            logger.info(f"学期をアクティブにしました: {semester.name}")
            return True, f"学期「{semester.name}」をアクティブにしました"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"学期アクティベーションエラー: {str(e)}")
            return False, f"学期のアクティベーションに失敗しました: {str(e)}"
    
    @staticmethod
    def migrate_users_to_last_semester(from_semester_id=None, to_semester_id=None):
        """
        ユーザーを現在のUserテーブルからLastSemester_userテーブルに移行
        
        Args:
            from_semester_id: 移行元学期ID（省略時は現在のアクティブな学期）
            to_semester_id: 移行先学期ID（省略時は新しくアクティブになる学期）
        """
        try:
            # 現在のユーザー数を取得
            users_to_migrate = User.query.all()
            users_count = len(users_to_migrate)
            
            if users_count == 0:
                logger.info("移行するユーザーがありません")
                return True, "移行するユーザーがありません", 0
            
            migrated_count = 0
            
            for user in users_to_migrate:
                # LastSemester_userに既に存在するかチェック
                existing_last_user = LastSemester_user.query.filter_by(
                    student_id=user.student_id
                ).first()
                
                if not existing_last_user:
                    # LastSemester_userテーブルに追加
                    last_semester_user = LastSemester_user(
                        student_id=user.student_id,
                        idm_univ=user.idm_univ,
                        idm_bus=user.idm_bus,
                        regist_now_time=user.regist_now_time
                    )
                    db.session.add(last_semester_user)
                    migrated_count += 1
                else:
                    logger.info(f"ユーザー {user.student_id} は既にLastSemester_userに存在します")
            
            # Userテーブルからデータを削除
            User.query.delete()
            
            # 学期切り替え履歴を記録
            transition = SemesterTransition(
                from_semester_id=from_semester_id,
                to_semester_id=to_semester_id,
                users_migrated=migrated_count,
                status='completed',
                notes=f"自動学期切り替え: {migrated_count}名のユーザーを移行"
            )
            db.session.add(transition)
            
            db.session.commit()
            
            logger.info(f"ユーザー移行完了: {migrated_count}名を移行しました")
            return True, f"ユーザー移行完了: {migrated_count}名を移行しました", migrated_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"ユーザー移行エラー: {str(e)}")
            return False, f"ユーザー移行に失敗しました: {str(e)}", 0
    
    @staticmethod
    def switch_semester(new_semester_id, migrate_users=True):
        """
        学期を切り替える（ユーザー移行も含む）
        
        Args:
            new_semester_id: 新しい学期のID
            migrate_users: ユーザーを移行するかどうか
        """
        try:
            # 現在のアクティブな学期を取得
            current_semester = SemesterManager.get_active_semester()
            current_semester_id = current_semester.id if current_semester else None
            
            # 新しい学期をアクティブにする
            success, message = SemesterManager.activate_semester(new_semester_id)
            if not success:
                return False, message
            
            # ユーザー移行を実行
            if migrate_users:
                migrate_success, migrate_message, migrated_count = SemesterManager.migrate_users_to_last_semester(
                    from_semester_id=current_semester_id,
                    to_semester_id=new_semester_id
                )
                
                if not migrate_success:
                    return False, f"学期切り替えは成功しましたが、ユーザー移行に失敗しました: {migrate_message}"
                
                return True, f"学期切り替えが完了しました。{migrate_message}"
            else:
                return True, "学期切り替えが完了しました（ユーザー移行なし）"
                
        except Exception as e:
            logger.error(f"学期切り替えエラー: {str(e)}")
            return False, f"学期切り替えに失敗しました: {str(e)}"
    
    @staticmethod
    def auto_semester_check():
        """
        自動学期チェック - 現在の日付が新しい学期に入っている場合に自動切り替え
        """
        try:
            current_semester = SemesterManager.get_current_semester()
            active_semester = SemesterManager.get_active_semester()
            
            # 現在の日付に該当する学期がない場合
            if not current_semester:
                logger.warning("現在の日付に該当する学期がありません")
                return False, "現在の日付に該当する学期がありません"
            
            # 既にアクティブな学期が現在の学期と一致している場合
            if active_semester and active_semester.id == current_semester.id:
                logger.info(f"学期は既に正しく設定されています: {active_semester.name}")
                return True, f"学期は既に正しく設定されています: {active_semester.name}"
            
            # 学期の自動切り替えを実行
            logger.info(f"自動学期切り替えを実行: {current_semester.name}")
            return SemesterManager.switch_semester(current_semester.id, migrate_users=True)
            
        except Exception as e:
            logger.error(f"自動学期チェックエラー: {str(e)}")
            return False, f"自動学期チェックに失敗しました: {str(e)}"
    
    @staticmethod
    def get_all_semesters():
        """全ての学期を取得"""
        return Semester.query.order_by(Semester.start_date.desc()).all()
    
    @staticmethod
    def get_semester_by_id(semester_id):
        """IDで学期を取得"""
        return Semester.query.get(semester_id)
    
    @staticmethod
    def delete_semester(semester_id):
        """学期を削除（アクティブな学期は削除不可）"""
        try:
            semester = Semester.query.get(semester_id)
            if not semester:
                return False, "指定された学期が見つかりません"
            
            if semester.is_active:
                return False, "アクティブな学期は削除できません"
            
            # 関連する移行履歴も削除
            SemesterTransition.query.filter(
                db.or_(
                    SemesterTransition.from_semester_id == semester_id,
                    SemesterTransition.to_semester_id == semester_id
                )
            ).delete()
            
            db.session.delete(semester)
            db.session.commit()
            
            logger.info(f"学期を削除しました: {semester.name}")
            return True, f"学期「{semester.name}」を削除しました"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"学期削除エラー: {str(e)}")
            return False, f"学期削除に失敗しました: {str(e)}"