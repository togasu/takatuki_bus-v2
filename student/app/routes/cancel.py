from flask import Blueprint, redirect, url_for, flash

bp = Blueprint('cancel', __name__)

@bp.route('/cancelcheck', methods=['POST'])
def cancelcheck():
    # 予約キャンセル処理を実装
    flash('予約がキャンセルされました。', 'success')
    return redirect(url_for('top.index'))

