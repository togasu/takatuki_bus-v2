from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.user import User
from app.authorization import require_permission
from app.utils.now_jst import now_jst

bp = Blueprint('admin_users', __name__)

@bp.route('/users', methods=['GET'])
@require_permission("admin_user", "read")
def admin_users_list():
    """管理者ユーザー一覧を表示"""
    # クエリパラメータからフィルタ条件を取得
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')
    
    # ベースクエリ
    query = User.query
    
    # フィルタ適用
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.filter(
            db.or_(
                User.username.like(search_pattern),
                User.email.like(search_pattern)
            )
        )
    
    # 作成日時の降順でソート
    users = query.order_by(User.created_at.desc()).all()
    
    return render_template('admin_users.html', 
                         users=users,
                         role_filter=role_filter,
                         status_filter=status_filter,
                         search_query=search_query)

@bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@require_permission("admin_user", "update")
def toggle_user_status(user_id):
    """ユーザーのアクティブ状態を切り替え"""
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    user.updated_at = now_jst()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'user_id': user.id,
        'is_active': user.is_active,
        'message': f'ユーザー {user.username} のステータスを{"有効" if user.is_active else "無効"}に変更しました'
    })

@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@require_permission("admin_user", "delete")
def delete_user(user_id):
    """ユーザーを削除"""
    user = User.query.get_or_404(user_id)
    username = user.username
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'ユーザー {username} を削除しました'
    })
