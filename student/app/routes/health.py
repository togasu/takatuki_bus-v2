from flask import Blueprint

bp = Blueprint("health", __name__)

@bp.route("/health", methods=["GET"])
def health():
    return {
        "status": "ok",
        "service": "Service 1"
    }
