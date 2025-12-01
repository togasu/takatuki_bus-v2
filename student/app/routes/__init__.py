from .auth import auth_bp
from .main import main_bp
from .booking import booking_bp
from .cancel import cancel_bp
from .management_api import management_api_bp
from .statistics_api import statistics_api_bp
from .semester_api import semester_api_bp
from .ws import ws_bp
from .seat_info import seat_info_bp

def register_blueprints(app):
    """全てのブループリントを登録"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(cancel_bp)
    app.register_blueprint(management_api_bp)
    app.register_blueprint(statistics_api_bp)
    app.register_blueprint(semester_api_bp)
    app.register_blueprint(ws_bp)
    app.register_blueprint(seat_info_bp)
