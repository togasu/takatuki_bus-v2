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
#>

param(
    [Parameter(Position=0)]
    [string]$Action
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
    $containers = docker ps -q --filter "name=test-"
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
if ($Action -eq "init") {
    $initDatabase = $true
    Write-Warning "データベース初期化モードです"
    
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
    
    $containers = docker ps --filter "name=test-" --format "table {{.Names}}\t{{.Status}}"
    $runningContainers = (docker ps --filter "name=test-" -q | Measure-Object).Count
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
    Start-Sleep -Seconds 10
    
    # 各サービスのマイグレーション実行
    $services = @("admin", "student", "driver")
    
    foreach ($service in $services) {
        Write-Info "$service サービスのマイグレーション実行中..."
        try {
            docker exec "test-$service-1" python init_migration.py
            Write-Success "$service サービスのマイグレーションが完了しました"
        } catch {
            Write-Warning "$service サービスのマイグレーションでエラーが発生しました: $_"
        }
        Start-Sleep -Seconds 2
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

# 8. 完了メッセージ
Write-Info "==========================================="
Write-Success "バスシステム開発環境の起動が完了しました！"
Write-Info "==========================================="
Write-Info "🌐 システムURL: https://localhost"
Write-Info "🔧 管理画面: https://localhost/admin"
Write-Info "📊 ログ確認: docker logs <container-name>"
Write-Info "🛑 停止方法: docker-compose down"

if ($initDatabase) {
    Write-Info "📝 データベースが初期化されました"
}

Write-Info "==========================================="
