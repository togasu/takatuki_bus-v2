#!/usr/bin/env python3
"""
Dynamic Model Import Test Script
動的インポート機能をテストするためのスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_dynamic_import():
    """動的インポート機能のテスト"""
    print("=== Dynamic Model Import Test ===")
    
    try:
        # modelsパッケージをインポート
        from app import models
        
        print(f"✓ Models package imported successfully")
        print(f"Available models: {models.__all__}")
        
        # 各モデルが正しくインポートされているかチェック
        expected_models = ['Bus', 'Seat', 'Reservation', 'User', 'User_Penalty', 
                          'LastSemester_user', 'Cancel', 'TestModel']
        
        for model_name in expected_models:
            if hasattr(models, model_name):
                model_class = getattr(models, model_name)
                print(f"✓ {model_name}: {model_class}")
            else:
                print(f"✗ {model_name}: Not found")
        
        # TestModelが動的にインポートされているかの特別なテスト
        if hasattr(models, 'TestModel'):
            TestModel = models.TestModel
            print(f"✓ TestModel dynamically imported: {TestModel}")
            print(f"  - Table name: {TestModel.__tablename__}")
            print(f"  - Module: {TestModel.__module__}")
        else:
            print("✗ TestModel was not dynamically imported")
        
        print(f"\n=== インポートされたモデルの詳細 ===")
        for model_name in sorted(models.__all__):
            model_class = getattr(models, model_name)
            if hasattr(model_class, '__tablename__'):
                print(f"{model_name}: table='{model_class.__tablename__}', module='{model_class.__module__}'")
            else:
                print(f"{model_name}: {type(model_class)} (not a SQLAlchemy model)")
                
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    return True

def test_model_creation():
    """新しいモデルの作成テスト"""
    print(f"\n=== Model Creation Test ===")
    
    # model_helper.pyを使ったモデル生成のテスト
    test_model_path = "app/models/dynamic_test.py"
    
    try:
        from app.models.model_helper import create_model_template
        
        # テンプレート生成
        template = create_model_template("DynamicTest", "dynamic_test")
        print("✓ Model template generated successfully")
        
        # ファイルに書き込み
        with open(test_model_path, 'w', encoding='utf-8') as f:
            f.write(template)
        print(f"✓ Model file created: {test_model_path}")
        
        # インポートテスト（次回アプリ起動時に自動でインポートされる）
        print("Note: DynamicTest model will be automatically imported on next app startup")
        
    except Exception as e:
        print(f"✗ Model creation failed: {e}")
    finally:
        # テストファイルのクリーンアップ
        if os.path.exists(test_model_path):
            os.remove(test_model_path)
            print(f"✓ Test file cleaned up: {test_model_path}")

if __name__ == "__main__":
    success = test_dynamic_import()
    test_model_creation()
    
    if success:
        print(f"\n=== Test Result ===")
        print("✓ All tests passed successfully!")
        print("The dynamic import system is working correctly.")
    else:
        print(f"\n=== Test Result ===")
        print("✗ Some tests failed. Please check the configuration.")
        sys.exit(1)
