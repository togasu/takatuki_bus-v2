#!/bin/bash
#
# Driver Service Startup Script
# マイグレーションとサービス起動を管理
#

set -e

echo "=== Driver Service Startup ==="
echo "Environment: ${ENVIRONMENT:-development}"
echo "Skip Migration: ${SKIP_MIGRATION:-false}"

# データベース接続待機
echo "Waiting for database connection..."
max_retries=30
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    if python -c "
import os
import psycopg2
try:
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        database=os.getenv('POSTGRES_DB', 'mydb'),
        user=os.getenv('POSTGRES_USER', 'user'),
        password=os.getenv('POSTGRES_PASSWORD', 'pass')
    )
    conn.close()
    print('Database connection successful')
    exit(0)
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
fi
"; then
        echo "Database is ready!"
        break
    else
        echo "Database not ready yet... ($((retry_count + 1))/$max_retries)"
        sleep 2
        retry_count=$((retry_count + 1))
    fi
done

if [ $retry_count -eq $max_retries ]; then
    echo "ERROR: Database connection timeout"
    exit 1
fi

# マイグレーション処理
if [ "${SKIP_MIGRATION}" != "true" ]; then
    echo "Running migration initialization..."
    python init_migration.py
    
    if [ $? -eq 0 ]; then
        echo "Migration initialization successful"
    else
        echo "Migration initialization failed, attempting auto-fix..."
        python auto_fix_tables.py
        
        if [ $? -eq 0 ]; then
            echo "Auto-fix successful"
        else
            echo "Auto-fix failed, but continuing with service startup..."
        fi
    fi
    
    # 最終的なテーブル状態確認
    echo "Verifying table status..."
    python auto_fix_tables.py
    
else
    echo "Skipping migration (SKIP_MIGRATION=true)"
fi

# サービス起動
echo "Starting uwsgi server..."
exec uwsgi --ini uwsgi.ini