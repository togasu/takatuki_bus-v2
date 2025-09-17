from .auth import auth_bp
from .main import main_bp
from .booking import booking_bp
from .cancel import cancel_bp

def register_blueprints(app):
    """全てのブループリントを登録"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(cancel_bp)
