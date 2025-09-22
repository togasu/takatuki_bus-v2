from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from app.api_client import admin_api
from app.authorization import require_permission
import logging

# ログの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bp = Blueprint('student_management', __name__, url_prefix='/student_management')

@bp.route('/')
@require_permission('student', 'view')
def index():
    """学生管理画面"""
    return render_template('student_management.html')

@bp.route('/all_students', methods=['GET'])
@require_permission('student', 'view')
def get_all_students():
    """全学生一覧取得API"""
    try:
        logger.info(f"=== get_all_students API called ===")
        logger.info(f"Request path: {request.path}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request args: {dict(request.args)}")
        logger.info(f"Session data: {dict(session)}")
        logger.info(f"Cookies: {dict(request.cookies)}")
        
        # 現在のユーザー情報を取得して確認
        from app.auth import get_current_user
        current_user = get_current_user()
        logger.info(f"Current user: {current_user.username if current_user else 'None'}")
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        logger.info(f"全学生取得リクエスト開始: page={page}, per_page={per_page}")
        
        # student サービスのAPIを呼び出し
        result = admin_api.get_all_students(page=page, per_page=per_page)
        
        logger.info(f"student API レスポンス: success={result.get('success')}")
        if not result.get('success'):
            logger.error(f"student API エラー: {result.get('message')}")
        
        if result.get('success'):
            logger.info(f"全学生取得成功: page={page}, per_page={per_page}, total={result.get('pagination', {}).get('total', 0)}")
        else:
            logger.warning(f"全学生取得失敗: {result.get('message')}")
        
        logger.info(f"Returning response: {type(result)}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"全学生取得エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'学生一覧取得中にエラーが発生しました: {str(e)}'
        }), 500

@bp.route('/search', methods=['POST'])
@require_permission('student', 'view')
def search_student():
    """学生検索API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'リクエストデータが不正です'
            }), 400
        
        student_id = data.get('student_id', '').strip()
        username = data.get('username', '').strip()
        
        if not student_id and not username:
            return jsonify({
                'success': False,
                'message': '学籍番号またはユーザー名を入力してください'
            }), 400
        
        # student サービスのAPIを呼び出し
        result = admin_api.search_student(student_id=student_id, username=username)
        
        if result.get('success'):
            logger.info(f"学生検索成功: {student_id or username}")
        else:
            logger.warning(f"学生検索失敗: {student_id or username} - {result.get('message')}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"学生検索エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'検索中にエラーが発生しました: {str(e)}'
        }), 500

@bp.route('/delete', methods=['POST'])
@require_permission('student', 'delete')
def delete_student():
    """学生削除API"""
    try:
        data = request.get_json()
        if not data or 'student_id' not in data:
            return jsonify({
                'success': False,
                'message': '学籍番号が指定されていません'
            }), 400
        
        student_id = data['student_id']
        
        # student サービスのAPIを呼び出し
        result = admin_api.delete_student_account(student_id)
        
        if result.get('success'):
            logger.info(f"学生削除成功: {student_id}")
        else:
            logger.warning(f"学生削除失敗: {student_id} - {result.get('message')}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"学生削除エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'削除中にエラーが発生しました: {str(e)}'
        }), 500

@bp.route('/clear_penalty', methods=['POST'])
@require_permission('student', 'update')
def clear_penalty():
    """ペナルティ解除API"""
    try:
        data = request.get_json()
        if not data or 'student_id' not in data:
            return jsonify({
                'success': False,
                'message': '学籍番号が指定されていません'
            }), 400
        
        student_id = data['student_id']
        
        # student サービスのAPIを呼び出し
        result = admin_api.clear_student_penalty(student_id)
        
        if result.get('success'):
            logger.info(f"ペナルティ解除成功: {student_id}")
        else:
            logger.warning(f"ペナルティ解除失敗: {student_id} - {result.get('message')}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"ペナルティ解除エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'ペナルティ解除中にエラーが発生しました: {str(e)}'
        }), 500

@bp.route('/apply_penalty', methods=['POST'])
@require_permission('student', 'update')
def apply_penalty():
    """ペナルティ付与API"""
    try:
        data = request.get_json()
        if not data or 'student_id' not in data:
            return jsonify({
                'success': False,
                'message': '学籍番号が指定されていません'
            }), 400
        
        student_id = data['student_id']
        reason = data.get('reason', '管理者による手動ペナルティ')
        
        # student サービスのAPIを呼び出し
        result = admin_api.apply_student_penalty(student_id, reason)
        
        if result.get('success'):
            logger.info(f"ペナルティ付与成功: {student_id}, 理由: {reason}")
        else:
            logger.warning(f"ペナルティ付与失敗: {student_id} - {result.get('message')}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"ペナルティ付与エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'ペナルティ付与中にエラーが発生しました: {str(e)}'
        }), 500

@bp.route('/reservations/<student_id>', methods=['GET'])
@require_permission('student', 'view')
def get_reservations(student_id):
    """学生の予約情報取得API"""
    try:
        # student サービスのAPIを呼び出し
        result = admin_api.get_student_reservations(student_id)
        
        if result.get('success'):
            logger.info(f"予約情報取得成功: {student_id}")
        else:
            logger.warning(f"予約情報取得失敗: {student_id} - {result.get('message')}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"予約情報取得エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'予約情報取得中にエラーが発生しました: {str(e)}'
        }), 500

@bp.route('/debug_auth', methods=['GET'])
def debug_auth():
    """認証デバッグ用エンドポイント（開発用）"""
    try:
        from app.auth import get_current_user
        from app.utils.auth_utils import SessionManager
        
        debug_info = {
            'session_data': dict(session),
            'cookies': dict(request.cookies),
            'headers': dict(request.headers),
            'current_user': None,
            'session_validation': None,
            'request_info': {
                'path': request.path,
                'url': request.url,
                'endpoint': request.endpoint,
                'blueprint': request.blueprint
            }
        }
        
        # 現在のユーザー情報を取得
        current_user = get_current_user()
        if current_user:
            debug_info['current_user'] = {
                'id': current_user.id,
                'username': current_user.username,
                'role': current_user.role,
                'is_active': current_user.is_active
            }
        
        # セッショントークンの検証
        session_token = request.cookies.get('admin_session_token')
        if session_token:
            session_manager = SessionManager()
            session_data = session_manager.validate_session(session_token)
            debug_info['session_validation'] = session_data
        
        return jsonify({
            'success': True,
            'debug_info': debug_info
        })
    except Exception as e:
        logger.error(f"認証デバッグエラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'認証デバッグ中にエラーが発生しました: {str(e)}'
        }), 500

@bp.route('/test', methods=['GET'])
def test_endpoint():
    """シンプルなテスト用エンドポイント"""
    return jsonify({
        'success': True,
        'message': 'Student management blueprint is working!',
        'path': request.path,
        'blueprint': request.blueprint
    })