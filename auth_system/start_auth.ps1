# マイコン向け高速起動スクリプト (PowerShell)

# 環境変数の設定
$env:ID = if ($env:ID) { $env:ID } else { "1" }
$env:API_URL = if ($env:API_URL) { $env:API_URL } else { "http://shuttlebus.kutc.kansai-u.ac.jp:49155" }
$env:PYTHONOPTIMIZE = "2"  # 最適化モード
$env:PYTHONDONTWRITEBYTECODE = "1"  # .pycファイル作成を無効化

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
