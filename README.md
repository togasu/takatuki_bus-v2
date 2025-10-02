# README

## 概要
このプロジェクトは、**Flask ベースのマイクロサービス**（`student` / `admin` / `driver`）を  
**nginx リバースプロキシ**で統合し、**PostgreSQL** と **Redis** をバックエンドに利用する構成です。  

- 各サービスは独立した Flask アプリとして動作
- API は Blueprint 単位で分割管理
- WebSocket（Flask-SocketIO）対応
- PostgreSQL + SQLAlchemy + Flask-Migrate によるDBマイグレーション
- nginx による HTTPS 強制 & リバースプロキシ
- 各サービスごとのアクセスログ
- メンテナンスページ対応（サービスダウン時に表示）
- 永続化（PostgreSQL / Redis / ログ / 証明書）

---

## ディレクトリ構成
```
.
├── student/
│   ├── app/
│   │   ├── __init__.py         # Flask, DB, SocketIO 初期化
│   │   ├── routes/             # APIルート（Blueprint）
│   │   ├── models/             # SQLAlchemyモデル
│   │   └── templates/          # HTMLテンプレート
│   ├── requirements.txt
│   ├── uwsgi.ini
│   └── Dockerfile
├── admin/                      # student と同様の構成
├── driver/                     # student と同様の構成
├── nginx.conf                   # nginx 設定（HTTPS + リバースプロキシ + メンテ画面）
├── maintenance.html             # ダウン時表示用ページ
├── docker-compose.yml
├── certs/                       # SSL証明書（自己署名 or 実証明書）
├── logs/                        # アクセスログ
├── generate_cert.sh              # Mac/Linux 用証明書生成スクリプト
├── generate_cert.ps1              # Windows PowerShell 用証明書生成スクリプト
└── .gitignore
```

---

## 前提条件
- Docker / Docker Compose がインストールされていること
- OpenSSL が利用可能であること（証明書生成用）

---

## セットアップ

### 1. 証明書の生成
#### Mac / Linux
```bash
chmod +x generate_cert.sh
./generate_cert.sh
```
#### Windows PowerShell
```powershell
.\generate_cert.ps1
```

---

### 2. コンテナ起動
```bash
docker-compose up --build
```

---

### 3. HTTPSアクセス
- `https://localhost/student`
- `https://localhost/admin`
- `https://localhost/driver`

HTTPアクセスは自動的にHTTPSへリダイレクトされます。

---

## DBマイグレーション（Flask-Migrate）

例：`student` サービスで実行
```bash
docker-compose exec student flask db init        # 初回のみ
docker-compose exec student flask db migrate -m "Initial migration"
docker-compose exec student flask db upgrade
```
同様に `admin` / `driver` でも実行可能です。

---

## ログ
- 各サービスの `/app/logs/access.log` に  
  「アクセス元IPアドレス」「アクセスパス」を記録
- `docker-compose.yml` の `./logs` にマウントされ、ホスト側にも保存されます

---

## メンテナンスページ
- サービスが落ちた場合、nginx が `/maintenance.html` を表示
- 対象：502, 503, 504 エラー

---

## APIルーティング方針
- `app/routes/` に1機能1ファイルでBlueprint定義
- 新しいルートを追加する場合はファイルを置くだけで自動登録

---

## WebSocket
- 各サービスに `ws.py` を置くことで WebSocket イベント対応
- nginx.conf に `Upgrade` ヘッダー設定済み

---

## 永続化
- PostgreSQL: `postgres_data` ボリューム
- Redis: `redis_data` ボリューム
- ログ: `./logs` ディレクトリ
- SSL証明書: `./certs`

---

## セキュリティ
- HTTPS強制
- サービス間通信は内部Dockerネットワーク
- APIアクセス制御はJWT/OAuth2などの導入を推奨

---

## 今後の拡張案
- JWTによる認証API追加
- AdminからStudentの機密データ取得API（HTTPS + 認可制御）
- CI/CD導入
- ヘルスチェックのK8s対応
