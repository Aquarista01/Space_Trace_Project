# Lenh tat cho docker compose production (Windows PowerShell).
# Dung: .\scripts\prod.ps1 {up|stop|down|ps|logs|build} [service]
param(
  [Parameter(Position = 0)][string]$Action = "",
  [Parameter(Position = 1, ValueFromRemainingArguments = $true)][string[]]$Rest
)
Set-Location (Join-Path $PSScriptRoot "..")

$compose = @("compose", "-f", "docker-compose.prod.yml", "--env-file", ".env", "--env-file", ".env.deploy")

switch ($Action) {
  "up"    { docker @compose up -d --build }
  "stop"  { docker @compose stop }
  "down"  { docker @compose down }   # khong dung -v: giu lai du lieu
  "ps"    { docker @compose ps }
  "logs"  { docker @compose logs -f --tail=100 @Rest }
  "build" { docker @compose build @Rest }
  default { Write-Host "Dung: .\scripts\prod.ps1 {up|stop|down|ps|logs|build} [service]"; exit 1 }
}