#!/usr/bin/env bash
set -e

echo "[UNICON] Starting LiDAR service"

cd ~/UNICON/unicon_core/services/lidar_service

python3 app.py
