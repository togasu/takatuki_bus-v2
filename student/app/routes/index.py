from flask import Blueprint

bp = Blueprint("index", __name__)

@bp.route("/", methods=["GET"])
def index():
    return {
        "service": "Student",
        "message": "HTTP route works!"
    }
