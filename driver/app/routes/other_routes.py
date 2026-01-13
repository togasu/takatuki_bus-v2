"""その他のルーティング"""

from flask import Blueprint, render_template
from app.utils.helper_functions import get_authenticated_user

tips_bp = Blueprint('tips', __name__)


@tips_bp.route('/tips')
def tips():
    """説明ページ"""
    user = get_authenticated_user()
    if user:
        return render_template('tips.html')
    return render_template('login.html')