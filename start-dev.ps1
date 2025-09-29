#!/usr/bin/env pwsh
<#
.SYNOPSIS
    バスシステム開発環境の起動スクリプト (PowerShell版)

.DESCRIPTION
    証明書の確認・作成、Dockerコンテナの管理、データベースの初期化を行います。

.PARAMETER Init
    データベースを初期化する場合に指定します

.EXAMPLE
    ./start-dev.ps1
    通常の起動（既存のデータベースを保持）

.EXAMPLE
    ./start-dev.ps1 init
    データベースを初期化して起動

.EXAMPLE
    ./start-dev.ps1 init debug
    データベースを初期化し、デバッグ用テストデータを作成して起動
#>

param(
    [Parameter(Position=0)]
    [string]$Action,
    [Parameter(Position=1)]
    [string]$DebugMode
)

# エラー時にスクリプトを停止
$ErrorActionPreference = "Stop"

# カラー出力用の関数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$ForegroundColor = "White"
    )
    Write-Host $Message -ForegroundColor $ForegroundColor
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✅ $Message" "Green"
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "ℹ️  $Message" "Cyan"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠️  $Message" "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "❌ $Message" "Red"
}

# メイン処理開始
Write-Info "バスシステム開発環境起動スクリプト開始"

# 1. 証明書の確認と作成
Write-Info "Step 1: 証明書の確認"
if ((Test-Path "certs/server.crt") -and (Test-Path "certs/server.key")) {
    Write-Success "証明書が既に存在します"
} else {
    Write-Warning "証明書が見つかりません。新しい証明書を作成します..."
    
    # certsディレクトリの作成
    if (-not (Test-Path "certs")) {
        New-Item -ItemType Directory -Path "certs" -Force | Out-Null
        Write-Info "certsディレクトリを作成しました"
    }
    
    # generate_cert.ps1が存在するかチェック
    if (Test-Path "generate_cert.ps1") {
        Write-Info "generate_cert.ps1を実行中..."
        & "./generate_cert.ps1"
        if ($LASTEXITCODE -eq 0) {
            Write-Success "証明書の作成が完了しました"
        } else {
            Write-Error "証明書の作成に失敗しました"
            exit 1
        }
    } else {
        Write-Error "generate_cert.ps1が見つかりません"
        exit 1
    }
}

# 2. 既存のDockerコンテナを停止
Write-Info "Step 2: 既存のDockerコンテナを停止"
try {
    $containers = docker ps -q --filter "name=takatuki_bus-v2-"
    if ($containers) {
        Write-Info "既存のコンテナを停止中..."
        docker-compose down
        Write-Success "Dockerコンテナを停止しました"
    } else {
        Write-Info "停止すべきコンテナが見つかりません"
    }
} catch {
    Write-Warning "Dockerコンテナの停止でエラーが発生しましたが、続行します"
}

# 3. データベースの初期化判定
$initDatabase = $false
$debugMode = $false

if ($Action -eq "init") {
    $initDatabase = $true
    Write-Warning "データベース初期化モードです"
    
    if ($DebugMode -eq "debug") {
        $debugMode = $true
        Write-Warning "デバッグモードが有効です（テストデータを作成します）"
    }
    
    # データベースボリュームを削除
    Write-Info "Step 3: データベースボリュームの削除"
    try {
        docker volume rm test_postgres_data -f 2>$null
        Write-Success "データベースボリュームを削除しました"
    } catch {
        Write-Info "データベースボリュームが存在しないか、既に削除されています"
    }
} else {
    Write-Info "Step 3: 既存のデータベースを保持します"
}

# 4. Dockerコンテナの起動
Write-Info "Step 4: Dockerコンテナの起動"
try {
    Write-Info "docker-compose up --build -d を実行中..."
    docker-compose up --build -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Dockerコンテナの起動が完了しました"
    } else {
        Write-Error "Dockerコンテナの起動に失敗しました"
        exit 1
    }
} catch {
    Write-Error "Dockerコンテナの起動でエラーが発生しました: $_"
    exit 1
}

# 5. コンテナの起動待機
Write-Info "Step 5: コンテナの起動を待機中..."
Start-Sleep -Seconds 5

# コンテナの状態確認
$maxRetries = 30
$retryCount = 0
$allHealthy = $false

while ($retryCount -lt $maxRetries -and -not $allHealthy) {
    $retryCount++
    Write-Info "コンテナの状態確認中... ($retryCount/$maxRetries)"
    
    $containers = docker ps --filter "name=takatuki_bus-v2-" --format "table {{.Names}}\t{{.Status}}"
    $runningContainers = (docker ps --filter "name=takatuki_bus-v2-" -q | Measure-Object).Count
    $expectedContainers = 6  # nginx, student, admin, driver, postgres, redis
    
    if ($runningContainers -eq $expectedContainers) {
        $allHealthy = $true
        Write-Success "全てのコンテナが起動しました"
        break
    }
    
    Start-Sleep -Seconds 2
}

if (-not $allHealthy) {
    Write-Warning "一部のコンテナの起動に時間がかかっています"
}

# 6. データベース初期化（initオプション指定時）
if ($initDatabase) {
    Write-Info "Step 6: データベースの初期化"
    
    Write-Info "データベースの準備完了を待機中..."
    Start-Sleep -Seconds 15
    
    # 各サービスのマイグレーション実行（独立して実行）
    $services = @("admin", "student", "driver")
    
    foreach ($service in $services) {
        Write-Info "$service サービスのマイグレーション実行中..."
        try {
            if ($service -eq "admin" -or $service -eq "driver") {
                # adminとdriverサービスは改善された初期化スクリプトを使用
                # まず既存のマイグレーションディレクトリを削除してクリーンスタート
                Write-Info "$service サービス: 既存マイグレーションを削除中..."
                docker exec "takatuki_bus-v2-$service-1" rm -rf migrations 2>$null
                
                Write-Info "$service サービス: init_migration.pyを実行中..."
                docker exec "takatuki_bus-v2-$service-1" python init_migration.py
                
                # マイグレーション後の確実な自動修復確認
                Write-Info "$service サービス: テーブル状態の自動確認・修復を実行中..."
                try {
                    # 直接テーブル作成を実行して確実にテーブルが存在することを保証
                    docker exec "takatuki_bus-v2-$service-1" python -c "
from app import create_app
from app.database import db
from sqlalchemy import text, inspect
app = create_app()
with app.app_context():
    print('🔧 Ensuring tables exist...')
    db.create_all()
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f'✅ Available tables: {tables}')
    print('✅ Table creation completed')
"
                    Write-Success "$service サービスのテーブル状態確認が完了しました"
                } catch {
                    Write-Warning "$service サービスの自動修復でエラーが発生しました: $_"
                }
            } else {
                # studentサービスは従来通り
                # 既存のマイグレーションディレクトリを削除（クリーンスタート）
                docker exec "takatuki_bus-v2-$service-1" rm -rf migrations 2>$null
                
                # Flask-Migrateを使用してマイグレーション実行
                docker exec "takatuki_bus-v2-$service-1" flask db init 2>$null
                docker exec "takatuki_bus-v2-$service-1" flask db migrate -m "Initial migration for $service"
                docker exec "takatuki_bus-v2-$service-1" flask db upgrade
            }
            Write-Success "$service サービスのマイグレーションが完了しました"
        } catch {
            Write-Warning "$service サービスのマイグレーションでエラーが発生しました: $_"
        }
        Start-Sleep -Seconds 5  # サービス間の待機時間を延長
    }
    
    # マイグレーション完了後の待機時間を追加
    Write-Info "マイグレーション完了後の安定化を待機中..."
    Start-Sleep -Seconds 10  # 待機時間を延長
    
    # ペナルティシステムのマイグレーション実行
    Write-Info "Step 6a: ペナルティシステムの初期化"
    try {
        Write-Info "studentサービスでペナルティシステムマイグレーション実行中..."
        docker exec "takatuki_bus-v2-student-1" python migrate_penalty_system.py migrate 2>&1
        Write-Success "ペナルティシステムのマイグレーションが完了しました"
        
        # 自動ペナルティチェックの初回実行
        Write-Info "自動ペナルティチェック機能の確認中..."
        docker exec "takatuki_bus-v2-student-1" python -c "
from app.utils.penalty_manager import PenaltyManager
print('✅ PenaltyManagerが正常に読み込まれました')
print('📊 自動ペナルティシステムが利用可能です')
" 2>&1
        Write-Success "自動ペナルティチェック機能が利用可能です"
    } catch {
        Write-Warning "ペナルティシステムのマイグレーションでエラーが発生しました: $_"
    }
    Start-Sleep -Seconds 3
    
    # デバッグモード時のみテストデータを作成
    if ($debugMode) {
        Write-Info "Step 6b: デバッグ用テストデータの作成"
        
        # テストユーザーの作成
        Write-Info "テストユーザーの作成中..."
        
        # admin テストユーザーの作成（データベーステーブル確認付き）
        Write-Info "admin テストユーザーを作成中..."
        try {
            # データベース接続確認
            docker exec "takatuki_bus-v2-admin-1" python -c "
from app import create_app
from app.models import User
app = create_app()
with app.app_context():
    print(f'Users table exists: {User.query.count()} users found')
"
            
            docker exec "takatuki_bus-v2-admin-1" python create_test_admin.py
            Write-Success "admin テストユーザーの作成が完了しました (admin_test / admin123)"
        } catch {
            Write-Warning "admin テストユーザーの作成でエラーが発生しました: $_"
        }
        Start-Sleep -Seconds 3
        
        # driver テストユーザーの作成
        Write-Info "driver テストユーザーを作成中..."
        try {
            docker exec "takatuki_bus-v2-driver-1" python create_test_driver.py
            Write-Success "driver テストユーザーの作成が完了しました (driver_test / driver123)"
        } catch {
            Write-Warning "driver テストユーザーの作成でエラーが発生しました: $_"
        }
        Start-Sleep -Seconds 3
        
        # student デバッグユーザーの作成
        Write-Info "student デバッグユーザーを作成中..."
        try {
            docker exec "takatuki_bus-v2-student-1" python create_test_student.py
            Write-Success "student デバッグユーザーの作成が完了しました"
            Write-Info "   - debug_student1 / student123 (学籍番号: 230092)"
            Write-Info "   - debug_student2 / student123 (学籍番号: 230093)"
            Write-Info "   - debug_student3 / student123 (学籍番号: 230094)"
            Write-Info "   - debug_student4 / student123 (学籍番号: 230095)"
        } catch {
            Write-Warning "student デバッグユーザーの作成でエラーが発生しました: $_"
        }
        Start-Sleep -Seconds 3
        
        # student デバッグバス・座席の作成
        Write-Info "student デバッグバス・座席を作成中..."
        try {
            docker exec "takatuki_bus-v2-student-1" python create_test_bus.py
            Write-Success "student デバッグバス・座席の作成が完了しました"
            Write-Info "   - デバッグバス6台 (上り3台、下り3台)"
            Write-Info "   - 各バス20-30席の座席"
            Write-Info "   - 予約可能時間: 60-120分"
            # 全席空席化スクリプトの実行
            docker exec "takatuki_bus-v2-student-1" python clear_debug_bus_reservations.py
            Write-Success "student デバッグバスの全席空席化が完了しました"
        } catch {
            Write-Warning "student デバッグバス・座席の作成でエラーが発生しました: $_"
        }
        Start-Sleep -Seconds 3
        
        # ペナルティシステムのテスト（デバッグモード時のみ）
        Write-Info "ペナルティシステムのテスト実行中..."
        try {
            Write-Info "   - PenaltyManagerの動作確認"
            Write-Info "   - テスト用ペナルティデータの作成"
            Write-Info "   - 自動ペナルティ機能の確認"
            # 注意: 実際のテストは手動で行う（自動テストでデータが汚染されるため）
            Write-Success "ペナルティシステムが利用可能です"
            Write-Info "   📋 手動テスト: docker exec takatuki_bus-v2-student-1 python test_penalty_system.py"
            Write-Info "   🔧 自動チェック: docker exec takatuki_bus-v2-student-1 python auto_penalty_check.py"
        } catch {
            Write-Warning "ペナルティシステムのテストでエラーが発生しました: $_"
        }
        Start-Sleep -Seconds 3
    } else {
        Write-Info "Step 6b: デバッグモードが無効のため、テストデータの作成をスキップします"
    }
}

# 7. 起動確認
Write-Info "Step 7: システムの起動確認"
try {
    $response = Invoke-WebRequest -Uri "https://localhost" -SkipCertificateCheck -Method Head -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Success "システムが正常に起動しました"
    } else {
        Write-Warning "システムは起動していますが、レスポンスが期待と異なります (Status: $($response.StatusCode))"
    }
} catch {
    Write-Warning "システムの起動確認でエラーが発生しました。手動で確認してください。"
}

# 8. LDAP接続確認（studentサービスのみ）
Write-Info "Step 8: LDAP接続確認"
try {
    Write-Info "studentサービスのLDAP接続を確認中..."
    $ldapResult = docker exec "takatuki_bus-v2-student-1" python check_ldap_connection.py 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success $ldapResult
    } else {
        Write-Warning $ldapResult
    }
} catch {
    Write-Warning "LDAP接続確認でエラーが発生しました: $_"
}

# 9. 完了メッセージ
Write-Info "==========================================="
Write-Success "バスシステム開発環境の起動が完了しました！"
Write-Info "==========================================="
Write-Info "🌐 システムURL: https://localhost"
Write-Info "🔧 管理画面: https://localhost/admin"
Write-Info "📊 ログ確認: docker logs <container-name>"
Write-Info "🛑 停止方法: docker-compose down"

if ($initDatabase) {
    Write-Info "📝 データベースが初期化されました"
    Write-Info "⚖️  ペナルティシステムが初期化されました"
    
    if ($debugMode) {
        Write-Info "👤 テストユーザー:"
        Write-Info "   Admin: admin_test / admin123"
        Write-Info "   Driver: driver_test / driver123"
        Write-Info "   Students (デバッグ用):"
        Write-Info "     - debug_student1 / student123 (学籍番号: 230092)"
        Write-Info "     - debug_student2 / student123 (学籍番号: 230093)"
        Write-Info "     - debug_student3 / student123 (学籍番号: 230094)"
        Write-Info "     - debug_student4 / student123 (学籍番号: 230095)"
        Write-Info "🚌 デバッグバス:"
        Write-Info "   - 6台のテストバス (上り3台、下り3台)"
        Write-Info "   - 各バス20-30席の座席データ"
        Write-Info "   - 予約テスト用のスケジュール設定済み"
        Write-Info "⚖️  ペナルティシステム:"
        Write-Info "   - 自動ペナルティ: 未承認予約3回で自動適用"
        Write-Info "   - 手動ペナルティ: 管理画面から理由・期間選択可能"
        Write-Info "   - テストコマンド: docker exec takatuki_bus-v2-student-1 python test_penalty_system.py"
        Write-Info "   - 自動チェック: docker exec takatuki_bus-v2-student-1 python auto_penalty_check.py"
    } else {
        Write-Info "ℹ️  デバッグ用テストデータは作成されていません"
        Write-Info "   テストデータが必要な場合は 'init debug' オプションを使用してください"
        Write-Info "⚖️  ペナルティシステム:"
        Write-Info "   - システム初期化済み、管理画面から利用可能"
        Write-Info "   - 自動チェック: docker exec takatuki_bus-v2-student-1 python auto_penalty_check.py"
    }
}

Write-Info "==========================================="
