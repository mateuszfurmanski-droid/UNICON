# aruco_api_v1.py
# Minimal stable API module: always provides `aruco_bp` for master import.

import time
from flask import Blueprint, jsonify, request

aruco_bp = Blueprint("aruco_v1", __name__, url_prefix="/api/aruco")

@aruco_bp.get("/test_v1")
def test_v1():
    # Minimal health-style endpoint for fast verification.
    d = request.args.get("dict", "DICT_4X4_50")
    return jsonify({
        "ok": True,
        "ts": time.time(),
        "dict": d,
        "ids": [],
        "corners": [],
        "err": "stub_ok"
    })

@aruco_bp.get("/ping")
def ping():
    return jsonify({"ok": True, "ts": time.time()})
