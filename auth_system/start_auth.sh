#!/bin/bash
# マイコン向け高速起動スクリプト
# 使用方法:
#   本番: ./start_auth.sh
#   開発: ./start_auth.sh --dev

# 環境変数の設定
export ID=${ID:-1}
export API_URL=${API_URL:-http://shuttlebus.kutc.kansai-u.ac.jp:49155}
export DRIVER_API_URL=${DRIVER_API_URL:-http://localhost}

# 開発モードの判定
if [[ "$1" == "--dev" ]] || [[ "$1" == "-d" ]]; then
    export DEV_MODE=1
    echo "==================================="
    echo "  開発モード (NFCリーダー不要)"
    echo "  手動入力: http://localhost:8000/dev/manual-scan"
    echo "==================================="
else
    export DEV_MODE=0
    export PYTHONOPTIMIZE=2  # 最適化モード
    export PYTHONDONTWRITEBYTECODE=1  # .pycファイル作成を無効化
fi

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
