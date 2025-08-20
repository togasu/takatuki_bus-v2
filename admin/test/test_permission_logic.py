#!/usr/bin/env python3
"""
権限システムの独立テスト
"""

def test_permission_logic():
    """権限ロジックのテスト"""
    
    def check_guest_permissions(resource, action):
        """
        guest権限のチェック
        studentのbusとseat（予約者名を除く）の個人情報を含まない情報のAPIのみ
        """
        allowed_permissions = [
            ("student_bus", "read"),
            ("student_seat", "read")
        ]
        
        return (resource, action) in allowed_permissions

    def check_normal_permissions(resource, action):
        """
        normal権限のチェック
        アカウント作成・削除以外のすべて
        """
        # アカウント作成・削除は禁止
        if resource == "admin_user" and action in ["create", "delete"]:
            return False
        
        # その他の操作は許可
        allowed_resources = [
            "admin_user",      # 読み取り・更新のみ
            "admin_permission",
            "driver",
            "student",
            "student_bus",
            "student_seat",
            "student_course",
            "student_season"
        ]
        
        return resource in allowed_resources

    def has_permission(user_role, resource, action):
        """権限チェック"""
        if user_role == "admin":
            # adminは全ての権限を持つ
            return True
        elif user_role == "normal":
            # normalは特定の権限を持つ
            return check_normal_permissions(resource, action)
        elif user_role == "guest":
            # guestは限定された権限のみ
            return check_guest_permissions(resource, action)
        
        return False

    # テストケース
    test_cases = [
        # ユーザーロール, リソース, アクション, 期待値
        ("guest", "student_bus", "read", True),
        ("guest", "student_seat", "read", True),
        ("guest", "admin_user", "read", False),
        ("guest", "admin_user", "create", False),
        
        ("normal", "student_bus", "read", True),
        ("normal", "student_seat", "read", True),
        ("normal", "admin_user", "read", True),
        ("normal", "admin_user", "update", True),
        ("normal", "admin_user", "create", False),
        ("normal", "admin_user", "delete", False),
        ("normal", "driver", "all", True),
        ("normal", "student", "all", True),
        
        ("admin", "student_bus", "read", True),
        ("admin", "admin_user", "create", True),
        ("admin", "admin_user", "delete", True),
        ("admin", "system", "all", True),
    ]
    
    print("=== 権限システム テスト結果 ===\n")
    
    passed = 0
    failed = 0
    
    for role, resource, action, expected in test_cases:
        result = has_permission(role, resource, action)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        print(f"{status} {role:8} | {resource:15} | {action:8} | 期待値: {expected}, 結果: {result}")
        
        if result == expected:
            passed += 1
        else:
            failed += 1
    
    print(f"\n=== テスト結果 ===")
    print(f"合格: {passed}")
    print(f"失敗: {failed}")
    print(f"合計: {passed + failed}")
    
    if failed == 0:
        print("✓ すべてのテストが合格しました！")
    else:
        print(f"✗ {failed}個のテストが失敗しました。")

if __name__ == "__main__":
    test_permission_logic()
