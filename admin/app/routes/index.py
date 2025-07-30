from flask import Blueprint

bp = Blueprint("index", __name__)

@bp.route("/", methods=["GET"])
def index():
    return {
        "service": "Admin",
        "message": "HTTP route works!"
    }
