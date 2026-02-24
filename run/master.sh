#!/usr/bin/env bash
set -e

echo "=== UNICON MASTER START ==="

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE_DIR"

if [ -f "$BASE_DIR/config/unicon.env" ]; then
  echo "[OK] loading config/unicon.env"
  set -a
  source "$BASE_DIR/config/unicon.env"
  set +a
else
  echo "[WARN] config/unicon.env NOT FOUND"
fi

echo "[INFO] BASE_DIR=$BASE_DIR"
echo "[INFO] LUNA_PORT=${LUNA_PORT:-not_set}"
echo "[INFO] LUNA_BAUD=${LUNA_BAUD:-not_set}"
echo "[INFO] FORCE_SCALE=${FORCE_SCALE:-not_set}"

exec python3 src/cam_luna_web.py
