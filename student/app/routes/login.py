from flask import Blueprint
from flask import render_template

bp = Blueprint("login", __name__)

@bp.route("/login", methods=["GET"])
def login():
    return render_template("login.html")
