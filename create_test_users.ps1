# テストユーザー作成スクリプト (PowerShell)

Write-Host "=== テストユーザー作成 ===" -ForegroundColor Green

Write-Host "Adminテストユーザーを作成中..." -ForegroundColor Yellow
docker-compose exec admin python create_test_admin.py

Write-Host "Driverテストユーザーを作成中..." -ForegroundColor Yellow  
docker-compose exec driver python create_test_driver.py

Write-Host ""
Write-Host "=== テストユーザー情報 ===" -ForegroundColor Green
Write-Host "Admin:" -ForegroundColor Cyan
Write-Host "  URL: https://localhost/admin/" -ForegroundColor White
Write-Host "  ユーザー名: admin_test" -ForegroundColor White
Write-Host "  パスワード: admin123" -ForegroundColor White
Write-Host ""
Write-Host "Driver:" -ForegroundColor Cyan
Write-Host "  URL: https://localhost/driver/" -ForegroundColor White
Write-Host "  ユーザー名: driver_test" -ForegroundColor White
Write-Host "  パスワード: driver123" -ForegroundColor White
Write-Host ""
Write-Host "Student:" -ForegroundColor Cyan
Write-Host "  URL: https://localhost/student/" -ForegroundColor White
Write-Host "  ユーザー名: LDAPアカウント（設定に依存）" -ForegroundColor White
Write-Host ""
Write-Host "=== 完了 ===" -ForegroundColor Green
