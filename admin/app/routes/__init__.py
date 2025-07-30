import os
import importlib

def register_blueprints(app):
    package_dir = os.path.dirname(__file__)
    for filename in os.listdir(package_dir):
        if filename.endswith(".py") and filename not in ("__init__.py",):
            module_name = f"app.routes.{filename[:-3]}"
            module = importlib.import_module(module_name)
            if hasattr(module, "bp"):
                app.register_blueprint(module.bp)
