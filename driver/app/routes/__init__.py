import os
import importlib
from app.routes.main_routes import main_bp
from app.routes.yoyaku_routes import yoyaku_bp
from app.routes.question_routes import question_bp
from app.routes.other_routes import tips_bp
from app.routes.message_routes import message_bp

def register_blueprints(app):
    """既存のBlueprintとリファクタリング後のBlueprintを登録"""
    # リファクタリング後のBlueprintを先に登録
    app.register_blueprint(main_bp)
    app.register_blueprint(yoyaku_bp)
    app.register_blueprint(question_bp)
    app.register_blueprint(tips_bp)
    app.register_blueprint(message_bp)
    
    # 既存のBlueprint自動登録機能（indexを最後に登録）
    package_dir = os.path.dirname(__file__)
    for filename in os.listdir(package_dir):
        if filename.endswith(".py") and filename not in ("__init__.py", "main_routes.py", "yoyaku_routes.py", "question_routes.py", "other_routes.py", "message_routes.py"):
            module_name = f"app.routes.{filename[:-3]}"
            module = importlib.import_module(module_name)
            if hasattr(module, "bp"):
                app.register_blueprint(module.bp)
