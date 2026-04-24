Write-Host "=== 自己署名証明書を生成します ==="

New-Item -ItemType Directory -Force -Path ".\certs" | Out-Null

docker run --rm -v "${PWD}\certs:/certs" alpine/openssl `
  req -x509 -nodes -days 365 `
  -newkey rsa:2048 `
  -keyout /certs/server.key `
  -out /certs/server.crt `
  -subj "/CN=localhost"

if ((Test-Path ".\certs\server.crt") -and (Test-Path ".\certs\server.key")) {
    Write-Host "=== 証明書生成完了 ==="
    Write-Host "証明書: certs/server.crt"
    Write-Host "秘密鍵: certs/server.key"
} else {
    Write-Error "証明書生成に失敗しました"
    exit 1
}