#!/usr/bin/env python3
"""
Redis Token Manager Test Script
Redisベースのトークン管理機能をテストするためのスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.redis_token import RedisTokenManager

def test_token_manager():
    """トークンマネージャーのテスト"""
    print("=== Redis Token Manager Test ===")
    
    # トークンマネージャーの初期化
    tm = RedisTokenManager()
    
    try:
        # Redis接続テスト
        active_count = tm.get_active_sessions_count()
        print(f"✓ Redis接続成功: 現在のアクティブセッション数 = {active_count}")
    except Exception as e:
        print(f"✗ Redis接続失敗: {e}")
        return
    
    # テストデータ
    test_k_number = "k12345"
    test_student_id = "123456"
    
    print(f"\n=== セッション作成テスト ===")
    token = tm.create_session(test_k_number, test_student_id)
    print(f"✓ トークン作成成功: {token[:10]}...")
    
    print(f"\n=== セッション検証テスト ===")
    session_data = tm.check_session(token)
    if session_data['flag']:
        print(f"✓ セッション検証成功:")
        print(f"  - k_number: {session_data['k_number']}")
        print(f"  - student_id: {session_data['student_id']}")
    else:
        print("✗ セッション検証失敗")
    
    print(f"\n=== 無効なトークンテスト ===")
    invalid_session = tm.check_session("invalid_token")
    if not invalid_session['flag']:
        print("✓ 無効なトークンは正しく拒否されました")
    else:
        print("✗ 無効なトークンが受け入れられました")
    
    print(f"\n=== セッション削除テスト ===")
    delete_result = tm.delete_session(token)
    if delete_result:
        print("✓ セッション削除成功")
    else:
        print("✗ セッション削除失敗")
    
    # 削除後の検証
    deleted_session = tm.check_session(token)
    if not deleted_session['flag']:
        print("✓ 削除されたセッションは正しく無効化されました")
    else:
        print("✗ 削除されたセッションがまだ有効です")
    
    print(f"\n=== 重複セッション管理テスト ===")
    token1 = tm.create_session(test_k_number, test_student_id)
    print(f"✓ 最初のトークン作成: {token1[:10]}...")
    
    token2 = tm.create_session(test_k_number, test_student_id)
    print(f"✓ 二番目のトークン作成: {token2[:10]}...")
    
    # 最初のトークンは無効になっているはず
    first_session = tm.check_session(token1)
    if not first_session['flag']:
        print("✓ 古いセッションは正しく無効化されました")
    else:
        print("✗ 古いセッションがまだ有効です")
    
    # 二番目のトークンは有効なはず
    second_session = tm.check_session(token2)
    if second_session['flag']:
        print("✓ 新しいセッションは有効です")
    else:
        print("✗ 新しいセッションが無効です")
    
    # クリーンアップ
    tm.delete_session(token2)
    
    final_count = tm.get_active_sessions_count()
    print(f"\n=== テスト完了 ===")
    print(f"最終アクティブセッション数: {final_count}")

if __name__ == "__main__":
    test_token_manager()
