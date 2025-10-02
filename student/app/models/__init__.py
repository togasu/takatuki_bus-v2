import os
import importlib
from pathlib import Path

# 現在のディレクトリのパスを取得
current_dir = Path(__file__).parent

# 動的に全ての.pyファイルをインポート
__all__ = []

# 除外するファイル名
EXCLUDE_FILES = {'__init__.py', 'token.py', 'admin.py', 'model_helper.py'}  # admin.pyとmodel_helper.pyも除外

for file_path in current_dir.glob('*.py'):
    filename = file_path.name
    
    # 除外ファイルをスキップ
    if filename in EXCLUDE_FILES:
        continue
    
    # モジュール名を取得（.pyを除く）
    module_name = filename[:-3]
    
    try:
        # 動的にモジュールをインポート
        module = importlib.import_module(f'.{module_name}', package=__name__)
        
        # モジュール内の全ての公開クラス/関数を取得
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            # クラスまたは関数で、プライベート属性でない場合
            if not attr_name.startswith('_') and (
                hasattr(attr, '__module__') and 
                attr.__module__ == module.__name__
            ):
                # グローバル名前空間に追加
                globals()[attr_name] = attr
                __all__.append(attr_name)
                
    except ImportError as e:
        # インポートエラーが発生した場合は警告を出力（本番環境では適切なログに変更）
        print(f"Warning: Could not import {module_name}: {e}")
        continue

# 明示的なインポートも維持（後方互換性のため）
try:
    from .bus import Bus
    from .seat import Seat
    from .reservation import Reservation
    from .user import User, User_Penalty, LastSemester_user
    from .cancel import Cancel
    
    # 明示的なインポートを__all__に追加（重複を避ける）
    explicit_imports = ['Bus', 'Seat', 'Reservation', 'User', 'User_Penalty', 'LastSemester_user', 'Cancel']
    for item in explicit_imports:
        if item not in __all__:
            __all__.append(item)
            
except ImportError as e:
    print(f"Warning: Could not import some models explicitly: {e}")

# __all__をソートして読みやすくする
__all__ = sorted(list(set(__all__)))
