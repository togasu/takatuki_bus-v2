# 内部APIセキュリティ設計

## 概要
adminサービスとstudentサービス間の内部APIを外部から隠蔽し、マイクロサービス間の通信をセキュアに保護する設計です。

## セキュリティレイヤー

### 1. ネットワークレベルの保護（Docker Network）

**docker-compose.yml**
- student, admin, driverサービスの外部ポート公開を削除
- サービス間通信はDockerの内部ネットワーク（`takatuki_bus-v2_default`）のみで行われる
- nginxコンテナのみが80/443ポートを外部公開

**メリット:**
- 直接的なポート攻撃を防止
- サービスへのアクセスは必ずnginxを経由

### 2. nginxレベルの保護（リバースプロキシ）

**nginx/nginx.conf**
```nginx
# 内部API保護: /api/management と /api/statistics へのアクセスを拒否
location ~ ^/(api/management|api/statistics) {
    deny all;
    return 403;
}
```

**保護対象のエンドポイント:**
- `/api/management/*` - 学生管理、バス管理、ペナルティ管理API
- `/api/statistics/*` - 統計情報API

**メリット:**
- 外部からこれらのエンドポイントへの直接アクセスを完全にブロック
- 403 Forbiddenを返すことで、エンドポイントの存在を隠蔽

### 3. アプリケーションレベルの保護（認証デコレーター）

**student/app/decorators.py**
```python
@require_service_auth
def protected_endpoint():
    # 内部API処理
    pass
```

**認証フロー:**
1. リクエストヘッダーから`X-Service-Auth`と`X-API-Key`を検証
2. 環境変数`ADMIN_SERVICE_TOKEN`および`API_SECRET_KEY`と照合
3. 一致しない場合は401 Unauthorizedを返す

**保護対象ファイル:**
- `student/app/routes/management_api.py` - 全エンドポイント
- `student/app/routes/statistics_api.py` - 全エンドポイント

## 内部サービス間の通信フロー

### Admin → Student
```
[Admin Service]
    ↓ (Docker内部ネットワーク)
    ↓ X-Service-Auth: <token>
    ↓ X-API-Key: <api_key>
    ↓
[Student Service] → @require_service_auth → 認証成功 → API処理
```

### Driver → Student
```
[Driver Service]
    ↓ (Docker内部ネットワーク)
    ↓ X-Service-Auth: <token>
    ↓ X-API-Key: <api_key>
    ↓
[Student Service] → @require_service_auth → 認証成功 → API処理
```

### 外部ユーザー → Student（内部API）
```
[外部ユーザー]
    ↓
[nginx] → location ~ ^/(api/management|api/statistics)
    ↓
deny all (403 Forbidden)
```

## 認証トークン管理

### 環境変数（.env）
```bash
ADMIN_SERVICE_TOKEN=admin-secret-token-2024
API_SECRET_KEY=bus-system-api-key-2024
```

**重要:**
- 本番環境では必ず強力なランダム文字列に変更すること
- トークンは定期的にローテーションすること
- トークンをGitにコミットしないこと

### トークン生成例
```bash
# PowerShellの場合
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})

# Linuxの場合
openssl rand -base64 32
```

## 内部APIクライアント実装

### Admin Service
**admin/app/api_client.py**
```python
class AdminAPIClient:
    def __init__(self):
        self.admin_token = os.getenv('ADMIN_SERVICE_TOKEN')
        self.api_key = os.getenv('API_SECRET_KEY')
        self.headers = {
            'X-Service-Auth': self.admin_token,
            'X-API-Key': self.api_key,
            'User-Agent': 'admin-service-client/1.0',
            'Content-Type': 'application/json'
        }
```

### Driver Service
**driver/app/utils/student_api_client.py**
```python
class StudentServiceClient:
    def __init__(self):
        self.session.headers.update({
            'X-Service-Auth': os.getenv('ADMIN_SERVICE_TOKEN'),
            'X-API-Key': os.getenv('API_SECRET_KEY'),
            'User-Agent': 'driver-service-client/1.0'
        })
```

## セキュリティテスト

### 外部アクセスのテスト（失敗すべき）
```bash
# 内部APIへの外部アクセス - 403エラーが返るべき
curl http://localhost/api/management/all_students
curl https://localhost/api/statistics/realtime

# 期待される結果: 403 Forbidden
```

### 内部アクセスのテスト（成功すべき）
```bash
# Dockerコンテナ内から
docker exec -it takatuki_bus-v2-admin-1 bash

# 正しいトークンで内部APIにアクセス
curl -H "X-Service-Auth: admin-secret-token-2024" \
     -H "X-API-Key: bus-system-api-key-2024" \
     http://student:5000/api/management/all_students
```

## 利点

1. **多層防御**
   - ネットワーク、プロキシ、アプリケーションの3層で保護
   - 一つの層が突破されても他の層で防御

2. **ゼロトラスト原則**
   - 内部ネットワークからのアクセスでもトークン認証が必要
   - サービス間の信頼関係を明示的に管理

3. **監査とログ**
   - 認証失敗のログを記録
   - 不正アクセス試行を検知可能

4. **柔軟性**
   - 新しいマイクロサービスを追加する際も同じパターンで保護
   - トークンの更新が容易

## セキュリティチェックリスト

- [ ] 本番環境でトークンを変更済み
- [ ] .envファイルが.gitignoreに含まれている
- [ ] nginx設定で内部APIがブロックされている
- [ ] 全内部APIエンドポイントに@require_service_authが適用されている
- [ ] 外部からの内部APIアクセスが403を返すことを確認
- [ ] 内部サービス間通信が正常に動作することを確認
- [ ] ログに認証失敗が記録されることを確認

## トラブルシューティング

### 内部API呼び出しで401エラーが発生する場合
1. 環境変数が正しく設定されているか確認
   ```bash
   docker exec takatuki_bus-v2-admin-1 env | grep TOKEN
   docker exec takatuki_bus-v2-student-1 env | grep TOKEN
   ```

2. ヘッダーが正しく送信されているか確認
   - `X-Service-Auth`と`X-API-Key`が両方必要

3. トークンの値が一致しているか確認
   - 全サービスで同じ環境変数を使用していること

### nginx設定変更が反映されない場合
```bash
docker-compose restart nginx
# または
docker-compose exec nginx nginx -s reload
```

## 参考資料
- [マイクロサービスセキュリティベストプラクティス](https://microservices.io/patterns/security/service-to-service-security.html)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
