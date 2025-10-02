# ペナルティシステム実装ガイド

## 概要

このドキュメントでは、新しく実装されたペナルティシステムについて説明します。

## 機能一覧

### 1. 自動ペナルティシステム
- **自動適用条件**: approved=0の予約が3つになると自動でペナルティ適用
- **ペナルティ理由**: "未乗車が3回以上"
- **期間**: ペナルティ適用日から2週間後の22:00まで
- **再適用ロジック**: 不乗車ペナルティの場合、解除後に再度カウント開始

### 2. 管理者による手動ペナルティ
- **理由選択**: 
  - 未乗車（無断欠席）
  - 直前キャンセル
  - 複数回の違反
  - 車内での不適切な行為
  - システムの不正利用
  - その他（カスタム入力）
- **解除時間設定**:
  - デフォルト（2週間後の22:00）
  - 即時解除
  - 1日後/3日後/1週間後
  - カスタム日時

### 3. ペナルティ詳細表示
- **管理者画面**: ペナルティ理由、適用日時、解除日時を表示
- **不乗車ペナルティ**: 該当する予約一覧を表示
- **ペナルティ種別**: 自動適用 or 手動適用を区別

## ファイル構成

### 新規作成ファイル
```
student/
├── app/
│   └── utils/
│       └── penalty_manager.py           # ペナルティ管理クラス
├── auto_penalty_check.py               # 自動ペナルティチェックバッチ
├── migrate_penalty_system.py           # データベースマイグレーション
└── test_penalty_system.py              # テストスクリプト
```

### 更新ファイル
```
student/app/models/user.py              # User_Penaltyモデル拡張
student/app/routes/management_api.py    # APIエンドポイント更新
admin/app/api_client.py                 # APIクライアント拡張
admin/app/routes/student_management.py  # 管理画面ルート更新
admin/app/templates/student_management.html # フロントエンド更新
```

## データベーススキーマ

### User_Penalty テーブル（更新）
```sql
CREATE TABLE user_penalty (
    id INTEGER PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL,
    end_time_of_usage_restriction DATETIME NOT NULL,
    reason VARCHAR(200) NOT NULL,
    penalty_type VARCHAR(50) DEFAULT 'manual' NOT NULL,
    applied_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT 1 NOT NULL
);
```

### Penalty_Reservation テーブル（新規）
```sql
CREATE TABLE penalty_reservation (
    id INTEGER PRIMARY KEY,
    penalty_id INTEGER NOT NULL,
    reservation_id INTEGER NOT NULL,
    student_id VARCHAR(20) NOT NULL,
    bus_id INTEGER NOT NULL,
    seat_number INTEGER NOT NULL,
    reserved_time DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (penalty_id) REFERENCES user_penalty (id)
);
```

## API エンドポイント

### Student Service
- `POST /api/management/apply_penalty` - ペナルティ適用
- `POST /api/management/clear_penalty` - ペナルティ解除
- `GET /api/management/penalty_details/<student_id>` - ペナルティ詳細取得
- `POST /api/management/check_auto_penalty/<student_id>` - 自動ペナルティチェック

### Admin Service
- `POST /admin/student_management/apply_penalty` - ペナルティ適用（拡張版）
- `POST /admin/student_management/clear_penalty_with_time` - 時間指定解除
- `GET /admin/student_management/penalty_details/<student_id>` - 詳細取得

## 使用方法

### 1. システムセットアップ

```bash
# マイグレーション実行
cd student
python migrate_penalty_system.py

# テストデータ作成（オプション）
python create_test_student.py
```

### 2. 自動ペナルティチェック

```bash
# 手動実行
python auto_penalty_check.py

# 定期実行（cron設定例）
# 毎時0分に実行
0 * * * * /path/to/python /path/to/auto_penalty_check.py
```

### 3. 管理者操作

1. **学生一覧から対象学生を選択**
2. **ペナルティ付与**:
   - 理由を選択
   - 解除時間を設定
   - 「ペナルティ付与」をクリック
3. **ペナルティ解除**:
   - 解除時間を指定（即時 or 将来日時）
   - 「ペナルティ解除」をクリック

### 4. システムテスト

```bash
cd student
python test_penalty_system.py
```

## 注意事項

### セキュリティ
- ペナルティ操作には適切な権限が必要
- APIアクセスにはサービス認証が必要

### パフォーマンス
- 自動ペナルティチェックは定期実行推奨
- 大量データ処理時はバッチサイズを調整

### データ整合性
- ペナルティ適用前に既存ペナルティをチェック
- トランザクション処理でデータ整合性を保証

## トラブルシューティング

### 1. ペナルティが適用されない
- 学生IDの形式を確認
- 未承認予約数をチェック
- ログファイルでエラー確認

### 2. 管理画面でエラー
- サービス間通信の確認
- APIエンドポイントの動作確認
- ブラウザのコンソールログ確認

### 3. データベースエラー
- マイグレーション実行状況確認
- テーブル構造の整合性確認
- 外部キー制約の確認

## ログファイル

- `penalty_check.log` - 自動ペナルティチェックログ
- `sojo-bus.log` - アプリケーションログ
- ブラウザコンソール - フロントエンドエラーログ

## 今後の拡張予定

1. **メール通知機能** - ペナルティ適用/解除時の通知
2. **統計機能** - ペナルティ統計の可視化
3. **ルール設定** - ペナルティルールのカスタマイズ
4. **履歴管理** - ペナルティ履歴の詳細表示