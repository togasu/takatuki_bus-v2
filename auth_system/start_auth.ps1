# マイコン向け高速起動スクリプト (PowerShell)
# 使用方法:
#   本番: .\start_auth.ps1
#   開発: .\start_auth.ps1 -DevMode

param(
    [switch]$DevMode = $false
)

# 環境変数の設定
$env:ID = if ($env:ID) { $env:ID } else { "1" }
$env:DRIVER_API_URL = if ($env:DRIVER_API_URL) { $env:DRIVER_API_URL } else { "http://localhost/driver" }

# 開発モードの設定
if ($DevMode) {
    $env:DEV_MODE = "1"
    Write-Host "===================================" -ForegroundColor Yellow
    Write-Host "  開発モード (NFCリーダー不要)" -ForegroundColor Yellow
    Write-Host "  手動入力: http://localhost:8000/dev/manual-scan" -ForegroundColor Cyan
    Write-Host "===================================" -ForegroundColor Yellow
} else {
    $env:DEV_MODE = "0"
    $env:PYTHONOPTIMIZE = "2"  # 最適化モード
    $env:PYTHONDONTWRITEBYTECODE = "1"  # .pycファイル作成を無効化
}

# データベースの事前作成（起動時間短縮）
if (!(Test-Path "instance/yoyaku_seki.db") -or !(Test-Path "instance/users.db")) {
    Write-Host "Initializing databases..."
    python -c @"
from auth import app, db
with app.app_context():
    db.create_all()
print('Databases initialized')
"@
}

# アプリケーション起動
Write-Host "Starting auth system (Bus ID: $env:ID)..."
python -O auth.py
