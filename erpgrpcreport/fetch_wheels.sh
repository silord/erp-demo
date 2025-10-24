#!/usr/bin/env bash
# Download wheels for erpgrpcreport requirements into ./wheels

set -euo pipefail
OUT_DIR="./wheels"
INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"

if [ ! -f erpgrpcreport/requirements.txt ]; then
  echo "requirements.txt not found at erpgrpcreport/requirements.txt" >&2
  exit 2
fi

mkdir -p "$OUT_DIR"
echo "Downloading wheels into $OUT_DIR using index $INDEX_URL"

# prefer-binary to prefer wheels where available
python -m pip download -r erpgrpcreport/requirements.txt -d "$OUT_DIR" --index-url "$INDEX_URL" --prefer-binary || {
  echo "Initial download failed; retrying without --prefer-binary" >&2
  python -m pip download -r erpgrpcreport/requirements.txt -d "$OUT_DIR" --index-url "$INDEX_URL"
}

cat <<'USAGE'
Download finished. To install from this folder on the target machine run:
  python -m pip install --no-index --find-links=./wheels -r erpgrpcreport/requirements.txt
USAGE
