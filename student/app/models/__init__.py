import os
import importlib
import inspect
from app.database import db
from flask import Blueprint

# 現在のディレクトリのパスを取得
current_dir = os.path.dirname(__file__)

# 自動的にモデルをインポートする
_models = {}
_blueprints = {}
_all_exports = []

# このディレクトリ内のすべての.pyファイルを探索
for filename in os.listdir(current_dir):
    if filename.endswith('.py') and filename != '__init__.py':
        module_name = filename[:-3]  # .pyを削除
        
        try:
            # モジュールを動的にインポート
            module = importlib.import_module(f'.{module_name}', package=__name__)
            
            # モジュール内のすべてのクラスを検査
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # SQLAlchemyのModelを継承しているクラスのみを対象
                if hasattr(obj, '__tablename__') and issubclass(obj, db.Model):
                    _models[name] = obj
                    _all_exports.append(name)
                    # グローバルスコープに追加（直接インポート可能にする）
                    globals()[name] = obj
            
            # Blueprintも同様に検査
            for name, obj in inspect.getmembers(module):
                if isinstance(obj, Blueprint):
                    _blueprints[name] = obj
                    _all_exports.append(name)
                    # グローバルスコープに追加
                    globals()[name] = obj
                    
        except ImportError as e:
            print(f"Warning: Could not import {module_name}: {e}")

# __all__を動的に設定
__all__ = _all_exports

# デバッグ用：ロードされたモデルとBlueprintを表示
if __debug__:
    print(f"Student models loaded: {list(_models.keys())}")
    print(f"Student blueprints loaded: {list(_blueprints.keys())}")

# Blueprintを自動登録するための関数
def register_model_blueprints(app):
    """モデルに定義されたBlueprintを自動登録"""
    for bp_name, blueprint in _blueprints.items():
        app.register_blueprint(blueprint)
        print(f"Registered blueprint: {bp_name}")
