from flask import Blueprint, render_template, request, jsonify
from app.database import db
from app.models.user import User
from app.authorization import require_permission
from app.utils.now_jst import now_jst
from app.api_client import AdminAPIClient

bp = Blueprint('admin_users', __name__)
api_client = AdminAPIClient()

@bp.route('/users', methods=['GET'])
@require_permission("admin_user", "read")
def admin_users_list():
    """管理者ユーザーとドライバーユーザー一覧を表示"""
    # クエリパラメータからフィルタ条件を取得
    user_type = request.args.get('user_type', 'admin')  # 'admin' or 'driver'
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')
    
    users = []
    
    if user_type == 'driver':
        # DriverサービスのAPIから取得
        is_active = None
        if status_filter == 'active':
            is_active = True
        elif status_filter == 'inactive':
            is_active = False
        
        drivers_data = api_client.get_drivers(is_active=is_active, search_query=search_query if search_query else None)
        
        if drivers_data:
            # Driver情報をUser形式に変換
            for driver in drivers_data:
                users.append({
                    'id': driver['id'],
                    'username': driver['username'],
                    'email': f'運転手番号: {driver["number"]}',
                    'role': 'driver',
                    'is_active': driver['is_active'],
                    'last_login': None,
                    'created_at': driver.get('created_at'),
                    'user_type': 'driver'
                })
    else:
        # 管理者ユーザー（既存の処理）
        query = User.query
        
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
        
        admin_users = query.order_by(User.created_at.desc()).all()
        for user in admin_users:
            users.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active,
                'last_login': user.last_login,
                'created_at': user.created_at,
                'user_type': 'admin'
            })
    
    return render_template('admin_users.html', 
                         users=users,
                         user_type=user_type,
                         role_filter=role_filter,
                         status_filter=status_filter,
                         search_query=search_query)

@bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@require_permission("admin_user", "update")
def toggle_user_status(user_id):
    """ユーザーのアクティブ状態を切り替え"""
    user_type = request.args.get('user_type', 'admin')
    
    if user_type == 'driver':
        # DriverサービスのAPIを呼び出し
        result = api_client.toggle_driver_status(user_id)
        if result and result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify({
                'success': False,
                'message': result.get('error', 'ドライバーのステータス変更に失敗しました') if result else '通信エラーが発生しました'
            }), 500
    else:
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
    user_type = request.args.get('user_type', 'admin')
    
    if user_type == 'driver':
        # DriverサービスのAPIを呼び出し
        result = api_client.delete_driver(user_id)
        if result and result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify({
                'success': False,
                'message': result.get('error', 'ドライバーの削除に失敗しました') if result else '通信エラーが発生しました'
            }), 500
    else:
        user = User.query.get_or_404(user_id)
        username = user.username
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'ユーザー {username} を削除しました'
        })
