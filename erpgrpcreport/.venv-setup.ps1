<#
.SYNOPSIS
    Create and bootstrap a Python virtual environment for erpgrpcreport.

DESCRIPTION
    This script will:
      - create a .venv folder if not present
      - upgrade pip, setuptools and wheel
      - install dependencies from erpgrpcreport/requirements.txt
        using a domestic PyPI mirror by default (Tsinghua)

    Usage (PowerShell):
      .\.venv-setup.ps1 [-Mirror <mirrorUrl>] [-Force]

    Examples:
      .\.venv-setup.ps1
      .\.venv-setup.ps1 -Mirror 'https://pypi.tuna.tsinghua.edu.cn/simple' -Force

#>
param(
    [string] $Mirror = 'https://pypi.tuna.tsinghua.edu.cn/simple',
    [switch] $Force
)

Set-StrictMode -Version Latest

function Write-Info($m) { Write-Host "[info] $m" -ForegroundColor Cyan }
function Write-ErrorAndExit($m) { Write-Host "[error] $m" -ForegroundColor Red; exit 1 }

Write-Info "Using Python from PATH to create virtual environment (python)"

try {
    $py = Get-Command python -ErrorAction Stop
} catch {
    Write-ErrorAndExit "python not found in PATH. Please install Python 3.8+ and ensure 'python' is on PATH."
}

$venvDir = Join-Path -Path (Get-Location) -ChildPath '.venv'
if (Test-Path $venvDir) {
    if ($Force) {
        Write-Info "Removing existing .venv because -Force provided"
        Remove-Item -Recurse -Force $venvDir
    } else {
        Write-Info ".venv already exists; skipping creation"
    }
}

if (-not (Test-Path $venvDir)) {
    Write-Info "Creating virtual environment in .venv"
    & python -m venv $venvDir
    if ($LASTEXITCODE -ne 0) { Write-ErrorAndExit "Failed to create virtualenv" }
}

$pyExe = Join-Path $venvDir 'Scripts\python.exe'
if (-not (Test-Path $pyExe)) { Write-ErrorAndExit "Virtualenv python not found at $pyExe" }

Write-Info "Upgrading pip, setuptools, wheel in virtualenv"
& $pyExe -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) { Write-ErrorAndExit "Failed to upgrade packaging tools" }

$requirements = 'erpgrpcreport/requirements.txt'
if (-not (Test-Path $requirements)) { Write-ErrorAndExit "Requirements file not found: $requirements" }

Write-Info "Installing requirements from $requirements using mirror $Mirror"
& $pyExe -m pip install --prefer-binary -r $requirements --index-url $Mirror
if ($LASTEXITCODE -ne 0) {
    Write-Host "Primary install failed. Retrying without --prefer-binary..." -ForegroundColor Yellow
    & $pyExe -m pip install -r $requirements --index-url $Mirror
    if ($LASTEXITCODE -ne 0) { Write-ErrorAndExit "Failed to install requirements" }
}

Write-Info "Setup complete. To activate the virtualenv in this PowerShell session run:"
Write-Host "  .\ .venv\Scripts\Activate.ps1" -ForegroundColor Green
Write-Host "Then you can run: python erpgrpcreport/app.py" -ForegroundColor Green
