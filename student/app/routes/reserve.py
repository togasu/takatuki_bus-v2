from flask import Blueprint, render_template, redirect, url_for, flash

bp = Blueprint('reserve', __name__)

@bp.route('/reserve', methods=['POST'])
def reserve():
    # 予約処理を実装
    flash('予約が完了しました。', 'success')
    return redirect(url_for('top.index'))

@bp.route('/choice', methods=['GET'])
def choice():
    # 予約選択処理を実装
    return render_template('choice.html')