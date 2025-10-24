<#
.SYNOPSIS
    Download Python wheels for erpgrpcreport requirements into ./wheels

.DESCRIPTION
    Run this on a machine with internet access to prefetch wheel files for
    offline or air-gapped builds. The default uses the Tsinghua PyPI mirror.

    Usage:
      .\fetch_wheels.ps1
      .\fetch_wheels.ps1 -OutDir .\wheels -IndexUrl 'https://pypi.tuna.tsinghua.edu.cn/simple'

#>
param(
    [string] $OutDir = '.\wheels',
    [string] $IndexUrl = 'https://pypi.tuna.tsinghua.edu.cn/simple'
)

Set-StrictMode -Version Latest

if (-not (Test-Path 'erpgrpcreport/requirements.txt')) {
    Write-Error "requirements.txt not found at erpgrpcreport/requirements.txt"
    exit 2
}

if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

Write-Host "Downloading wheels into $OutDir using index $IndexUrl"

# Try prefer-binary first to get wheels when possible
& python -m pip download -r erpgrpcreport/requirements.txt -d $OutDir --index-url $IndexUrl --prefer-binary
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Initial download failed; retrying without --prefer-binary"
    & python -m pip download -r erpgrpcreport/requirements.txt -d $OutDir --index-url $IndexUrl
    if ($LASTEXITCODE -ne 0) {
        Write-Error "pip download failed"
        exit $LASTEXITCODE
    }
}

Write-Host "Download finished. To install from this folder on the target machine run:" -ForegroundColor Green
Write-Host "  python -m pip install --no-index --find-links=./wheels -r erpgrpcreport/requirements.txt" -ForegroundColor Green
