# ペナルティシステム クイックスタートガイド

## システム起動

基本的なシステム起動は以下のコマンドで行います：

```powershell
# 既存データを保持して起動
./start-dev.ps1

# データベースを初期化して起動
./start-dev.ps1 init

# データベース初期化 + デバッグデータ作成
./start-dev.ps1 init debug
```

## ペナルティシステムの使用方法

### 1. 管理者画面でのペナルティ管理

1. **管理画面にアクセス**: https://localhost/admin
2. **ログイン**: admin_test / admin123 (デバッグモード時)
3. **学生管理**: サイドメニューの「学生管理」をクリック
4. **学生選択**: 対象学生を検索または一覧から選択

#### ペナルティ付与
1. 学生詳細で「ペナルティ付与」ボタンをクリック
2. **理由を選択**:
   - 未乗車（無断欠席）
   - 直前キャンセル  
   - 複数回の違反
   - 車内での不適切な行為
   - システムの不正利用
   - その他（手動入力）

3. **解除時間を設定**:
   - デフォルト（2週間後の22:00）
   - 即時解除
   - 1日後/3日後/1週間後
   - カスタム日時

4. 「ペナルティ付与」をクリック

#### ペナルティ解除
1. 学生詳細で「ペナルティ解除」ボタンをクリック
2. 確認ダイアログで「はい」をクリック

### 2. 自動ペナルティシステム

#### 自動適用条件
- **トリガー**: approved=0の予約が3つになった時
- **理由**: "未乗車が3回以上"
- **期間**: 適用日から2週間後の22:00まで
- **再適用**: 不乗車ペナルティ解除後、再度カウント開始

#### 手動チェック実行
```bash
# コンテナ内で実行
docker exec takatuki_bus-v2-student-1 python auto_penalty_check.py
```

### 3. テストとデバッグ

#### ペナルティシステムのテスト
```bash
# 対話式テストメニュー
docker exec -it takatuki_bus-v2-student-1 python test_penalty_system.py

# 選択肢:
# 1. PenaltyManagerテスト
# 2. 自動ペナルティテスト  
# 3. テストデータクリーンアップ
# 4. 終了
```

#### 個別テスト例
```bash
# 学生のペナルティ状況確認
docker exec takatuki_bus-v2-student-1 python -c "
from app.utils.penalty_manager import PenaltyManager
status = PenaltyManager.get_student_penalty_status('230092')
print(status)
"

# 未承認予約数確認
docker exec takatuki_bus-v2-student-1 python -c "
from app.utils.penalty_manager import PenaltyManager
count = PenaltyManager.get_unapproved_reservations_count('230092')
print(f'未承認予約数: {count}')
"
```

### 4. データベース操作

#### ペナルティデータの確認
```bash
# 現在のペナルティ一覧
docker exec takatuki_bus-v2-student-1 python -c "
from app import create_app
from app.models.user import User_Penalty
from app.database import db

app = create_app()
with app.app_context():
    penalties = User_Penalty.query.all()
    for p in penalties:
        print(f'学籍番号: {p.student_id}, 理由: {p.reason}, 終了日時: {p.end_time_of_usage_restriction}')
"
```

#### テストペナルティの作成
```bash
# マイグレーションスクリプト使用
docker exec takatuki_bus-v2-student-1 python migrate_penalty_system.py test
```

### 5. トラブルシューティング

#### よくある問題と解決方法

**Q: ペナルティが自動適用されない**
```bash
# 学生の未承認予約を確認
docker exec takatuki_bus-v2-student-1 python -c "
from app.models.reservation import Reservation
from app.database import db
from app import create_app

app = create_app()
with app.app_context():
    unapproved = Reservation.query.filter_by(user_id='230092', approved=0).all()
    print(f'未承認予約数: {len(unapproved)}')
    for r in unapproved:
        print(f'予約ID: {r.id}, バス: {r.bus_id}, 座席: {r.seat_number}')
"
```

**Q: 管理画面でエラーが発生**
```bash
# APIエンドポイントの確認
docker logs takatuki_bus-v2-student-1 | tail -20
docker logs takatuki_bus-v2-admin-1 | tail -20
```

**Q: データベースの不整合**
```bash
# ペナルティテーブルの再作成
docker exec takatuki_bus-v2-student-1 python migrate_penalty_system.py migrate
```

### 6. 定期実行の設定

#### crontabでの自動ペナルティチェック
```bash
# crontab -e で編集
# 毎時0分に実行
0 * * * * docker exec takatuki_bus-v2-student-1 python auto_penalty_check.py

# 毎日22:00に実行
0 22 * * * docker exec takatuki_bus-v2-student-1 python auto_penalty_check.py
```

## システム構成

### 関連ファイル
- **バックエンド**: `student/app/utils/penalty_manager.py`
- **API**: `student/app/routes/management_api.py`  
- **フロントエンド**: `admin/app/templates/student_management.html`
- **テスト**: `student/test_penalty_system.py`
- **バッチ**: `student/auto_penalty_check.py`

### データベーステーブル
- **user_penalty**: ペナルティ情報
- **penalty_reservation**: ペナルティ関連予約情報

## 注意事項

1. **本番環境**: 自動ペナルティチェックは定期実行を推奨
2. **データバックアップ**: ペナルティデータは重要な業務データです
3. **権限管理**: ペナルティ操作は管理者権限が必要
4. **ログ監視**: 異常な動作がないか定期的に確認してください