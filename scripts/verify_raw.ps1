# List raw TLC + weather objects in MinIO (requires mc + credentials).
param(
  [string]$AliasName = "local",
  [string]$Endpoint = "http://127.0.0.1:9000",
  [string]$User = "minio",
  [string]$Pass = "minio_dev_change_me"
)

$ErrorActionPreference = "Stop"
mc alias set $AliasName $Endpoint $User $Pass | Out-Null
Write-Host "=== raw/tlc ==="
mc ls --recursive "$AliasName/raw/tlc/" 2>$null
Write-Host "=== raw/weather ==="
mc ls --recursive "$AliasName/raw/weather/" 2>$null
