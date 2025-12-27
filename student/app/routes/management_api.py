from flask import Blueprint, request, jsonify
from ..database import db
from ..models.user import User, User_Penalty, Penalty_Reservation
from ..models.reservation import Reservation
from ..models.cancel import Cancel
from ..models.bus import Bus
from ..models.seat import Seat
from ..utils.penalty_manager import PenaltyManager
from ..decorators import require_service_auth
from datetime import datetime, timedelta, time
import logging

# ログの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

management_api_bp = Blueprint('management_api', __name__, url_prefix='/api/management')

@management_api_bp.route('/all_students', methods=['GET'])
@require_service_auth
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
            # ペナルティ情報を取得（新スキーマ）
            penalty_status = PenaltyManager.get_student_penalty_status(user.student_id)
            
            # 現在の予約数を取得
            current_reservations_count = db.session.query(Reservation).join(
                Bus, Reservation.bus_id == Bus.id
            ).filter(
                Reservation.user_id == user.student_id,  # user.idではなくuser.student_idを使用
                Bus.departure_time >= datetime.now()
            ).count()
            
            # 未承認予約の数を取得（不乗車カウント）
            unapproved_count = PenaltyManager.get_unapproved_reservations_count(user.student_id)
            
            students_data.append({
                'id': user.id,
                'student_id': user.student_id,
                'idm_univ': user.idm_univ,
                'idm_bus': user.idm_bus,
                'regist_time': user.regist_now_time.isoformat() if user.regist_now_time else None,
                'penalty': {
                    'has_penalty': penalty_status['has_penalty'],
                    'reason': penalty_status['penalty']['reason'] if penalty_status['has_penalty'] else None,
                    'end_time': penalty_status['penalty']['end_time'].isoformat() if penalty_status['has_penalty'] and penalty_status['penalty']['end_time'] else None,
                    'penalty_type': penalty_status['penalty']['penalty_type'] if penalty_status['has_penalty'] else None
                },
                'unapproved_reservations_count': unapproved_count,
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
@require_service_auth
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
        
        # ペナルティ情報を取得（新スキーマ）
        penalty_status = PenaltyManager.get_student_penalty_status(user.student_id)
        
        # 現在の予約情報を取得
        current_reservations = db.session.query(
            Reservation, Bus, Seat
        ).join(
            Bus, Reservation.bus_id == Bus.id
        ).join(
            Seat, Reservation.seat_number == Seat.number
        ).filter(
            Reservation.user_id == user.student_id,  # user.idではなくuser.student_idを使用
            Bus.departure_time >= datetime.now()
        ).all()
        
        # 未承認予約の数を取得
        unapproved_count = PenaltyManager.get_unapproved_reservations_count(user.student_id)
        
        # レスポンスデータを構築
        student_data = {
            'id': user.id,
            'student_id': user.student_id,
            'idm_univ': user.idm_univ,
            'idm_bus': user.idm_bus,
            'regist_time': user.regist_now_time.isoformat() if user.regist_now_time else None,
            'penalty': {
                'has_penalty': penalty_status['has_penalty'],
                'reason': penalty_status['penalty']['reason'] if penalty_status['has_penalty'] else None,
                'end_time': penalty_status['penalty']['end_time'].isoformat() if penalty_status['has_penalty'] and penalty_status['penalty']['end_time'] else None,
                'penalty_type': penalty_status['penalty']['penalty_type'] if penalty_status['has_penalty'] else None,
                'related_reservations': penalty_status['related_reservations']
            },
            'unapproved_reservations_count': unapproved_count,
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
@require_service_auth
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
@require_service_auth
def clear_penalty():
    """ペナルティを解除するAPI（新システム）"""
    try:
        data = request.get_json()
        if not data or 'student_id' not in data:
            return jsonify({
                'success': False,
                'message': '学籍番号が指定されていません'
            }), 400
        
        student_id = data['student_id']
        clear_time_str = data.get('clear_time')
        
        # 学生の存在確認
        user = User.query.filter_by(student_id=student_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '学生が見つかりませんでした'
            }), 404
        
        # 解除時間のパース
        clear_time = None
        if clear_time_str:
            try:
                clear_time = datetime.fromisoformat(clear_time_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': '解除時間の形式が不正です'
                }), 400
        
        # PenaltyManagerを使用してペナルティを解除
        result = PenaltyManager.clear_penalty(student_id, clear_time)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"ペナルティ解除エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'ペナルティ解除中にエラーが発生しました: {str(e)}'
        }), 500

@management_api_bp.route('/apply_penalty', methods=['POST'])
@require_service_auth
def apply_penalty():
    """ペナルティを付与するAPI（新システム）"""
    try:
        data = request.get_json()
        if not data or 'student_id' not in data:
            return jsonify({
                'success': False,
                'message': '学籍番号が指定されていません'
            }), 400
        
        student_id = data['student_id']
        reason = data.get('reason', '管理者による手動ペナルティ')
        end_time_str = data.get('end_time')
        
        # 学生の存在確認
        user = User.query.filter_by(student_id=student_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '学生が見つかりませんでした'
            }), 404
        
        # 終了時間のパース
        end_time = None
        if end_time_str:
            try:
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': '終了時間の形式が不正です'
                }), 400
        
        # PenaltyManagerを使用してペナルティを適用
        result = PenaltyManager.apply_manual_penalty(student_id, reason, end_time)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"ペナルティ付与エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'ペナルティ付与中にエラーが発生しました: {str(e)}'
        }), 500

@management_api_bp.route('/student_reservations/<student_id>', methods=['GET'])
@require_service_auth
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
            Reservation.user_id == user.student_id  # user.idではなくuser.student_idを使用
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

@management_api_bp.route('/penalty_details/<student_id>', methods=['GET'])
@require_service_auth
def get_penalty_details(student_id):
    """学生のペナルティ詳細情報を取得するAPI"""
    try:
        # 学生の存在確認
        user = User.query.filter_by(student_id=student_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '学生が見つかりませんでした'
            }), 404
        
        # PenaltyManagerを使用してペナルティ詳細を取得
        penalty_status = PenaltyManager.get_student_penalty_status(student_id)
        
        return jsonify({
            'success': True,
            'penalty_status': penalty_status
        })
        
    except Exception as e:
        logger.error(f"ペナルティ詳細取得エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'ペナルティ詳細取得中にエラーが発生しました: {str(e)}'
        }), 500

@management_api_bp.route('/check_auto_penalty/<student_id>', methods=['POST'])
@require_service_auth
def check_auto_penalty(student_id):
    """学生の自動ペナルティをチェックし、必要に応じて適用するAPI"""
    try:
        # 学生の存在確認
        user = User.query.filter_by(student_id=student_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '学生が見つかりませんでした'
            }), 404
        
        # 自動ペナルティチェック
        penalty_applied = PenaltyManager.check_and_apply_auto_penalty(student_id)
        
        if penalty_applied:
            return jsonify({
                'success': True,
                'message': '自動ペナルティが適用されました',
                'penalty_applied': True
            })
        else:
            return jsonify({
                'success': True,
                'message': 'ペナルティの適用は不要です',
                'penalty_applied': False
            })
        
    except Exception as e:
        logger.error(f"自動ペナルティチェックエラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'自動ペナルティチェック中にエラーが発生しました: {str(e)}'
        }), 500

# バス管理API
@management_api_bp.route('/buses', methods=['GET'])
@require_service_auth
def get_all_buses():
    """全バス一覧を取得"""
    try:
        buses = Bus.query.order_by(Bus.departure_time.desc()).all()
        buses_data = []
        
        for bus in buses:
            buses_data.append({
                'id': bus.id,
                'busid': bus.busid,
                'departure_time': bus.departure_time.isoformat() if bus.departure_time else None,
                'seats': bus.seats,
                'ud': bus.ud,  # 0=上り, 1=下り
                'bookable_time': bus.bookable_time,
                'status': bus.status  # 0=通常, 1=キャンセル待ち, 2=出発後
            })
        
        return jsonify(buses_data)
        
    except Exception as e:
        logger.error(f"バス一覧取得エラー: {str(e)}")
        return jsonify({'error': f'バス一覧取得中にエラーが発生しました: {str(e)}'}), 500

@management_api_bp.route('/buses/with_reservations', methods=['GET'])
@require_service_auth
def get_buses_with_reservations():
    """予約があるバス一覧を取得"""
    try:
        # 予約があるバスのみを取得
        buses_with_reservations = db.session.query(
            Bus,
            db.func.count(Reservation.id).label('reservation_count')
        ).outerjoin(
            Reservation, Bus.id == Reservation.bus_id
        ).group_by(Bus.id).having(
            db.func.count(Reservation.id) > 0
        ).order_by(Bus.departure_time.desc()).limit(100).all()
        
        buses_data = []
        for bus, reservation_count in buses_with_reservations:
            # バス情報を構築
            buses_data.append({
                'id': bus.id,
                'busid': bus.busid,
                'departure_time': bus.departure_time.isoformat() if bus.departure_time else None,
                'arrival_time': None,  # arrival_timeフィールドがある場合は追加
                'route_name': f"{'上り' if bus.ud == 0 else '下り'}",
                'departure_location': '大学' if bus.ud == 0 else '駅',
                'arrival_location': '駅' if bus.ud == 0 else '大学',
                'seats': bus.seats,
                'status': bus.status,
                'reservation_count': reservation_count
            })
        
        return jsonify({
            'success': True,
            'buses': buses_data
        })
        
    except Exception as e:
        logger.error(f"予約バス一覧取得エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'予約バス一覧取得中にエラーが発生しました: {str(e)}'
        }), 500

@management_api_bp.route('/buses/<int:bus_id>/seats', methods=['GET'])
@require_service_auth
def get_bus_seat_status(bus_id):
    """特定バスの座席予約状況を取得"""
    try:
        # バス情報を取得
        bus = Bus.query.filter_by(id=bus_id).first()
        if not bus:
            return jsonify({
                'success': False,
                'message': 'バスが見つかりませんでした'
            }), 404
        
        # 予約情報を取得
        logger.info(f"Querying reservations for bus_id={bus_id}")
        logger.info(f"Reservation table name: {Reservation.__tablename__}")
        logger.info(f"User table name: {User.__tablename__ if hasattr(User, '__tablename__') else 'users'}")
        
        # まずReservationテーブルから直接データを確認
        all_reservations = db.session.query(Reservation).filter(
            Reservation.bus_id == bus_id
        ).all()
        logger.info(f"Direct query: Found {len(all_reservations)} reservations in Reservation table")
        for r in all_reservations:
            logger.info(f"  Reservation: id={r.id}, seat={r.seat_number}, user_id='{r.user_id}', bus_id={r.bus_id}")
        
        # Userテーブルのstudent_idも確認
        if all_reservations:
            sample_user_id = all_reservations[0].user_id
            matching_user = db.session.query(User).filter(User.student_id == sample_user_id).first()
            logger.info(f"Looking for user with student_id='{sample_user_id}': {'Found' if matching_user else 'NOT FOUND'}")
            if matching_user:
                logger.info(f"  User found: student_id='{matching_user.student_id}'")
            else:
                # ユーザーが見つからない場合、すべてのユーザーのstudent_idを確認
                all_users = db.session.query(User.student_id).limit(10).all()
                logger.info(f"  Sample user student_ids in database: {[u.student_id for u in all_users]}")
        
        # LEFT JOINを使用してユーザーが見つからない場合でも予約を表示
        reservations = db.session.query(
            Reservation, User
        ).outerjoin(
            User, Reservation.user_id == User.student_id
        ).filter(
            Reservation.bus_id == bus_id
        ).order_by(Reservation.seat_number).all()
        
        logger.info(f"Found {len(reservations)} reservations for bus {bus_id}")
        for r, u in reservations:
            if u:
                logger.info(f"  Seat {r.seat_number}: user={u.student_id}, approved={r.approved}")
            else:
                logger.info(f"  Seat {r.seat_number}: user_id={r.user_id} (User not found), approved={r.approved}")
        
        # 座席ごとの予約状態を作成（27席分）
        seat_status = []
        reservation_map = {r.seat_number: (r, u) for r, u in reservations}
        
        for i in range(1, 28):  # 1〜27番の座席
            if i in reservation_map:
                reservation, user = reservation_map[i]
                # ユーザーが見つからない場合はreservation.user_idを使用
                if user:
                    seat_status.append({
                        'seat_number': i,
                        'reserved': True,
                        'student_id': user.student_id,
                        'user_id': user.student_id,
                        'display_name': user.name if hasattr(user, 'name') and user.name else user.student_id,
                        'approved': reservation.approved,
                        'reserved_time': reservation.reserved_time.isoformat() if reservation.reserved_time else None
                    })
                else:
                    # Userレコードが見つからない場合
                    seat_status.append({
                        'seat_number': i,
                        'reserved': True,
                        'student_id': reservation.user_id,
                        'user_id': reservation.user_id,
                        'display_name': f'{reservation.user_id} (未登録)',
                        'approved': reservation.approved,
                        'reserved_time': reservation.reserved_time.isoformat() if reservation.reserved_time else None
                    })
            else:
                seat_status.append({
                    'seat_number': i,
                    'reserved': False,
                    'student_id': None,
                    'user_id': None,
                    'display_name': None,
                    'approved': None,
                    'reserved_time': None
                })
        
        return jsonify({
            'success': True,
            'bus': {
                'id': bus.id,
                'busid': bus.busid,
                'departure_time': bus.departure_time.isoformat() if bus.departure_time else None,
                'arrival_time': None,
                'route_name': f"{'上り' if bus.ud == 0 else '下り'}",
                'departure_location': '大学' if bus.ud == 0 else '駅',
                'arrival_location': '駅' if bus.ud == 0 else '大学',
                'seats': bus.seats,
                'status': bus.status
            },
            'seat_status': seat_status
        })
        
    except Exception as e:
        logger.error(f"バス座席状況取得エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'バス座席状況取得中にエラーが発生しました: {str(e)}'
        }), 500

@management_api_bp.route('/buses', methods=['POST'])
@require_service_auth
def create_bus():
    """新しいバスを作成"""
    try:
        data = request.get_json()
        
        # 必須フィールドの確認
        required_fields = ['departure_time', 'seats', 'direction']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} は必須項目です'}), 400
        
        # departure_timeを適切なdatetimeオブジェクトに変換
        departure_time_str = data['departure_time']
        if isinstance(departure_time_str, str):
            # ISO形式の文字列をdatetimeに変換
            departure_time = datetime.fromisoformat(departure_time_str.replace('Z', '+00:00'))
        else:
            departure_time = departure_time_str
        
        # busidは号車番号（1～4）として扱う
        # リクエストで指定されていない場合は1をデフォルトとする
        new_busid = int(data.get('busid', 1))
        if new_busid < 1 or new_busid > 4:
            return jsonify({'error': 'busidは1～4の範囲で指定してください'}), 400
        
        # 新しいバスを作成
        new_bus = Bus()
        new_bus.busid = new_busid
        new_bus.departure_time = departure_time
        new_bus.seats = int(data['seats'])
        new_bus.ud = int(data['direction'])  # 0=上り, 1=下り
        new_bus.bookable_time = data.get('bookable_time', 0)
        new_bus.status = data.get('status', 0)  # デフォルトは通常
        
        db.session.add(new_bus)
        db.session.commit()
        
        logger.info(f"新しいバスが作成されました: busid={new_busid}, departure_time={departure_time}")
        
        return jsonify({
            'id': new_bus.id,
            'busid': new_bus.busid,
            'departure_time': new_bus.departure_time.isoformat() if new_bus.departure_time else None,
            'seats': new_bus.seats,
            'ud': new_bus.ud,
            'bookable_time': new_bus.bookable_time,
            'status': new_bus.status,
            'message': 'バスが正常に作成されました'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"バス作成エラー: {str(e)}")
        return jsonify({'error': f'バス作成中にエラーが発生しました: {str(e)}'}), 500

@management_api_bp.route('/reservations', methods=['POST'])
@require_service_auth
def create_reservations():
    """管理者用：複数座席の予約を作成するAPI"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'リクエストデータが不正です'}), 400
        
        bus_id = data.get('bus_id')
        seat_numbers = data.get('seat_numbers', [])
        user_id = data.get('user_id')
        
        if not bus_id or not seat_numbers or not user_id:
            return jsonify({'success': False, 'message': '必須パラメータが不足しています'}), 400
        
        # バスの存在確認
        bus = db.session.query(Bus).filter_by(id=bus_id).first()
        if not bus:
            return jsonify({'success': False, 'message': '指定されたバスが見つかりません'}), 404
        
        # 座席番号のバリデーション
        if not isinstance(seat_numbers, list) or not all(isinstance(s, int) for s in seat_numbers):
            return jsonify({'success': False, 'message': '座席番号は整数のリストで指定してください'}), 400
        
        # 重複チェック
        if len(seat_numbers) != len(set(seat_numbers)):
            return jsonify({'success': False, 'message': '同じ座席番号が重複しています'}), 400
        
        # 既存予約のチェック
        existing_reservations = db.session.query(Reservation).filter(
            Reservation.bus_id == bus_id,
            Reservation.seat_number.in_(seat_numbers)
        ).all()
        
        if existing_reservations:
            reserved_seats = [r.seat_number for r in existing_reservations]
            return jsonify({
                'success': False,
                'message': f'既に予約済みの座席があります: {", ".join(map(str, reserved_seats))}'
            }), 400
        
        # 予約を作成
        created_reservations = []
        for seat_number in seat_numbers:
            reservation = Reservation(
                seat_number=seat_number,
                user_id=user_id,
                bus_id=bus_id,
                approved=0,
                reserved_time=datetime.now()
            )
            db.session.add(reservation)
            created_reservations.append({
                'seat_number': seat_number,
                'user_id': user_id,
                'bus_id': bus_id
            })
        
        db.session.commit()
        
        logger.info(f"管理者による予約作成: user_id={user_id}, bus_id={bus_id}, seats={seat_numbers}")
        
        # WebSocketでリアルタイム更新をブロードキャスト
        try:
            from flask import current_app
            if hasattr(current_app, 'socketio'):
                from .ws import broadcast_bus_update
                broadcast_bus_update(current_app.socketio)
        except Exception as ws_error:
            logger.warning(f"WebSocket更新エラー: {ws_error}")
        
        return jsonify({
            'success': True,
            'message': f'{len(created_reservations)}件の予約を作成しました',
            'reservations': created_reservations
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"予約作成エラー: {str(e)}")
        return jsonify({'success': False, 'message': f'予約作成中にエラーが発生しました: {str(e)}'}), 500