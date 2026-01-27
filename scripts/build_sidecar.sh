#!/usr/bin/env bash
set -euo pipefail

OS_SHORT=${1:-}
if [[ -z "$OS_SHORT" ]]; then
  echo "Usage: $0 <mac|win|linux>"
  exit 1
fi

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install .
python -m pip install pyinstaller

python -m PyInstaller \
  --noconfirm \
  --clean \
  --onedir \
  --name harmonization-sidecar \
  --paths src \
  --distpath dist/sidecar/${OS_SHORT} \
  scripts/sidecar_entry.py

echo "Built sidecar in dist/sidecar/${OS_SHORT}"
