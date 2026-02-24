from __future__ import annotations

import os
import time
from typing import Any, Dict

import cv2
from flask import Flask, jsonify, request

APP_NAME = "unicon_aruco_8096_fixed"
app = Flask(APP_NAME)

PORT = int(os.environ.get("UNICON_ARUCO_PORT", "8096"))
DEFAULT_DEV = os.environ.get("UNICON_ARUCO_VIDEO", "/dev/video0")
DICT_NAME = os.environ.get("UNICON_ARUCO_DICT", "DICT_4X4_50")

def _aruco_mod():
    try:
        return cv2.aruco
    except Exception:
        return None

def _get_dict():
    aruco = _aruco_mod()
    if aruco is None:
        return None
    if not hasattr(aruco, DICT_NAME):
        return None
    return aruco.getPredefinedDictionary(getattr(aruco, DICT_NAME))

def _open_cam(dev: str):
    cap = cv2.VideoCapture(dev, cv2.CAP_V4L2)
    if not cap or not cap.isOpened():
        return None
    # conservative defaults
    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    except Exception:
        pass
    # warmup
    t0 = time.time()
    ok = False
    frame = None
    while time.time() - t0 < 1.0:
        ok, frame = cap.read()
        if ok and frame is not None:
            break
        time.sleep(0.05)
    if not ok or frame is None:
        cap.release()
        return None
    return cap

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": APP_NAME, "port": PORT, "video": DEFAULT_DEV, "dict": DICT_NAME})

@app.get("/api/aruco/test")
def aruco_test():
    dev = request.args.get("dev", DEFAULT_DEV)
    aruco = _aruco_mod()
    if aruco is None:
        return jsonify({"ok": False, "err": "cv2.aruco_missing", "video": dev}), 500

    d = _get_dict()
    if d is None:
        return jsonify({"ok": False, "err": f"bad_dict:{DICT_NAME}", "video": dev}), 500

    cap = _open_cam(dev)
    if cap is None:
        return jsonify({"ok": False, "err": f"open_failed VIDEO={dev}", "video": dev}), 500

    try:
        ok, frame = cap.read()
        if not ok or frame is None:
            return jsonify({"ok": False, "err": f"read_failed VIDEO={dev}", "video": dev}), 500

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = aruco.detectMarkers(gray, d)

        n = 0 if ids is None else int(len(ids))
        return jsonify({
            "ok": True,
            "video": dev,
            "markers": n,
            "ids": [] if ids is None else [int(x) for x in ids.flatten().tolist()],
            "w": int(frame.shape[1]),
            "h": int(frame.shape[0]),
        })
    finally:
        try:
            cap.release()
        except Exception:
            pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
