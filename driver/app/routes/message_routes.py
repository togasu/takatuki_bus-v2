"""メッセージ送信機能のルーティング"""

from flask import Blueprint, render_template, request, redirect, url_for
from app.utils.helper_functions import get_authenticated_user
from app.models import DriverMessage, Driver
from app.database import db
import logging

logger = logging.getLogger(__name__)

message_bp = Blueprint('message', __name__, url_prefix='/message')


@message_bp.route('/send', methods=['GET'])
def send_message_form():
    """メッセージ送信フォーム"""
    user = get_authenticated_user()
    if not user:
        return render_template('login.html')
    
    return render_template('message_send.html')


@message_bp.route('/send', methods=['POST'])
def send_message():
    """メッセージ送信処理"""
    user = get_authenticated_user()
    if not user:
        return render_template('login.html')
    
    try:
        # フォームデータ取得
        subject = request.form.get('subject', '').strip()
        message_text = request.form.get('message_text', '').strip()
        priority = request.form.get('priority', 'normal')
        
        # バリデーション
        if not subject or not message_text:
            return render_template('message_send.html', 
                                 message='件名とメッセージは必須です')
        
        # ドライバー情報取得
        driver = Driver.query.filter_by(username=user).first()
        if not driver:
            return render_template('message_send.html',
                                 message='ドライバー情報が見つかりません')
        
        # メッセージ作成
        new_message = DriverMessage(
            driver_id=driver.id,
            driver_username=user,
            subject=subject,
            message=message_text,
            priority=priority
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        logger.info(f"Message sent from {user}: {subject}")
        
        return render_template('message_send.html', success=True)
        
    except Exception as e:
        logger.error(f"Error sending message: {e}", exc_info=True)
        db.session.rollback()
        return render_template('message_send.html',
                             message='メッセージ送信中にエラーが発生しました')


@message_bp.route('/sent', methods=['GET'])
def sent_messages():
    """送信済みメッセージ一覧"""
    user = get_authenticated_user()
    if not user:
        return render_template('login.html')
    
    try:
        driver = Driver.query.filter_by(username=user).first()
        if not driver:
            return render_template('message_list.html', messages=[])
        
        # 送信済みメッセージを取得（新しい順）
        messages = DriverMessage.query.filter_by(driver_id=driver.id)\
            .order_by(DriverMessage.created_at.desc())\
            .all()
        
        return render_template('message_list.html', messages=messages)
        
    except Exception as e:
        logger.error(f"Error retrieving messages: {e}", exc_info=True)
        return render_template('message_list.html', messages=[])
