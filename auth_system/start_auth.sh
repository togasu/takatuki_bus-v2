#!/bin/bash
# マイコン向け高速起動スクリプト

# 環境変数の設定
export ID=${ID:-1}
export API_URL=${API_URL:-http://shuttlebus.kutc.kansai-u.ac.jp:49155}
export PYTHONOPTIMIZE=2  # 最適化モード
export PYTHONDONTWRITEBYTECODE=1  # .pycファイル作成を無効化

# データベースの事前作成（起動時間短縮）
if [ ! -f instance/yoyaku_seki.db ] || [ ! -f instance/users.db ]; then
    echo "Initializing databases..."
    python3 -c "
from auth import app, db
with app.app_context():
    db.create_all()
print('Databases initialized')
"
fi

# アプリケーション起動
echo "Starting auth system (Bus ID: $ID)..."
python3 -O auth.py
