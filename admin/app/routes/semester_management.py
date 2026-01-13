from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from app.api_client import admin_api
from app.authorization import require_permission
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('semester_management', __name__, url_prefix='/semester_management')

@bp.route('/')
@require_permission('admin', 'view')
def index():
    """学期管理画面"""
    return render_template('semester_management.html')

@bp.route('/api/semesters', methods=['GET'])
@require_permission('admin', 'view')
def get_semesters():
    """学期一覧取得API"""
    try:
        result = admin_api.get_semesters()
        return jsonify(result)
    except Exception as e:
        logger.error(f"学期一覧取得エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'学期一覧取得中にエラーが発生しました: {str(e)}'
        }), 500

@bp.route('/api/active-semester', methods=['GET'])
@require_permission('admin', 'view')
def get_active_semester():
    """アクティブ学期取得API"""
    try:
        result = admin_api.get_active_semester()
        return jsonify(result)
    except Exception as e:
        logger.error(f"アクティブ学期取得エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'アクティブ学期取得中にエラーが発生しました: {str(e)}'
        }), 500

@bp.route('/api/create-semester', methods=['POST'])
@require_permission('admin', 'create')
def create_semester():
    """学期作成API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'リクエストデータが不正です'
            }), 400

        result = admin_api.create_semester(data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"学期作成エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'学期作成中にエラーが発生しました: {str(e)}'
        }), 500

@bp.route('/api/switch-semester', methods=['POST'])
@require_permission('admin', 'update')
def switch_semester():
    """学期切り替えAPI"""
    try:
        data = request.get_json()
        if not data or 'semester_id' not in data:
            return jsonify({
                'success': False,
                'message': '学期IDが指定されていません'
            }), 400

        result = admin_api.switch_semester(data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"学期切り替えエラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'学期切り替え中にエラーが発生しました: {str(e)}'
        }), 500

@bp.route('/api/auto-check', methods=['POST'])
@require_permission('admin', 'update')
def auto_semester_check():
    """自動学期チェックAPI"""
    try:
        result = admin_api.auto_semester_check()
        return jsonify(result)
    except Exception as e:
        logger.error(f"自動学期チェックエラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'自動学期チェック中にエラーが発生しました: {str(e)}'
        }), 500

@bp.route('/api/migrate-users', methods=['POST'])
@require_permission('admin', 'update')
def migrate_users():
    """ユーザー移行API"""
    try:
        data = request.get_json() or {}
        result = admin_api.migrate_users(data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"ユーザー移行エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'ユーザー移行中にエラーが発生しました: {str(e)}'
        }), 500

@bp.route('/api/delete-semester/<int:semester_id>', methods=['DELETE'])
@require_permission('admin', 'delete')
def delete_semester(semester_id):
    """学期削除API"""
    try:
        result = admin_api.delete_semester(semester_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"学期削除エラー: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'学期削除中にエラーが発生しました: {str(e)}'
        }), 500