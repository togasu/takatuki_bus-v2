from flask import Blueprint
from flask import render_template

bp = Blueprint("auth", __name__)

@bp.route("/auth", methods=["GET"])
def auth():
    return render_template("auth.html")