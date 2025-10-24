How to prefetch wheels for offline/air-gapped builds
===============================================

This directory contains helper scripts to download Python wheel files for the
`erpgrpcreport` package's dependencies so you can install them in an
environment without internet access.

1) On a machine that has internet access (Windows PowerShell):

   .\fetch_wheels.ps1  # by default saves to ./wheels using Tsinghua mirror

2) Or on Linux/macOS:

   ./fetch_wheels.sh

3) Copy the resulting `wheels/` directory to the target machine and install:

   python -m pip install --no-index --find-links=./wheels -r erpgrpcreport/requirements.txt

Notes:
- If you need wheels for a different platform (e.g. manylinux vs win_amd64), run the download script on a machine with that same platform / Python version so pip will select compatible wheels.
- You can supply a different PyPI mirror by editing the script or passing parameters where supported.
