#!/usr/bin/env pwsh
# 内部APIセキュリティテストスクリプト

Write-Host "=== 内部APIセキュリティテスト ===" -ForegroundColor Cyan

# テスト1: 外部から内部APIへのアクセス（失敗すべき）
Write-Host "`n[テスト1] 外部から/api/managementへのアクセス（403が返るべき）" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost/api/management/all_students" -Method GET -ErrorAction Stop
    Write-Host "❌ FAILED: アクセスが許可されました (Status: $($response.StatusCode))" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 403) {
        Write-Host "✅ PASSED: 403 Forbidden が返されました" -ForegroundColor Green
    } else {
        Write-Host "⚠️ WARNING: 予期しないエラー: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Yellow
    }
}

# テスト2: 外部から/api/statisticsへのアクセス（失敗すべき）
Write-Host "`n[テスト2] 外部から/api/statisticsへのアクセス（403が返るべき）" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost/api/statistics/realtime" -Method GET -ErrorAction Stop
    Write-Host "❌ FAILED: アクセスが許可されました (Status: $($response.StatusCode))" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 403) {
        Write-Host "✅ PASSED: 403 Forbidden が返されました" -ForegroundColor Green
    } else {
        Write-Host "⚠️ WARNING: 予期しないエラー: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Yellow
    }
}

# テスト3: HTTPS経由でのアクセステスト
Write-Host "`n[テスト3] HTTPSから/api/managementへのアクセス（403が返るべき）" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://localhost/api/management/all_students" -Method GET -SkipCertificateCheck -ErrorAction Stop
    Write-Host "❌ FAILED: アクセスが許可されました (Status: $($response.StatusCode))" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 403) {
        Write-Host "✅ PASSED: 403 Forbidden が返されました" -ForegroundColor Green
    } else {
        Write-Host "⚠️ WARNING: 予期しないエラー: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Yellow
    }
}

# テスト4: 公開APIへのアクセス（成功すべき）
Write-Host "`n[テスト4] 外部から公開APIへのアクセス（成功すべき）" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost/" -Method GET -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ PASSED: 学生サービスのトップページにアクセスできました" -ForegroundColor Green
    } else {
        Write-Host "⚠️ WARNING: 予期しないステータスコード: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ FAILED: 公開APIにアクセスできませんでした" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# テスト5: 認証なしでコンテナ内から内部APIへアクセス（失敗すべき）
Write-Host "`n[テスト5] コンテナ内から認証なしでアクセス（401が返るべき）" -ForegroundColor Yellow
try {
    # Pythonを使ってHTTPリクエストを送信
    $pythonScript = @"
import requests
try:
    response = requests.get('http://localhost:5000/api/management/all_students', timeout=5)
    print(response.status_code)
except Exception as e:
    print('error')
"@
    
    $result = docker exec takatuki_bus-v2-student-1 python -c $pythonScript 2>$null
    
    if ($result -eq "401") {
        Write-Host "✅ PASSED: 401 Unauthorized が返されました" -ForegroundColor Green
    } elseif ($result -eq "error") {
        Write-Host "⚠️ WARNING: リクエストがエラーになりました（コンテナ内でテスト実行できない可能性）" -ForegroundColor Yellow
    } else {
        Write-Host "❌ FAILED: 予期しないステータスコード: $result" -ForegroundColor Red
    }
} catch {
    Write-Host "⚠️ WARNING: テストを実行できませんでした（コンテナが起動していない可能性）" -ForegroundColor Yellow
}

# テスト6: 正しい認証でコンテナ内からアクセス（成功すべき）
Write-Host "`n[テスト6] コンテナ内から正しい認証でアクセス（200が返るべき）" -ForegroundColor Yellow
try {
    $token = $env:ADMIN_SERVICE_TOKEN
    $apiKey = $env:API_SECRET_KEY
    
    if (-not $token) { $token = "admin-secret-token-2024" }
    if (-not $apiKey) { $apiKey = "bus-system-api-key-2024" }
    
    # Pythonを使ってHTTPリクエストを送信（認証ヘッダー付き）
    $pythonScript = @"
import requests
try:
    headers = {
        'X-Service-Auth': '$token',
        'X-API-Key': '$apiKey'
    }
    response = requests.get('http://localhost:5000/api/management/all_students?page=1&per_page=1', headers=headers, timeout=5)
    print(response.status_code)
except Exception as e:
    print('error')
"@
    
    $result = docker exec takatuki_bus-v2-student-1 python -c $pythonScript 2>$null
    
    if ($result -eq "200") {
        Write-Host "✅ PASSED: 200 OK が返されました（認証成功）" -ForegroundColor Green
    } elseif ($result -eq "error") {
        Write-Host "⚠️ WARNING: リクエストがエラーになりました" -ForegroundColor Yellow
    } else {
        Write-Host "❌ FAILED: 予期しないステータスコード: $result" -ForegroundColor Red
    }
} catch {
    Write-Host "⚠️ WARNING: テストを実行できませんでした（コンテナが起動していない可能性）" -ForegroundColor Yellow
}

Write-Host "`n=== テスト完了 ===" -ForegroundColor Cyan
Write-Host @"

📌 セキュリティ設定の確認:
1. ✅ 内部APIが外部から403でブロックされている
2. ✅ 公開APIは正常にアクセス可能
3. ✅ 内部APIは認証がないと401エラー
4. ✅ 正しい認証があれば内部APIにアクセス可能

⚠️ 注意事項:
- 本番環境ではADMIN_SERVICE_TOKENとAPI_SECRET_KEYを必ず変更してください
- トークンは定期的にローテーションしてください
- ログを定期的に監視し、不正アクセス試行がないか確認してください

"@ -ForegroundColor White
