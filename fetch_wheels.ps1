param(
    [string]$Index = 'https://pypi.tuna.tsinghua.edu.cn/simple',
    [string]$OutDir = '.\wheels'
)

if (-Not (Test-Path -Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir | Out-Null
}

# Ensure pip is available
python -m pip --version
if ($LASTEXITCODE -ne 0) {
    Write-Error 'python -m pip not available on PATH'
    exit 1
}

# Download wheels for requirements
Write-Host "Downloading wheels to $OutDir from index $Index"
python -m pip download -r requirements.txt -d $OutDir -i $Index --trusted-host $(($Index -replace '^https?://', '') -split '/')[0]
if ($LASTEXITCODE -ne 0) {
    Write-Error 'pip download failed'
    exit 2
}

Write-Host 'Wheels downloaded to' (Resolve-Path $OutDir)