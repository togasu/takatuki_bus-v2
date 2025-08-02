from flask import Blueprint

bp = Blueprint("health", __name__)

@bp.route("/health", methods=["GET"])
def health():
    """
    Nginxで設定されたヘルスチェック用のエンドポイント関数
    """
    return {
        "status": "ok",
        "service": "Student Service"
    }
