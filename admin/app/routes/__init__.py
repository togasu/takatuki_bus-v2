import os
import importlib

def register_blueprints(app):
    print("=== Blueprint登録開始 ===")
    package_dir = os.path.dirname(__file__)
    for filename in os.listdir(package_dir):
        if filename.endswith(".py") and filename not in ("__init__.py",):
            module_name = f"app.routes.{filename[:-3]}"
            print(f"モジュール読み込み: {module_name}")
            module = importlib.import_module(module_name)
            if hasattr(module, "bp"):
                print(f"Blueprint登録: {module.bp.name}")
                app.register_blueprint(module.bp)
            else:
                print(f"Blueprint not found in {module_name}")
    print("=== Blueprint登録完了 ===")
