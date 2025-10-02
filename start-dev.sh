#!/bin/bash

# バスシステム開発環境の起動スクリプト (Bash版)
# 使用方法:
#   ./start-dev.sh       : 通常起動（既存データベース保持）
#   ./start-dev.sh init  : データベース初期化して起動

set -e  # エラー時にスクリプトを停止

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 出力関数
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# メイン処理開始
print_info "バスシステム開発環境起動スクリプト開始"

# 引数の確認
INIT_DATABASE=false
if [ "$1" = "init" ]; then
    INIT_DATABASE=true
    print_warning "データベース初期化モードです"
fi

# 1. 証明書の確認と作成
print_info "Step 1: 証明書の確認"
if [ -f "certs/server.crt" ] && [ -f "certs/server.key" ]; then
    print_success "証明書が既に存在します"
else
    print_warning "証明書が見つかりません。新しい証明書を作成します..."
    
    # certsディレクトリの作成
    if [ ! -d "certs" ]; then
        mkdir -p certs
        print_info "certsディレクトリを作成しました"
    fi
    
    # generate_cert.shが存在するかチェック
    if [ -f "generate_cert.sh" ]; then
        print_info "generate_cert.shを実行中..."
        chmod +x generate_cert.sh
        ./generate_cert.sh
        if [ $? -eq 0 ]; then
            print_success "証明書の作成が完了しました"
        else
            print_error "証明書の作成に失敗しました"
            exit 1
        fi
    else
        print_error "generate_cert.shが見つかりません"
        exit 1
    fi
fi

# 2. 既存のDockerコンテナを停止
print_info "Step 2: 既存のDockerコンテナを停止"
if [ "$(docker ps -q --filter 'name=test-')" ]; then
    print_info "既存のコンテナを停止中..."
    docker-compose down
    print_success "Dockerコンテナを停止しました"
else
    print_info "停止すべきコンテナが見つかりません"
fi

# 3. データベースの初期化判定
if [ "$INIT_DATABASE" = true ]; then
    print_info "Step 3: データベースボリュームの削除"
    docker volume rm test_postgres_data -f 2>/dev/null || true
    print_success "データベースボリュームを削除しました（または存在しませんでした）"
else
    print_info "Step 3: 既存のデータベースを保持します"
fi

# 4. Dockerコンテナの起動
print_info "Step 4: Dockerコンテナの起動"
print_info "docker-compose up --build -d を実行中..."
if docker-compose up --build -d; then
    print_success "Dockerコンテナの起動が完了しました"
else
    print_error "Dockerコンテナの起動に失敗しました"
    exit 1
fi

# 5. コンテナの起動待機
print_info "Step 5: コンテナの起動を待機中..."
sleep 5

# コンテナの状態確認
MAX_RETRIES=30
RETRY_COUNT=0
ALL_HEALTHY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$ALL_HEALTHY" = false ]; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    print_info "コンテナの状態確認中... ($RETRY_COUNT/$MAX_RETRIES)"
    
    RUNNING_CONTAINERS=$(docker ps --filter "name=test-" -q | wc -l)
    EXPECTED_CONTAINERS=6  # nginx, student, admin, driver, postgres, redis
    
    if [ "$RUNNING_CONTAINERS" -eq "$EXPECTED_CONTAINERS" ]; then
        ALL_HEALTHY=true
        print_success "全てのコンテナが起動しました"
        break
    fi
    
    sleep 2
done

if [ "$ALL_HEALTHY" = false ]; then
    print_warning "一部のコンテナの起動に時間がかかっています"
fi

# 6. データベース初期化（initオプション指定時）
if [ "$INIT_DATABASE" = true ]; then
    print_info "Step 6: データベースの初期化"
    
    print_info "データベースの準備完了を待機中..."
    sleep 10
    
    # 各サービスのマイグレーション実行
    services=("admin" "student" "driver")
    
    for service in "${services[@]}"; do
        print_info "$service サービスのマイグレーション実行中..."
        if docker exec "test-$service-1" python init_migration.py; then
            print_success "$service サービスのマイグレーションが完了しました"
        else
            print_warning "$service サービスのマイグレーションでエラーが発生しました"
        fi
        sleep 2
    done
fi

# 7. 起動確認
print_info "Step 7: システムの起動確認"
if command -v curl >/dev/null 2>&1; then
    if curl -k -I https://localhost --max-time 10 >/dev/null 2>&1; then
        print_success "システムが正常に起動しました"
    else
        print_warning "システムの起動確認でエラーが発生しました。手動で確認してください。"
    fi
else
    print_warning "curlが見つかりません。手動でhttps://localhostにアクセスして確認してください。"
fi

# 8. 完了メッセージ
echo "==========================================="
print_success "バスシステム開発環境の起動が完了しました！"
echo "==========================================="
print_info "🌐 システムURL: https://localhost"
print_info "🔧 管理画面: https://localhost/admin"
print_info "📊 ログ確認: docker logs <container-name>"
print_info "🛑 停止方法: docker-compose down"

if [ "$INIT_DATABASE" = true ]; then
    print_info "📝 データベースが初期化されました"
fi

echo "==========================================="
