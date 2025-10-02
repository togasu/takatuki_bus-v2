$certDir = "certs"
if (-not (Test-Path $certDir)) {
    New-Item -ItemType Directory -Path $certDir | Out-Null
}

Write-Host "=== 自己署名証明書を生成します ==="

$subj = "/C=JP/ST=Tokyo/L=Shibuya/O=Example/OU=Dev/CN=localhost"

openssl req -x509 -nodes -days 365 `
  -newkey rsa:2048 `
  -keyout "$certDir/server.key" `
  -out "$certDir/server.crt" `
  -subj $subj

Write-Host "=== 証明書生成完了 ==="
Write-Host "証明書: $certDir/server.crt"
Write-Host "秘密鍵: $certDir/server.key"
