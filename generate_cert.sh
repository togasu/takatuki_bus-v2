#!/bin/bash

set -e

CERT_DIR="certs"
mkdir -p "$CERT_DIR"

echo "=== 自己署名証明書を生成します ==="

openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout "$CERT_DIR/server.key" \
  -out "$CERT_DIR/server.crt" \
  -subj "/C=JP/ST=Tokyo/L=Shibuya/O=Example/OU=Dev/CN=localhost"

echo "=== 証明書生成完了 ==="
echo "証明書: $CERT_DIR/server.crt"
echo "秘密鍵: $CERT_DIR/server.key"
