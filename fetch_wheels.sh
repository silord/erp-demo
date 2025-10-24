#!/bin/sh
INDEX=${1:-https://pypi.tuna.tsinghua.edu.cn/simple}
OUTDIR=${2:-./wheels}

mkdir -p "$OUTDIR"

python -m pip --version || { echo "pip not available"; exit 1; }

echo "Downloading wheels to $OUTDIR from index $INDEX"
python -m pip download -r requirements.txt -d "$OUTDIR" -i "$INDEX" --trusted-host $(echo $INDEX | awk -F/ '{print $3}')

if [ $? -ne 0 ]; then
  echo "pip download failed"
  exit 2
fi

echo "Wheels downloaded to $(pwd)/$OUTDIR"