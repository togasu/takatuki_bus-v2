#!/bin/bash
# テストユーザー作成スクリプト

echo "=== テストユーザー作成 ==="

echo "Adminテストユーザーを作成中..."
docker-compose exec admin python create_test_admin.py

echo "Driverテストユーザーを作成中..."
docker-compose exec driver python create_test_driver.py

echo ""
echo "=== テストユーザー情報 ==="
echo "Admin:"
echo "  URL: https://localhost/admin/"
echo "  ユーザー名: admin_test"
echo "  パスワード: admin123"
echo ""
echo "Driver:"
echo "  URL: https://localhost/driver/"
echo "  ユーザー名: driver_test"
echo "  パスワード: driver123"
echo ""
echo "Student:"
echo "  URL: https://localhost/student/"
echo "  ユーザー名: LDAPアカウント（設定に依存）"
echo ""
echo "=== 完了 ==="
