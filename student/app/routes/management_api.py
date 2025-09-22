from flask import Blueprint, request, jsonify
from ..database import db
from ..models.user import User, User_Penalty
from ..models.reservation import Reservation
from ..models.cancel import Cancel
from ..models.bus import Bus
from ..models.seat import Seat
from datetime import datetime
import logging

# ログの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

management_api_bp = Blueprint('management_api', __name__, url_prefix='/api/management')

@management_api_bp.route('/all_students', methods=['GET'])
def get_all_students():
    """全学生一覧を取得するAPI"""
    try:
        # ページネーション用のパラメータ
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 全学生を取得（ページネーション付き）
        users = User.query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        students_data = []
        for user in users.items:
            # ペナルティ情報を取得
            penalty = User_Penalty.query.filter_by(student_id=int(user.student_id)).first()
            
            # 現在の予約数を取得
            current_reservations_count = db.session.query(Reservation).join(
                Bus, Reservation.bus_id == Bus.id
            ).filter(
                Reservation.user_id == user.id,
                Bus.departure_time >= datetime.now()
            ).count()
            
            # キャンセル履歴から未乗車回数を計算
            cancel_count = Cancel.query.filter_by(
                student_id=user.student_id,
                status='未乗車'
            ).count()
            
            students_data.append({
                'id': user.id,
                'student_id': user.student_id,
                'idm_univ': user.idm_univ,
                'idm_bus': user.idm_bus,
                'regist_time': user.regist_now_time.isoformat() if user.regist_now_time else None,
                'penalty': {
                    'has_penalty': penalty is not None,
                    'penalty_count': penalty.penalty_count if penalty else 0,
                    'penalty_time': penalty.penalty_time.isoformat() if penalty and penalty.penalty_time else None
                },
                'no_show_count': cancel_count,
                'current_reservations_count': current_reservations_count
            })
        
        return jsonify({
            'success': True,
            'students': students_data,
            'pagination': {
                'page': users.page,
                'pages': users.pages,
                'per_page': users.per_page,
                'total': users.total,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"全学生取得エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'学生一覧取得中にエラーが発生しました: {str(e)}'
        }), 500

@management_api_bp.route('/search_student', methods=['GET'])
def search_student():
    """学生を検索するAPI"""
    try:
        # クエリパラメータから検索条件を取得
        student_id = request.args.get('student_id', '').strip()
        username = request.args.get('username', '').strip()
        
        if not student_id and not username:
            return jsonify({
                'success': False,
                'message': '学籍番号またはユーザー名を指定してください'
            }), 400
        
        # 学生を検索
        query = User.query
        if student_id:
            query = query.filter(User.student_id == student_id)
        elif username:
            # usernameはstudent_idと同じものとして扱う
            query = query.filter(User.student_id == username)
        
        user = query.first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': '学生が見つかりませんでした'
            }), 404
        
        # ペナルティ情報を取得
        penalty = User_Penalty.query.filter_by(student_id=int(user.student_id)).first()
        
        # 現在の予約情報を取得
        current_reservations = db.session.query(
            Reservation, Bus, Seat
        ).join(
            Bus, Reservation.bus_id == Bus.id
        ).join(
            Seat, Reservation.seat_number == Seat.number
        ).filter(
            Reservation.user_id == user.id,
            Bus.departure_time >= datetime.now()
        ).all()
        
        # キャンセル履歴から未乗車回数を計算
        cancel_count = Cancel.query.filter_by(
            student_id=user.student_id,
            status='未乗車'
        ).count()
        
        # レスポンスデータを構築
        student_data = {
            'id': user.id,
            'student_id': user.student_id,
            'idm_univ': user.idm_univ,
            'idm_bus': user.idm_bus,
            'regist_time': user.regist_now_time.isoformat() if user.regist_now_time else None,
            'penalty': {
                'has_penalty': penalty is not None,
                'penalty_count': penalty.penalty_count if penalty else 0,
                'penalty_time': penalty.penalty_time.isoformat() if penalty and penalty.penalty_time else None
            },
            'no_show_count': cancel_count,
            'current_reservations': []
        }
        
        # 予約情報を追加
        for reservation, bus, seat in current_reservations:
            student_data['current_reservations'].append({
                'reservation_id': reservation.id,
                'bus_departure_time': bus.departure_time.isoformat() if bus.departure_time else None,
                'bus_id': bus.busid,
                'ud': '上り' if bus.ud == 0 else '下り',
                'seat_number': seat.number,
                'approved': bool(reservation.approved),
                'reserved_time': reservation.reserved_time.isoformat() if reservation.reserved_time else None
            })
        
        return jsonify({
            'success': True,
            'student': student_data
        })
        
    except Exception as e:
        logger.error(f"学生検索エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'検索中にエラーが発生しました: {str(e)}'
        }), 500

@management_api_bp.route('/delete_student', methods=['DELETE'])
def delete_student():
    """学生アカウントを削除するAPI"""
    try:
        data = request.get_json()
        if not data or 'student_id' not in data:
            return jsonify({
                'success': False,
                'message': '学籍番号が指定されていません'
            }), 400
        
        student_id = data['student_id']
        
        # 学生を検索
        user = User.query.filter_by(student_id=student_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '学生が見つかりませんでした'
            }), 404
        
        # 関連データを削除
        try:
            # 予約を削除
            Reservation.query.filter_by(user_id=user.id).delete()
            
            # ペナルティを削除
            User_Penalty.query.filter_by(student_id=int(user.student_id)).delete()
            
            # キャンセル履歴を削除
            Cancel.query.filter_by(student_id=user.student_id).delete()
            
            # ユーザーを削除
            db.session.delete(user)
            
            db.session.commit()
            
            logger.info(f"学生アカウント削除完了: {student_id}")
            
            return jsonify({
                'success': True,
                'message': '学生アカウントが正常に削除されました'
            })
            
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        logger.error(f"学生削除エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'削除中にエラーが発生しました: {str(e)}'
        }), 500

@management_api_bp.route('/clear_penalty', methods=['POST'])
def clear_penalty():
    """ペナルティを解除するAPI"""
    try:
        data = request.get_json()
        if not data or 'student_id' not in data:
            return jsonify({
                'success': False,
                'message': '学籍番号が指定されていません'
            }), 400
        
        student_id = data['student_id']
        
        # 学生を検索
        user = User.query.filter_by(student_id=student_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '学生が見つかりませんでした'
            }), 404
        
        # ペナルティを検索
        penalty = User_Penalty.query.filter_by(student_id=int(user.student_id)).first()
        
        if not penalty:
            return jsonify({
                'success': False,
                'message': 'ペナルティが設定されていません'
            }), 404
        
        try:
            # ペナルティを削除
            db.session.delete(penalty)
            db.session.commit()
            
            logger.info(f"ペナルティ解除完了: {student_id}")
            
            return jsonify({
                'success': True,
                'message': 'ペナルティが正常に解除されました'
            })
            
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        logger.error(f"ペナルティ解除エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'ペナルティ解除中にエラーが発生しました: {str(e)}'
        }), 500

@management_api_bp.route('/apply_penalty', methods=['POST'])
def apply_penalty():
    """ペナルティを付与するAPI"""
    try:
        data = request.get_json()
        if not data or 'student_id' not in data:
            return jsonify({
                'success': False,
                'message': '学籍番号が指定されていません'
            }), 400
        
        student_id = data['student_id']
        reason = data.get('reason', '管理者による手動ペナルティ')
        
        # 学生を検索
        user = User.query.filter_by(student_id=student_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '学生が見つかりませんでした'
            }), 404
        
        # 既存のペナルティをチェック
        existing_penalty = User_Penalty.query.filter_by(student_id=int(user.student_id)).first()
        
        try:
            if existing_penalty:
                # 既存のペナルティがある場合はカウントを増加
                existing_penalty.penalty_count += 1
                existing_penalty.penalty_time = datetime.utcnow()
                penalty_count = existing_penalty.penalty_count
            else:
                # 新しいペナルティを作成
                new_penalty = User_Penalty(
                    student_id=int(user.student_id),
                    penalty_count=1,
                    penalty_time=datetime.utcnow()
                )
                db.session.add(new_penalty)
                penalty_count = 1
            
            db.session.commit()
            
            logger.info(f"ペナルティ付与完了: {student_id}, 理由: {reason}, カウント: {penalty_count}")
            
            return jsonify({
                'success': True,
                'message': f'ペナルティが正常に付与されました (合計: {penalty_count}回)',
                'penalty_count': penalty_count
            })
            
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        logger.error(f"ペナルティ付与エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'ペナルティ付与中にエラーが発生しました: {str(e)}'
        }), 500

@management_api_bp.route('/student_reservations/<student_id>', methods=['GET'])
def get_student_reservations(student_id):
    """学生の予約情報を取得するAPI"""
    try:
        # 学生を検索
        user = User.query.filter_by(student_id=student_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '学生が見つかりませんでした'
            }), 404
        
        # 予約情報を取得（過去と未来両方）
        reservations = db.session.query(
            Reservation, Bus, Seat
        ).join(
            Bus, Reservation.bus_id == Bus.id
        ).join(
            Seat, Reservation.seat_number == Seat.number
        ).filter(
            Reservation.user_id == user.id
        ).order_by(Bus.departure_time.desc()).all()
        
        reservation_list = []
        for reservation, bus, seat in reservations:
            reservation_list.append({
                'reservation_id': reservation.id,
                'bus_departure_time': bus.departure_time.isoformat() if bus.departure_time else None,
                'bus_id': bus.busid,
                'ud': '上り' if bus.ud == 0 else '下り',
                'seat_number': seat.number,
                'approved': bool(reservation.approved),
                'reserved_time': reservation.reserved_time.isoformat() if reservation.reserved_time else None,
                'is_past': bus.departure_time < datetime.now() if bus.departure_time else False
            })
        
        return jsonify({
            'success': True,
            'reservations': reservation_list
        })
        
    except Exception as e:
        logger.error(f"予約情報取得エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'予約情報取得中にエラーが発生しました: {str(e)}'
        }), 500