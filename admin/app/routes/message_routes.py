"""メッセージ管理機能のルーティング (Admin側)"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.message import DriverMessage
from app.database import db
from app.authorization import require_permission
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('messages', __name__, url_prefix='/messages')


@bp.route('/', methods=['GET'])
@require_permission('driver_messages', 'read')
def messages_inbox():
    """メッセージ受信箱"""
    try:
        # フィルター取得
        filter_type = request.args.get('filter', 'all')
        
        # ベースクエリ
        query = DriverMessage.query
        
        # フィルター適用
        if filter_type == 'unread':
            query = query.filter_by(is_read=False)
        elif filter_type == 'unreplied':
            query = query.filter_by(replied=False)
        elif filter_type == 'urgent':
            query = query.filter_by(priority='urgent')
        
        # メッセージ取得（新しい順）
        messages = query.order_by(DriverMessage.created_at.desc()).all()
        
        # 統計情報
        unread_count = DriverMessage.get_unread_count()
        unreplied_count = DriverMessage.get_unreplied_count()
        
        return render_template('messages.html',
                             messages=messages,
                             filter_type=filter_type,
                             unread_count=unread_count,
                             unreplied_count=unreplied_count)
        
    except Exception as e:
        logger.error(f"Error retrieving messages: {e}", exc_info=True)
        flash('メッセージの取得中にエラーが発生しました', 'danger')
        return render_template('messages.html',
                             messages=[],
                             filter_type='all',
                             unread_count=0,
                             unreplied_count=0)


@bp.route('/mark-read/<int:message_id>', methods=['POST'])
@require_permission('driver_messages', 'read')
def mark_as_read(message_id):
    """メッセージを既読にする"""
    try:
        message = DriverMessage.query.get_or_404(message_id)
        
        from flask import session
        admin_username = session.get('username', 'admin')
        
        message.mark_as_read(admin_username)
        flash('メッセージを既読にしました', 'success')
        
    except Exception as e:
        logger.error(f"Error marking message as read: {e}", exc_info=True)
        flash('既読処理中にエラーが発生しました', 'danger')
    
    return redirect(url_for('messages.messages_inbox'))


@bp.route('/reply/<int:message_id>', methods=['POST'])
@require_permission('driver_messages', 'update')
def reply_to_message(message_id):
    """メッセージに返信する"""
    try:
        message = DriverMessage.query.get_or_404(message_id)
        reply_text = request.form.get('reply_message', '').strip()
        
        if not reply_text:
            flash('返信メッセージを入力してください', 'danger')
            return redirect(url_for('messages.messages_inbox'))
        
        from flask import session
        admin_username = session.get('username', 'admin')
        
        message.add_reply(reply_text, admin_username)
        
        # 既読にもする
        if not message.is_read:
            message.mark_as_read(admin_username)
        
        flash(f'{message.driver_username}へ返信しました', 'success')
        logger.info(f"Reply sent to {message.driver_username} by {admin_username}")
        
    except Exception as e:
        logger.error(f"Error replying to message: {e}", exc_info=True)
        flash('返信処理中にエラーが発生しました', 'danger')
    
    return redirect(url_for('messages.messages_inbox'))
