$ErrorActionPreference = 'Stop'
$desktop = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Resolve-Path (Join-Path $desktop '../../..')).Path
Set-Location $desktop
if (-not (Test-Path (Join-Path $desktop 'node_modules'))) {
  Write-Host 'Installing frontend packages...' -ForegroundColor Cyan
  npm install
}
Write-Host 'Starting the Iskolar desktop UI...' -ForegroundColor Cyan
npm run tauri dev
