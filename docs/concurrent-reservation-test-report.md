# 並行予約負荷テスト結果レポート

## 📅 テスト実施日時
- **初回テスト**: 2025/12/27 23:20
- **修正後テスト**: 2025/12/27 23:24
- **ステータス**: ✅ **問題解決済み**

## テスト概要
500人の学生がほぼ同時に予約を試みた際のデータベース整合性テスト

## テスト環境
- ユーザー数: 500人
- 並行スレッド数: 50
- データベース: PostgreSQL

---

## 🔴 初回テスト：重大な問題発見

### 問題1: 重複予約の発生

#### 修正前のテスト結果（ランダム座席モード）
- **成功**: 38件 (7.6%)
- **失敗**: 462件 (92.4%)
- **ロックエラー**: 0件
- **重複エラー**: 462件
- **スループット**: 722.88予約/秒

**重複予約が検出されました:**
- 座席14: 2件の予約
- 座席13: 2件の予約
- 座席20: 2件の予約
- 座席25: 2件の予約
- 座席2: 2件の予約
- 座席19: 2件の予約
- 座席6: 3件の予約
- **座席1: 4件の予約** ⚠️

#### 修正前のテスト結果（最悪ケース：全員が座席1を予約）
- **成功**: 9件 (1.8%)
- **失敗**: 491件 (98.2%)
- **実行時間**: 0.54秒
- **スループット**: 931.76予約/秒

**重複予約が検出されました:**
- **座席1: 9件の予約** 🚨

## 原因分析

### 根本原因
現在の予約作成ロジックには適切なロック機構が実装されていません。

#### 問題のあるコード
```python
# 既存予約のチェック（ロックなし）
existing_reservations = db.session.query(Reservation).filter(
    Reservation.bus_id == bus_id,
    Reservation.seat_number.in_(seat_numbers)
).all()

if existing_reservations:
    return jsonify({'success': False, 'message': '既に予約済み'}), 400

# 予約を作成
reservation = Reservation(...)
db.session.add(reservation)
db.session.commit()
```

#### 競合状態（Race Condition）の発生
1. **時刻 T1**: スレッドAが座席1の予約状況を確認 → 空き
2. **時刻 T2**: スレッドBが座席1の予約状況を確認 → 空き（スレッドAはまだコミットしていない）
3. **時刻 T3**: スレッドAが座席1を予約してコミット
4. **時刻 T4**: スレッドBも座席1を予約してコミット ← **重複予約発生！**

## 📋 修正案

### 修正案1: SELECT FOR UPDATE を使用（推奨）

---

## ✅ 実装した修正内容

### 1. データベース制約の追加（実装済み）

#### Reservationテーブルに一意制約を追加
```python
class Reservation(db.Model):
    __tablename__ = 'Reservation'
    id = db.Column(db.Integer, primary_key=True)
    seat_number = db.Column(db.Integer, nullable=False)
    bus_id = db.Column(db.Integer, db.ForeignKey('bus.id'), nullable=False)
    user_id = db.Column(db.String(50), nullable=False)
    approved = db.Column(db.Integer, nullable=False)
    reserved_time = db.Column(db.DateTime)
    
    # 一意制約: 同じバスの同じ座席に複数の予約を防ぐ
    __table_args__ = (
        db.UniqueConstraint('bus_id', 'seat_number', name='uq_bus_seat'),
    )
```

**実装ファイル**: `student/app/models/reservation.py`

### 2. SELECT FOR UPDATE の実装（実装済み）

#### booking.py の修正
```python
# 席が空いているか確認（排他ロックを使用して最新データを取得）
# with_for_update()を使用して行レベルロックを取得し、並行アクセス時の競合を防止
seat = db.session.query(Reservation).filter_by(
    bus_id=bus_id, 
    seat_number=booked
).with_for_update().first()

if seat:
    error_message = "別の利用者が登録済みです"
    return render_template('error.html', error_message=error_message)

# 予約作成とコミット（ロック内で実行）
reservation = Reservation(...)
db.session.add(reservation)
db.session.commit()
```

**実装ファイル**: `student/app/routes/booking.py`

#### management_api.py の修正
```python
# 既存予約のチェック（排他ロックを使用）
# with_for_update()を使用して行レベルロックを取得し、並行アクセス時の競合を防止
existing_reservations = db.session.query(Reservation).filter(
    Reservation.bus_id == bus_id,
    Reservation.seat_number.in_(seat_numbers)
).with_for_update().all()

if existing_reservations:
    # エラー処理
    ...
```

**実装ファイル**: `student/app/routes/management_api.py`

### 3. マイグレーションツールの作成（実装済み）

#### add_unique_constraint_reservation.py
一意制約をデータベースに追加するマイグレーションスクリプト

**機能**:
- 既存の制約を確認
- 重複データの検出
- 一意制約の追加
- 制約の確認

**実装ファイル**: `student/add_unique_constraint_reservation.py`

#### clean_duplicate_reservations.py
既存の重複予約をクリーンアップするスクリプト

**機能**:
- 重複予約の検出
- 詳細情報の表示
- 最新以外の予約を削除（ドライランモードあり）

**実装ファイル**: `student/clean_duplicate_reservations.py`

---

## 🎯 修正後のテスト結果

### テスト1: 最悪ケース（全員が座席1を予約）

```
並行スレッド数: 50
ユーザー数: 500人
テストモード: same_seat
```

#### 結果
- **総実行時間**: 0.63秒
- **平均処理時間**: 0.054秒/予約
- **スループット**: 799.40予約/秒
- **成功**: 1件 (0.2%) ✅
- **失敗**: 499件 (99.8%)
- **ロックエラー**: 0件
- **重複エラー**: 499件（正常な拒否）
- **最終的な予約数**: 1件
- **✅ 重複予約なし: データベース整合性OK** 🎉

### テスト2: ランダム座席モード

```
並行スレッド数: 50
ユーザー数: 500人
テストモード: random_seats
```

#### 結果
- **総実行時間**: 0.55秒
- **平均処理時間**: 0.037秒/予約
- **スループット**: 916.77予約/秒
- **成功**: 27件 (5.4%) ✅
- **失敗**: 473件 (94.6%)
- **ロックエラー**: 0件
- **重複エラー**: 473件（正常な拒否）
- **最終的な予約数**: 27件
- **✅ 重複予約なし: データベース整合性OK** 🎉

---

## 📊 修正前後の比較

### データベース整合性

| 項目 | 修正前 | 修正後 |
|------|--------|--------|
| 重複予約の発生 | 🚨 **あり**（座席1に9件） | ✅ **なし** |
| データベース整合性 | ❌ **破綻** | ✅ **OK** |
| 一意制約 | ❌ **なし** | ✅ **あり** |
| 行レベルロック | ❌ **なし** | ✅ **あり** |

### パフォーマンス

| 項目 | 修正前 | 修正後 | 変化 |
|------|--------|--------|------|
| スループット（same_seat） | 931.76予約/秒 | 799.40予約/秒 | -14.2% |
| スループット（random_seats） | 722.88予約/秒 | 916.77予約/秒 | +26.8% |
| 平均処理時間 | 0.045-0.046秒 | 0.037-0.054秒 | ほぼ同等 |

**分析**: 
- 最悪ケースでは若干のパフォーマンス低下があるが、許容範囲内
- ランダムケースではむしろ改善
- データベース整合性の確保が最優先であり、この程度のオーバーヘッドは妥当

---

## 📋 実装手順（実施済み）

### ステップ1: モデルの修正 ✅
`student/app/models/reservation.py` に一意制約を追加

### ステップ2: ルートの修正 ✅
- `student/app/routes/booking.py` に SELECT FOR UPDATE を実装
- `student/app/routes/management_api.py` に SELECT FOR UPDATE を実装

### ステップ3: 既存データのクリーンアップ ✅
```bash
docker exec -it takatuki_bus-v2-student-1 python clean_duplicate_reservations.py --show
docker exec -it takatuki_bus-v2-student-1 python clean_duplicate_reservations.py --execute
```
結果: 8件の重複予約を削除

### ステップ4: マイグレーションの実行 ✅
```bash
docker exec -it takatuki_bus-v2-student-1 python add_unique_constraint_reservation.py
```
結果: 一意制約 'uq_bus_seat' を追加成功

### ステップ5: テストの再実行 ✅
```bash
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 same_seat
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 random_seats
```
結果: 全てのテストで重複予約なし

---

## 🎓 学んだ教訓

### 1. データベース制約の重要性
アプリケーションレベルのチェックだけでは不十分。データベースレベルでの制約が必須。

### 2. 並行処理時の競合状態
SELECT と INSERT の間にタイムラグがあると、複数のスレッドが同じ行を挿入できてしまう。

### 3. SELECT FOR UPDATE の効果
行レベルロックを使用することで、トランザクション完了まで他のトランザクションをブロックできる。

### 4. 多層防御の重要性
- 第1層: SELECT FOR UPDATE（アプリケーションレベル）
- 第2層: UniqueConstraint（データベースレベル）

両方実装することで、より安全なシステムになる。

---

### 1. リトライロジックの実装
デッドロックが発生した場合の自動リトライ機能

### 2. 監視とアラート
- 重複予約エラーの監視
- ロックタイムアウトの監視
- パフォーマンスメトリクスの収集

### 3. さらなる負荷テスト
- 1000人以上のユーザーでのテスト
- 複数バスへの同時予約テスト
- 長時間稼働テスト

---

## 📦 実装ファイル一覧

### 修正されたファイル
1. `student/app/models/reservation.py` - 一意制約追加
2. `student/app/routes/booking.py` - SELECT FOR UPDATE実装
3. `student/app/routes/management_api.py` - SELECT FOR UPDATE実装

### 新規作成されたファイル
1. `student/concurrent_reservation_test.py` - 並行予約負荷テストツール
2. `student/create_bulk_test_users.py` - 大量テストユーザー作成ツール
3. `student/clean_duplicate_reservations.py` - 重複予約クリーンアップツール
4. `student/add_unique_constraint_reservation.py` - マイグレーションツール
5. `docs/concurrent-reservation-test-report.md` - このレポート

---

## ✅ まとめ

### 🎯 達成したこと

1. **問題の発見**: 並行予約時の重複予約問題を検出
2. **根本原因の特定**: ロック機構の欠如を確認
3. **修正の実装**: 
   - データベース制約の追加
   - SELECT FOR UPDATEの実装
4. **検証**: 修正後のテストで重複予約が0件であることを確認
5. **ツール作成**: 今後のテストとメンテナンスのためのツール群を整備

### 🚀 本番環境への適用

以下の手順で本番環境に適用してください：

1. **バックアップ取得**
   ```bash
   pg_dump -h [host] -U [user] -d [database] > backup_$(date +%Y%m%d).sql
   ```

2. **重複データの確認と削除**
   ```bash
   docker exec -it [container] python clean_duplicate_reservations.py --show
   docker exec -it [container] python clean_duplicate_reservations.py --execute
   ```

3. **コードのデプロイ**
   - `reservation.py`, `booking.py`, `management_api.py` を更新

4. **マイグレーションの実行**
   ```bash
   docker exec -it [container] python add_unique_constraint_reservation.py
   ```

5. **動作確認**
   ```bash
   docker exec -it [container] python concurrent_reservation_test.py 100 10 random_seats
   ```

---

**レポート作成日**: 2025年12月27日  
**問題発見**: 2025年12月27日 23:20  
**修正完了**: 2025年12月27日 23:24  
**所要時間**: 約4分  
**ステータス**: ✅ **完全解決**

@contextmanager
def acquire_seat_lock(bus_id, seat_number, timeout=5):
    """座席予約用の分散ロック"""
    lock_key = f"seat_lock:{bus_id}:{seat_number}"
    lock = redis_client.lock(lock_key, timeout=timeout)
    
    acquired = lock.acquire(blocking=True, blocking_timeout=timeout)
    if not acquired:
        raise Exception("ロック取得タイムアウト")
    
    try:
        yield
    finally:
        lock.release()

def create_reservation_with_redis_lock(bus_id, seat_number, user_id):
    """Redisを使用した分散ロック付き予約作成"""
    with acquire_seat_lock(bus_id, seat_number):
        # 既存予約のチェック
        existing = db.session.query(Reservation).filter(
            Reservation.bus_id == bus_id,
            Reservation.seat_number == seat_number
        ).first()
        
        if existing:
            return {'success': False, 'message': '既に予約済みです'}
        
        # 予約作成
        reservation = Reservation(...)
        db.session.add(reservation)
        db.session.commit()
        
        return {'success': True}
```

## 推奨実装手順

### ステップ1: データベース制約を追加（最優先）
まずデータベースレベルでの保護を追加します。

### ステップ2: SELECT FOR UPDATE を実装
アプリケーションレベルでの排他制御を実装します。

### ステップ3: エラーハンドリングの改善
重複予約エラーをユーザーフレンドリーに処理します。

### ステップ4: テストの再実行
修正後、同じテストを実行して重複予約が発生しないことを確認します。

## パフォーマンスへの影響

### 現状（ロックなし）
- スループット: 722-931 予約/秒
- 重複予約: **発生する** 🚨

### 予想（SELECT FOR UPDATE導入後）
- スループット: 400-600 予約/秒（推定）
- 重複予約: **発生しない** ✅

### 予想（SERIALIZABLE導入後）
- スループット: 200-400 予約/秒（推定）
- 重複予約: **発生しない** ✅
- デッドロックの可能性: あり

## 影響範囲

### 修正が必要なファイル
1. `student/app/routes/management_api.py` - create_reservations()
2. `student/app/models/reservation.py` - UniqueConstraint追加
3. `student/migrations/` - 新しいマイグレーションファイル
4. 予約を作成する全てのエンドポイント

## テストコマンド

### 修正前のテスト
```bash
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 random_seats
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 same_seat
```

### 修正後のテスト（予定）
```bash
# 全てのテストで重複予約が0件になることを確認
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 random_seats
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 500 50 same_seat
docker exec -it takatuki_bus-v2-student-1 python concurrent_reservation_test.py 1000 100 different_seats
```

## まとめ

🚨 **現在、重大なデータベース整合性の問題が存在します。**

- ランダム座席モードでも重複予約が発生
- 最悪ケースでは同じ座席に9件の予約が入る
- 本番環境でトラブルになる可能性が高い

✅ **推奨される対応:**
1. データベース制約の追加（即座に実施）
2. SELECT FOR UPDATEの実装（高優先度）
3. エラーハンドリングの改善
4. 再テストによる検証

---

**生成日時**: 2025-12-27  
**テストスクリプト**: `student/concurrent_reservation_test.py`  
**テストユーザー作成**: `student/create_bulk_test_users.py`
