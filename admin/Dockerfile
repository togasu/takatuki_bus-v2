FROM python:3.11-slim

WORKDIR /app

# 必要なビルドツールと非rootユーザーを追加
RUN apt-get update && apt-get install -y \
    gcc g++ libc-dev linux-headers-amd64 make \
    && useradd -m uwsgi \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

# gevent / greenlet を先にインストールしてから uwsgi
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir "gevent>=24.2.1" "greenlet>=3.0.3" \
    && pip install --no-cache-dir -r requirements.txt

COPY app /app/app
COPY app_run.py /app/
COPY uwsgi.ini /app/
COPY init_migration.py /app/
COPY auto_fix_tables.py /app/
COPY create_test_admin.py /app/
COPY start_admin.sh /app/

# ディレクトリの作成と権限設定
RUN mkdir -p /app/logs /app/migrations && \
    chown -R uwsgi:uwsgi /app && \
    chmod -R 755 /app && \
    chmod +x /app/start_admin.sh

# Flask-Migrate用の環境変数
ENV FLASK_APP=app_run.py

# 非rootで実行
USER uwsgi

# 柔軟な起動スクリプト使用
CMD ["/app/start_admin.sh"]
