# マイコン向け高速起動Dockerfile
# 軽量なPython Alpine イメージを使用
FROM python:3.11-alpine AS builder

# ビルド時の依存関係をインストール
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    linux-headers \
    libusb-dev \
    pcsc-lite-dev

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係のみ先にコピー（キャッシュ効率化）
COPY requirements.txt .

# Pythonパッケージをインストール
RUN pip install --no-cache-dir --user -r requirements.txt

# 実行ステージ
FROM python:3.11-alpine

# 実行時の依存関係のみインストール
RUN apk add --no-cache \
    libusb \
    pcsc-lite-libs \
    sqlite \
    && rm -rf /var/cache/apk/*

# 作業ディレクトリを設定
WORKDIR /app

# ビルドステージからPythonパッケージをコピー
COPY --from=builder /root/.local /root/.local

# アプリケーションファイルをコピー
COPY auth.py .
COPY templates/ ./templates/
COPY *.wav ./

# データベースディレクトリを作成
RUN mkdir -p instance

# 環境変数のパスを設定
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# ポート8000を公開
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/auth/wait || exit 1

# アプリケーションを起動
CMD ["python", "-O", "auth.py"]
