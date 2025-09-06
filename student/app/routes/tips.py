from flask import Blueprint, render_template, redirect, url_for, session

bp = Blueprint("tips", __name__)

@bp.route("/tips", methods=["GET"])
def tips():
    return render_template("tips.html")