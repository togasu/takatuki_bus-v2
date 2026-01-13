"""質問・Q&A・メール関連のルーティング"""

from flask import Blueprint, render_template, request
from app.utils.helper_functions import get_authenticated_user
from app.services import QAService
import smtplib
from email.mime.text import MIMEText

question_bp = Blueprint('question', __name__, url_prefix='/question')


@question_bp.route('/')
def question():
    """質問のトップページ"""
    user = get_authenticated_user()
    if user:
        return render_template('question.html')
    return render_template('login.html')


@question_bp.route('/QA')
def qa():
    """Q&Aの表示"""
    user = get_authenticated_user()
    if user:
        qa_list = QAService.get_all_qa()
        return render_template('QA.html', QA=qa_list)
    return render_template('login.html')


@question_bp.route('/mail')
def mail():
    """メールの送信画面"""
    user = get_authenticated_user()
    if user:
        return render_template('mail.html')
    return render_template('login.html')


@question_bp.route('/mail/send', methods=['POST'])
def mailsend():
    """メール送信処理"""
    user = get_authenticated_user()
    if user:
        message = request.form['message']  
        msg = MIMEText(message, "plain", "utf-8")
        msg["From"] = "xxx@xxx.xxx"
        msg["To"] = "yyy@yyy.yyy"
        msg["Subject"] = "メールの件名"

        # TODO: メール送信設定を環境変数化
        smtp = smtplib.SMTP_SSL(host='プロバイダのSMTPメールサーバー', port=465)
        smtp.login('ユーザー名', 'パスワード')
        smtp.send_message(msg)
        smtp.quit()
        return render_template('mail.html', message='メールを送信しました')
    return render_template('login.html')