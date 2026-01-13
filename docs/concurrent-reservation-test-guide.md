# 並行予約負荷テスト ユーザーガイド

## 📖 概要

このガイドでは、バス予約システムの並行処理性能をテストするためのツール群の使い方を説明します。

### ツール一覧

1. **concurrent_reservation_test.py** - 並行予約負荷テスト
2. **create_bulk_test_users.py** - 大量テストユーザー作成
3. **clean_duplicate_reservations.py** - 重複予約クリーンアップ
4. **add_unique_constraint_reservation.py** - データベースマイグレーション

---

## 🚀 クイックスタート

### 1. ファイルの準備とDockerへのコピー

```bash
# プロジェクトのルートディレクトリに移動
cd C:\Users\okuno\Documents\takatuki_bus-v2

# Dockerコンテナが起動していることを確認
docker ps | grep student

# テストスクリプトをDockerコンテナにコピー
docker cp .\student\concurrent_reservation_test.py takatuki_bus-v2-student-1:/app/concurrent_reservation_test.py
docker cp .\student\create_bulk_test_users.py takatuki_bus-v2-student-1:/app/create_bulk_test_users.py
docker cp .\student\clean_duplicate_reservations.py takatuki_bus-v2-student-1:/app/clean_duplicate_reservations.py
docker cp .\student\add_unique_constraint_reservation.py takatuki_bus-v2-student-1:/app/add_unique_constraint_reservation.py
```

### 2. テスト環境の準備

```bash
# studentコンテナに入る
docker exec -it takatuki_bus-v2-student-1 bash

# または、コンテナに入らずに直接実行することも可能
# docker exec -it takatuki_bus-v2-student-1 python <スクリプト名>
```

### 3. テストユーザーの作成

```bash
# コンテナ内で実行
python create_bulk_test_users.py 500

# または、ホストから直接実行
docker exec -it takatuki_bus-v2-student-1 python create_bulk_test_users.py 500
```

### 4. 負荷テストの実行

```bash
# コンテナ内で実行
python concurrent_reservation_test.py 500 50 random_seats

# または、ホストから直接実行
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 random_seats

# 最悪ケース：全員が同じ座席を予約
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 same_seat
```

---

## 📚 詳細な使い方

## 1. create_bulk_test_users.py

### 概要
並行テスト用の大量のテストユーザーを作成します。

### 基本構文
```bash
python create_bulk_test_users.py [ユーザー数]
```

### パラメータ
| パラメータ | 説明 | デフォルト | 必須 |
|-----------|------|-----------|------|
| ユーザー数 | 作成するユーザーの数 | 500 | いいえ |

### 使用例

#### 500人のユーザーを作成
```bash
python create_bulk_test_users.py 500
```

#### 1000人のユーザーを作成
```bash
python create_bulk_test_users.py 1000
```

#### デフォルト（500人）で作成
```bash
python create_bulk_test_users.py
```

### 出力例
```
🚀 500人のテストユーザーを作成します...
📊 既存のテストユーザー: 0人
   ✅ 100人作成完了...
   ✅ 200人作成完了...
   ✅ 300人作成完了...
   ✅ 400人作成完了...
   ✅ 500人作成完了...

============================================================
🎉 テストユーザー作成完了！
============================================================
新規作成: 500人
スキップ: 0人 (既存)
総数: 500人
============================================================

📝 学籍番号範囲: 230090000 ~ 230090499
IDM_UNIV範囲: TEST_UNIV_000000 ~ TEST_UNIV_000499
IDM_BUS範囲: TEST_BUS_000000 ~ TEST_BUS_000499
```

### 注意事項
- 学籍番号は `230090000` から始まります
- 既存のユーザーは自動的にスキップされます
- IDM_UNIV と IDM_BUS は自動生成されます
- 100人ごとにデータベースにコミットされます

---

## 2. concurrent_reservation_test.py

### 概要
複数のユーザーがほぼ同時に予約を試みた際のシステムの動作を検証します。

### 基本構文
```bash
python concurrent_reservation_test.py [ユーザー数] [スレッド数] [モード]
```

### パラメータ
| パラメータ | 説明 | デフォルト | 必須 |
|-----------|------|-----------|------|
| ユーザー数 | シミュレートするユーザー数 | 500 | いいえ |
| スレッド数 | 並行実行する最大スレッド数 | 50 | いいえ |
| モード | テストモード（下記参照） | random_seats | いいえ |

### テストモード

#### same_seat（最悪ケース）
全員が同じ座席（座席1）を予約しようとします。
- **用途**: データベースロックの限界テスト
- **期待結果**: 1件のみ成功、他は全て失敗

```bash
python concurrent_reservation_test.py 500 50 same_seat
```

#### different_seats（理想ケース）
各ユーザーが異なる座席を予約します。
- **用途**: 理想的な状況でのパフォーマンステスト
- **期待結果**: 座席数まで成功（例：27席なら27件成功）

```bash
python concurrent_reservation_test.py 500 50 different_seats
```

#### random_seats（現実的ケース）
各ユーザーがランダムに座席を選択します。
- **用途**: 実際の利用に近い状況でのテスト
- **期待結果**: 一部成功、重複による失敗あり

```bash
python concurrent_reservation_test.py 500 50 random_seats
```

### 使用例

#### 基本的なテスト（500人、50スレッド、ランダム）
```bash
python concurrent_reservation_test.py
```

#### 少人数でのテスト（100人、10スレッド）
```bash
python concurrent_reservation_test.py 100 10 random_seats
```

#### 大規模負荷テスト（1000人、100スレッド）
```bash
python concurrent_reservation_test.py 1000 100 random_seats
```

#### 最悪ケースのテスト
```bash
python concurrent_reservation_test.py 500 50 same_seat
```

### 出力の見方

#### ヘッダー情報
```
[2025-12-27 14:24:34.711] =====================================
[2025-12-27 14:24:34.711] 🚌 並行予約負荷テスト開始
[2025-12-27 14:24:34.711]    ユーザー数: 500
[2025-12-27 14:24:34.711]    並行スレッド数: 50
[2025-12-27 14:24:34.711]    テストモード: same_seat
```

#### テスト結果
```
📊 テスト結果
総実行時間: 0.63秒
平均処理時間: 0.054秒/予約
スループット: 799.40予約/秒

✅ 成功: 1件 (0.2%)
❌ 失敗: 499件 (99.8%)

エラー内訳:
  🔒 ロックエラー: 0件
  🔄 重複エラー: 499件
  ⚠️  その他のエラー: 0件
```

#### 最終確認
```
📋 最終的な予約数: 1件
✅ 重複予約なし: データベース整合性OK
```

### 判定基準

#### 正常な結果
- ✅ **重複予約なし**: 最も重要
- ✅ **ロックエラー0件**: ロック機構が正常に動作
- ✅ **最終予約数が妥当**: 同じ座席に1件のみ

#### 異常な結果
- 🚨 **重複予約あり**: データベース整合性に問題
- ⚠️ **ロックエラー多数**: デッドロックやタイムアウト
- ⚠️ **予約数が異常**: 同じ座席に複数の予約

---

## 3. clean_duplicate_reservations.py

### 概要
既存の重複予約を検出・削除します。一意制約を追加する前に必須です。

### 基本構文
```bash
python clean_duplicate_reservations.py [オプション]
```

### オプション
| オプション | 説明 |
|-----------|------|
| なし | ドライラン（削除しない） |
| --show | 重複データの詳細を表示 |
| --execute | 実際に削除を実行 |

### 使用例

#### 重複データの確認（詳細表示）
```bash
python clean_duplicate_reservations.py --show
```

出力例：
```
⚠️  1件の重複が検出されました

📋 バスID: 1, 座席: 1 (9件の予約)
   削除対象: 8件
   ✅ 保持 - ID: 77, ユーザー: 230093, 予約時刻: 2025-12-27 14:18:52
   ❌ 削除予定 - ID: 76, ユーザー: 230090000, 予約時刻: 2025-12-27 14:18:52
   ❌ 削除予定 - ID: 75, ユーザー: 230090004, 予約時刻: 2025-12-27 14:18:52
   ...

📊 削除予定合計: 8件
```

#### ドライラン（実際には削除しない）
```bash
python clean_duplicate_reservations.py
```

#### 実際に削除を実行
```bash
python clean_duplicate_reservations.py --execute
```

### 削除ルール
- **最新の予約を保持**: IDが最大のものを残す
- **古い予約を削除**: それ以外は全て削除
- **承認状態は無関係**: 承認済みでも削除される可能性あり

### 注意事項
⚠️ **必ず--showまたはドライランで確認してから--executeを実行してください**

---

## 4. add_unique_constraint_reservation.py

### 概要
Reservationテーブルに一意制約を追加して、重複予約を防止します。

### 基本構文
```bash
python add_unique_constraint_reservation.py [オプション]
```

### オプション
| オプション | 説明 |
|-----------|------|
| なし | マイグレーションを実行 |
| --check | 制約の状態を確認のみ |

### 使用例

#### 制約の状態を確認
```bash
python add_unique_constraint_reservation.py --check
```

出力例：
```
📊 Reservationテーブルの制約情報

現在の制約:
  🔑 主キー Reservation_pkey (PRIMARY KEY)
  🔗 外部キー Reservation_bus_id_fkey (FOREIGN KEY)
  🎯 一意制約 uq_bus_seat (UNIQUE)
```

#### マイグレーションを実行
```bash
python add_unique_constraint_reservation.py
```

出力例：
```
🔧 Reservationテーブルに一意制約を追加します

📊 既存の重複データを確認中...
✅ 重複データなし

🔨 一意制約を追加中...
✅ 一意制約 'uq_bus_seat' を追加しました

✅ マイグレーション成功！

📝 追加された制約:
  - テーブル: Reservation
  - 制約名: uq_bus_seat
  - カラム: (bus_id, seat_number)
  - 効果: 同じバスの同じ座席に複数の予約を防止
```

### 前提条件
⚠️ **重複データが存在する場合、マイグレーションは失敗します**

重複データがある場合の対処：
```bash
# 1. 重複データを確認
python clean_duplicate_reservations.py --show

# 2. 重複データを削除
python clean_duplicate_reservations.py --execute

# 3. マイグレーションを実行
python add_unique_constraint_reservation.py
```

---

## 🔄 完全なワークフロー

### 初回セットアップ

#### Step 1: ファイルをDockerにコピー

```powershell
# PowerShellの場合（Windows）
cd C:\Users\okuno\Documents\takatuki_bus-v2

# 全てのテストスクリプトをコピー
docker cp .\student\concurrent_reservation_test.py takatuki_bus-v2-student-1:/app/concurrent_reservation_test.py
docker cp .\student\create_bulk_test_users.py takatuki_bus-v2-student-1:/app/create_bulk_test_users.py
docker cp .\student\clean_duplicate_reservations.py takatuki_bus-v2-student-1:/app/clean_duplicate_reservations.py
docker cp .\student\add_unique_constraint_reservation.py takatuki_bus-v2-student-1:/app/add_unique_constraint_reservation.py

# コピー成功を確認
docker exec -it takatuki_bus-v2-student-1 ls -la /app/*.py
```

```bash
# Bashの場合（Linux/Mac）
cd /path/to/takatuki_bus-v2

# 全てのテストスクリプトをコピー
docker cp ./student/concurrent_reservation_test.py takatuki_bus-v2-student-1:/app/concurrent_reservation_test.py
docker cp ./student/create_bulk_test_users.py takatuki_bus-v2-student-1:/app/create_bulk_test_users.py
docker cp ./student/clean_duplicate_reservations.py takatuki_bus-v2-student-1:/app/clean_duplicate_reservations.py
docker cp ./student/add_unique_constraint_reservation.py takatuki_bus-v2-student-1:/app/add_unique_constraint_reservation.py
```

#### Step 2: Dockerコンテナに入る（オプション）

```bash
# コンテナ内で作業する場合
docker exec -it takatuki_bus-v2-student-1 bash

# 以降のコマンドはコンテナ内で実行
```

**または、ホストから直接実行する場合は以下のように実行：**

```bash
docker exec -it takatuki_bus-v2-student-1 python <スクリプト名>
```

#### Step 3: テストユーザーを作成

```bash
# コンテナ内の場合
python create_bulk_test_users.py 500

# ホストから実行する場合
docker exec -it takatuki_bus-v2-student-1 python create_bulk_test_users.py 500
```

#### Step 4: 既存の重複データを確認

```bash
# コンテナ内の場合
python clean_duplicate_reservations.py --show

# ホストから実行する場合
docker exec -it takatuki_bus-v2-student-1 python clean_duplicate_reservations.py --show
```

#### Step 5: 重複データがあれば削除

```bash
# コンテナ内の場合
python clean_duplicate_reservations.py --execute

# ホストから実行する場合
docker exec -it takatuki_bus-v2-student-1 python clean_duplicate_reservations.py --execute
```

#### Step 6: 一意制約を追加

```bash
# コンテナ内の場合
python add_unique_constraint_reservation.py

# ホストから実行する場合
docker exec -it takatuki_bus-v2-student-1 python add_unique_constraint_reservation.py
```

#### Step 7: 制約が追加されたことを確認

```bash
# コンテナ内の場合
python add_unique_constraint_reservation.py --check

# ホストから実行する場合
docker exec -it takatuki_bus-v2-student-1 python add_unique_constraint_reservation.py --check
```

### 負荷テストの実行

```bash
# ホストから直接実行（推奨）

# 1. 現実的なケースでテスト
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 random_seats

# 2. 最悪ケースでテスト
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 same_seat

# 3. 理想ケースでテスト
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 different_seats

# 4. 大規模テスト（オプション）
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 1000 100 random_seats
```

```bash
# コンテナ内で実行する場合

# コンテナに入る
docker exec -it takatuki_bus-v2-student-1 bash

# 1. 現実的なケースでテスト
python concurrent_reservation_test.py 500 50 random_seats

# 2. 最悪ケースでテスト
python concurrent_reservation_test.py 500 50 same_seat

# 3. 理想ケースでテスト
python concurrent_reservation_test.py 500 50 different_seats

# 4. 大規模テスト（オプション）
python concurrent_reservation_test.py 1000 100 random_seats
```

### ファイル更新時の手順

スクリプトを修正した場合は、再度Dockerにコピーする必要があります：

```powershell
# PowerShellの場合
cd C:\Users\okuno\Documents\takatuki_bus-v2

# 修正したファイルをコピー
docker cp .\student\concurrent_reservation_test.py takatuki_bus-v2-student-1:/app/concurrent_reservation_test.py

# すぐに実行
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 random_seats
```

```bash
# Bashの場合
cd /path/to/takatuki_bus-v2

# 修正したファイルをコピー
docker cp ./student/concurrent_reservation_test.py takatuki_bus-v2-student-1:/app/concurrent_reservation_test.py

# すぐに実行
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 random_seats
```

### 定期的なメンテナンス

```bash
# ホストから直接実行

# 重複データの監視
docker exec -it takatuki_bus-v2-student-1 python clean_duplicate_reservations.py --show

# 制約の確認
docker exec -it takatuki_bus-v2-student-1 python add_unique_constraint_reservation.py --check
```

---

## 🐳 Dockerコマンドリファレンス

### よく使うDockerコマンド

#### コンテナの状態確認
```bash
# 起動中のコンテナを確認
docker ps

# studentコンテナのみ確認
docker ps | grep student

# コンテナの詳細情報
docker inspect takatuki_bus-v2-student-1
```

#### ファイル操作

##### ホスト → Docker へのコピー
```powershell
# PowerShell（Windows）
docker cp .\student\<ファイル名> takatuki_bus-v2-student-1:/app/<ファイル名>

# 例：concurrent_reservation_test.pyをコピー
docker cp .\student\concurrent_reservation_test.py takatuki_bus-v2-student-1:/app/concurrent_reservation_test.py
```

```bash
# Bash（Linux/Mac）
docker cp ./student/<ファイル名> takatuki_bus-v2-student-1:/app/<ファイル名>

# 例：concurrent_reservation_test.pyをコピー
docker cp ./student/concurrent_reservation_test.py takatuki_bus-v2-student-1:/app/concurrent_reservation_test.py
```

##### Docker → ホスト へのコピー（ログやレポートの取得）
```bash
# テスト結果ログをホストにコピー
docker cp takatuki_bus-v2-student-1:/app/test_results.log ./test_results.log

# バックアップファイルをホストにコピー
docker cp takatuki_bus-v2-student-1:/app/backup.sql ./backup.sql
```

##### コンテナ内のファイル確認
```bash
# ファイル一覧表示
docker exec -it takatuki_bus-v2-student-1 ls -la /app/

# 特定のファイルを検索
docker exec -it takatuki_bus-v2-student-1 find /app -name "*.py"

# ファイルの内容を確認
docker exec -it takatuki_bus-v2-student-1 cat /app/concurrent_reservation_test.py
```

#### コマンド実行

##### インタラクティブモード（コンテナに入る）
```bash
# bashで入る
docker exec -it takatuki_bus-v2-student-1 bash

# shで入る（bashが無い場合）
docker exec -it takatuki_bus-v2-student-1 sh

# 抜けるとき
exit
```

##### 直接実行モード（推奨）
```bash
# Pythonスクリプトを実行
docker exec -it takatuki_bus-v2-student-1 python <スクリプト名>

# シェルコマンドを実行
docker exec -it takatuki_bus-v2-student-1 ls -la /app

# 複数のコマンドを実行
docker exec -it takatuki_bus-v2-student-1 bash -c "cd /app && python test.py"
```

#### ログ確認
```bash
# コンテナのログを表示
docker logs takatuki_bus-v2-student-1

# 最新の50行のみ表示
docker logs takatuki_bus-v2-student-1 --tail 50

# リアルタイムでログを表示
docker logs -f takatuki_bus-v2-student-1
```

#### コンテナの再起動
```bash
# コンテナを再起動
docker restart takatuki_bus-v2-student-1

# 全てのコンテナを再起動
docker-compose restart

# 特定のサービスのみ再起動
docker-compose restart student
```

### 一括ファイルコピースクリプト

#### PowerShell版
```powershell
# copy-test-scripts.ps1
$containerName = "takatuki_bus-v2-student-1"
$files = @(
    "concurrent_reservation_test.py",
    "create_bulk_test_users.py",
    "clean_duplicate_reservations.py",
    "add_unique_constraint_reservation.py"
)

Write-Host "📦 テストスクリプトをDockerにコピー中..." -ForegroundColor Cyan

foreach ($file in $files) {
    Write-Host "  - $file をコピー..." -ForegroundColor Gray
    docker cp ".\student\$file" "${containerName}:/app/$file"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✅ 成功" -ForegroundColor Green
    } else {
        Write-Host "    ❌ 失敗" -ForegroundColor Red
    }
}

Write-Host "`n✨ コピー完了！" -ForegroundColor Green
```

実行方法：
```powershell
# スクリプトを作成して実行
.\copy-test-scripts.ps1

# または、直接実行
docker cp .\student\concurrent_reservation_test.py takatuki_bus-v2-student-1:/app/concurrent_reservation_test.py; `
docker cp .\student\create_bulk_test_users.py takatuki_bus-v2-student-1:/app/create_bulk_test_users.py; `
docker cp .\student\clean_duplicate_reservations.py takatuki_bus-v2-student-1:/app/clean_duplicate_reservations.py; `
docker cp .\student\add_unique_constraint_reservation.py takatuki_bus-v2-student-1:/app/add_unique_constraint_reservation.py
```

#### Bash版
```bash
#!/bin/bash
# copy-test-scripts.sh

container_name="takatuki_bus-v2-student-1"
files=(
    "concurrent_reservation_test.py"
    "create_bulk_test_users.py"
    "clean_duplicate_reservations.py"
    "add_unique_constraint_reservation.py"
)

echo "📦 テストスクリプトをDockerにコピー中..."

for file in "${files[@]}"; do
    echo "  - $file をコピー..."
    if docker cp "./student/$file" "$container_name:/app/$file"; then
        echo "    ✅ 成功"
    else
        echo "    ❌ 失敗"
    fi
done

echo -e "\n✨ コピー完了！"
```

実行方法：
```bash
# スクリプトに実行権限を付与
chmod +x copy-test-scripts.sh

# 実行
./copy-test-scripts.sh
```

---

## 📊 パフォーマンス指標

### 正常な結果の目安

| 項目 | 目標値 |
|------|--------|
| スループット | 500-1000予約/秒 |
| 平均処理時間 | 0.03-0.06秒/予約 |
| ロックエラー | 0件 |
| 重複予約 | 0件 |
| データベース整合性 | OK |

### 異常値の目安

| 項目 | 警告レベル | 対処 |
|------|-----------|------|
| 重複予約 | 1件以上 | 🚨 即座に調査・修正が必要 |
| ロックエラー | 10件以上 | ⚠️ トランザクション分離レベルの見直し |
| スループット | 200予約/秒未満 | ⚠️ データベースやアプリケーションの最適化 |
| 平均処理時間 | 0.1秒以上 | ⚠️ ボトルネックの特定と改善 |

---

## 🐛 トラブルシューティング

### エラー: "ファイルが見つかりません"

**原因**: Dockerにファイルがコピーされていない

**解決方法**:
```bash
# ファイルをコピー
docker cp .\student\concurrent_reservation_test.py takatuki_bus-v2-student-1:/app/concurrent_reservation_test.py

# コピーされたか確認
docker exec -it takatuki_bus-v2-student-1 ls -la /app/*.py
```

### エラー: "コンテナが見つかりません"

**原因**: Dockerコンテナが起動していない

**解決方法**:
```bash
# コンテナの状態を確認
docker ps -a | grep student

# コンテナが停止している場合は起動
docker start takatuki_bus-v2-student-1

# または、docker-composeで起動
docker-compose up -d student
```

### エラー: "利用可能なユーザーが見つかりません"

**原因**: テストユーザーが作成されていない

**解決方法**:
```bash
# テストユーザーを作成
docker exec -it takatuki_bus-v2-student-1 python create_bulk_test_users.py 500
```

### エラー: "利用可能なバスが見つかりません"

**原因**: status=0のバスがデータベースに存在しない

**解決方法**:
```bash
# バスを作成するスクリプトを実行
docker exec -it takatuki_bus-v2-student-1 python create_test_bus.py
```

### エラー: "重複データが存在します"

**原因**: マイグレーション実行前に重複データが存在

**解決方法**:
```bash
# 重複データを削除
docker exec -it takatuki_bus-v2-student-1 python clean_duplicate_reservations.py --execute

# マイグレーションを再実行
docker exec -it takatuki_bus-v2-student-1 python add_unique_constraint_reservation.py
```

### エラー: "UniqueViolation"

**原因**: 一意制約に違反する予約を試みた（これは正常な動作）

**確認方法**:
- テスト結果で「重複エラー」としてカウントされる
- 「重複予約なし」と表示されれば問題なし

### エラー: "Permission denied"

**原因**: Dockerコンテナ内の権限の問題

**解決方法**:
```bash
# rootユーザーで実行
docker exec -it -u root takatuki_bus-v2-student-1 bash

# ファイルの権限を確認
docker exec -it takatuki_bus-v2-student-1 ls -la /app/
```

### Dockerコピーが失敗する

**原因**: ファイルパスが間違っている、またはコンテナ名が間違っている

**解決方法**:
```bash
# コンテナ名を確認
docker ps

# 正しいコンテナ名でコピー
docker cp .\student\concurrent_reservation_test.py <正しいコンテナ名>:/app/concurrent_reservation_test.py

# パスの確認（PowerShell）
Get-ChildItem .\student\*.py

# パスの確認（Bash）
ls -la ./student/*.py
```

### パフォーマンスが悪い

**確認事項**:
1. データベース接続数を確認
2. PostgreSQLのログを確認
3. スレッド数を調整（多すぎる場合は減らす）

```bash
# スレッド数を減らしてテスト
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 25 random_seats

# より少ないユーザー数でテスト
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 100 10 random_seats

# Dockerのリソース使用状況を確認
docker stats takatuki_bus-v2-student-1
```

---

## 💡 ベストプラクティス

### 1. 段階的なテスト

```bash
# Step 1: ファイルをコピー
docker cp .\student\concurrent_reservation_test.py takatuki_bus-v2-student-1:/app/concurrent_reservation_test.py

# Step 2: 少人数でテスト
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 10 5 random_seats

# Step 3: 中規模でテスト
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 100 10 random_seats

# Step 4: 大規模でテスト
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 random_seats

# Step 5: 最悪ケースでテスト
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 same_seat
```

### 2. 定期的な監視

週次実行スクリプト（PowerShell版）:
```powershell
# weekly-test.ps1
$date = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logFile = "test_results_$date.log"

Write-Host "=== 週次並行予約テスト ===" -ForegroundColor Cyan
Write-Host "実行日時: $(Get-Date)" -ForegroundColor Gray

# ファイルをコピー
Write-Host "`n📦 スクリプトをコピー中..." -ForegroundColor Yellow
docker cp .\student\concurrent_reservation_test.py takatuki_bus-v2-student-1:/app/concurrent_reservation_test.py
docker cp .\student\clean_duplicate_reservations.py takatuki_bus-v2-student-1:/app/clean_duplicate_reservations.py
docker cp .\student\add_unique_constraint_reservation.py takatuki_bus-v2-student-1:/app/add_unique_constraint_reservation.py

# 重複データの確認
Write-Host "`n🔍 重複データを確認中..." -ForegroundColor Yellow
docker exec -it takatuki_bus-v2-student-1 python clean_duplicate_reservations.py --show | Tee-Object -FilePath $logFile -Append

# 制約の確認
Write-Host "`n📊 制約を確認中..." -ForegroundColor Yellow
docker exec -it takatuki_bus-v2-student-1 python add_unique_constraint_reservation.py --check | Tee-Object -FilePath $logFile -Append

# 負荷テスト
Write-Host "`n🚀 負荷テスト実行中..." -ForegroundColor Yellow
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 random_seats | Tee-Object -FilePath $logFile -Append

Write-Host "`n✅ テスト完了！" -ForegroundColor Green
Write-Host "ログファイル: $logFile" -ForegroundColor Cyan
```

Bash版:
```bash
#!/bin/bash
# weekly-test.sh

date=$(date +%Y-%m-%d_%H-%M-%S)
log_file="test_results_$date.log"

echo "=== 週次並行予約テスト ==="
echo "実行日時: $(date)"

# ファイルをコピー
echo -e "\n📦 スクリプトをコピー中..."
docker cp ./student/concurrent_reservation_test.py takatuki_bus-v2-student-1:/app/concurrent_reservation_test.py
docker cp ./student/clean_duplicate_reservations.py takatuki_bus-v2-student-1:/app/clean_duplicate_reservations.py
docker cp ./student/add_unique_constraint_reservation.py takatuki_bus-v2-student-1:/app/add_unique_constraint_reservation.py

# 重複データの確認
echo -e "\n🔍 重複データを確認中..."
docker exec -it takatuki_bus-v2-student-1 python clean_duplicate_reservations.py --show | tee -a "$log_file"

# 制約の確認
echo -e "\n📊 制約を確認中..."
docker exec -it takatuki_bus-v2-student-1 python add_unique_constraint_reservation.py --check | tee -a "$log_file"

# 負荷テスト
echo -e "\n🚀 負荷テスト実行中..."
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 random_seats | tee -a "$log_file"

echo -e "\n✅ テスト完了！"
echo "ログファイル: $log_file"
```

### 3. 本番環境への適用前

```bash
# 1. バックアップを取得
docker exec -it takatuki_bus-v2-student-1 pg_dump -h localhost -U postgres -d bus_reservation > backup_$(date +%Y%m%d).sql

# 2. ファイルをコピー
docker cp .\student\concurrent_reservation_test.py takatuki_bus-v2-student-1:/app/concurrent_reservation_test.py

# 3. テスト環境で確認
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 random_seats

# 4. 問題がなければマイグレーション
docker exec -it takatuki_bus-v2-student-1 python add_unique_constraint_reservation.py

# 5. 再度テスト
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 same_seat
```

---

## 📝 ログとレポート

### テスト結果の保存

```bash
# 結果をファイルに保存
python concurrent_reservation_test.py 500 50 random_seats > test_results_$(date +%Y%m%d_%H%M%S).log 2>&1

# 複数のテストを連続実行
for mode in same_seat different_seats random_seats; do
    echo "Testing mode: $mode"
    python concurrent_reservation_test.py 500 50 $mode > test_${mode}_$(date +%Y%m%d).log 2>&1
done
```

### 結果の分析

重要な指標：
- **重複予約の有無**: 必ず0件であること
- **スループット**: システムの処理能力
- **エラー率**: 失敗の割合と原因
- **実行時間**: 全体の処理時間

---

## 🔗 関連ドキュメント

- [並行予約負荷テスト結果レポート](./concurrent-reservation-test-report.md)
- [実装完了サマリー](../student/CONCURRENT_TEST_SUMMARY.md)

---

## ❓ よくある質問

### Q1: テストユーザーは本番環境と共存できますか？

A: はい、学籍番号が `23009` で始まるユーザーはテスト専用です。本番ユーザーとは区別されます。

### Q2: テスト後にデータをクリーンアップする必要がありますか？

A: テスト予約は自動的にクリアされますが、テストユーザーは残ります。不要な場合は手動で削除してください。

### Q3: 本番環境でこれらのテストを実行できますか？

A: **推奨しません**。本番環境では専用のテスト環境で実行し、結果を確認してから適用してください。

### Q4: スレッド数はいくつが適切ですか？

A: 一般的には50-100が適切です。多すぎるとデータベースに負荷がかかり、少なすぎると並行性の問題を検出できません。

### Q5: テストの実行時間はどのくらいですか？

A: 500人で約0.5-1秒程度です。ユーザー数やスレッド数により変動します。

---

**最終更新**: 2025年12月27日  
**バージョン**: 1.0
