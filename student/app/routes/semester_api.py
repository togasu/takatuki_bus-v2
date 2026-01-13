from flask import Blueprint, request, jsonify
from app.utils.semester_utils import SemesterManager
from app.database import db
import logging

logger = logging.getLogger(__name__)

semester_api_bp = Blueprint('semester_api', __name__, url_prefix='/api/semester')

@semester_api_bp.route('/list', methods=['GET'])
def get_semesters():
    """全ての学期を取得"""
    try:
        semesters = SemesterManager.get_all_semesters()
        return jsonify({
            'success': True,
            'semesters': [semester.to_dict() for semester in semesters]
        })
    except Exception as e:
        logger.error(f"学期一覧取得エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'学期一覧の取得に失敗しました: {str(e)}'
        }), 500

@semester_api_bp.route('/active', methods=['GET'])
def get_active_semester():
    """アクティブな学期を取得"""
    try:
        semester = SemesterManager.get_active_semester()
        if semester:
            return jsonify({
                'success': True,
                'semester': semester.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'アクティブな学期がありません'
            }), 404
    except Exception as e:
        logger.error(f"アクティブ学期取得エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'アクティブ学期の取得に失敗しました: {str(e)}'
        }), 500

@semester_api_bp.route('/current', methods=['GET'])
def get_current_semester():
    """現在の日付に基づく学期を取得"""
    try:
        semester = SemesterManager.get_current_semester()
        if semester:
            return jsonify({
                'success': True,
                'semester': semester.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'message': '現在の日付に該当する学期がありません'
            }), 404
    except Exception as e:
        logger.error(f"現在学期取得エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'現在学期の取得に失敗しました: {str(e)}'
        }), 500

@semester_api_bp.route('/create', methods=['POST'])
def create_semester():
    """新しい学期を作成"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'リクエストデータが不正です'
            }), 400

        required_fields = ['name', 'start_date', 'end_date']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'必須フィールド「{field}」が不足しています'
                }), 400

        semester, message = SemesterManager.create_semester(
            name=data['name'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            is_active=data.get('is_active', False)
        )

        if semester:
            return jsonify({
                'success': True,
                'message': message,
                'semester': semester.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400

    except Exception as e:
        logger.error(f"学期作成エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'学期作成に失敗しました: {str(e)}'
        }), 500

@semester_api_bp.route('/activate/<int:semester_id>', methods=['POST'])
def activate_semester(semester_id):
    """学期をアクティブにする"""
    try:
        success, message = SemesterManager.activate_semester(semester_id)
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400

    except Exception as e:
        logger.error(f"学期アクティベーションエラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'学期のアクティベーションに失敗しました: {str(e)}'
        }), 500

@semester_api_bp.route('/switch', methods=['POST'])
def switch_semester():
    """学期を切り替える（ユーザー移行込み）"""
    try:
        data = request.get_json()
        if not data or 'semester_id' not in data:
            return jsonify({
                'success': False,
                'message': '学期IDが指定されていません'
            }), 400

        semester_id = data['semester_id']
        migrate_users = data.get('migrate_users', True)

        success, message = SemesterManager.switch_semester(semester_id, migrate_users)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400

    except Exception as e:
        logger.error(f"学期切り替えエラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'学期切り替えに失敗しました: {str(e)}'
        }), 500

@semester_api_bp.route('/auto-check', methods=['POST'])
def auto_semester_check():
    """自動学期チェック・切り替え"""
    try:
        success, message = SemesterManager.auto_semester_check()
        
        return jsonify({
            'success': success,
            'message': message
        })

    except Exception as e:
        logger.error(f"自動学期チェックエラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'自動学期チェックに失敗しました: {str(e)}'
        }), 500

@semester_api_bp.route('/migrate-users', methods=['POST'])
def migrate_users():
    """手動でユーザーを移行"""
    try:
        data = request.get_json() or {}
        from_semester_id = data.get('from_semester_id')
        to_semester_id = data.get('to_semester_id')

        success, message, migrated_count = SemesterManager.migrate_users_to_last_semester(
            from_semester_id=from_semester_id,
            to_semester_id=to_semester_id
        )

        if success:
            return jsonify({
                'success': True,
                'message': message,
                'migrated_count': migrated_count
            })
        else:
            return jsonify({
                'success': False,
                'message': message,
                'migrated_count': migrated_count
            }), 400

    except Exception as e:
        logger.error(f"ユーザー移行エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'ユーザー移行に失敗しました: {str(e)}',
            'migrated_count': 0
        }), 500

@semester_api_bp.route('/delete/<int:semester_id>', methods=['DELETE'])
def delete_semester(semester_id):
    """学期を削除"""
    try:
        success, message = SemesterManager.delete_semester(semester_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400

    except Exception as e:
        logger.error(f"学期削除エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'学期削除に失敗しました: {str(e)}'
        }), 500