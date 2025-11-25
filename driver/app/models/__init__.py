# Driver Service Models
from app.models.driver import Driver, QA, Bus, Seat, Reservation

# Export models
# Hash は Redis で管理するため削除
__all__ = ['Driver', 'QA', 'Bus', 'Seat', 'Reservation']

def register_model_blueprints(app):
    """モデルに定義されたBlueprintを自動登録（現在はなし）"""
    # ドライバーモデルにはBlueprintが定義されていないため何もしない
    pass
