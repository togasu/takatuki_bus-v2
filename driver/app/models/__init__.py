# Driver Service Models
from app.models.driver import Driver, QA

# Export models
__all__ = ['Driver', 'QA']

def register_model_blueprints(app):
    """モデルに定義されたBlueprintを自動登録（現在はなし）"""
    # ドライバーモデルにはBlueprintが定義されていないため何もしない
    pass
