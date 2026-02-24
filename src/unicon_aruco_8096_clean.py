from __future__ import annotations
import os, time
from typing import Any, Dict
import cv2
from flask import Flask, jsonify, request

APP_NAME = "unicon_aruco_8096_clean"
PORT = int(os.environ.get("UNICON_ARUCO_PORT", "8096"))
VIDEO = os.environ.get("UNICON_ARUCO_VIDEO", "/dev/video2")
DICT_NAME = os.environ.get("UNICON_ARUCO_DICT", "DICT_4X4_50")

app = Flask(APP_NAME)

def _aruco():
    return getattr(cv2, "aruco", None)

def _get_dict():
    ar = _aruco()
    if ar is None:
        return None
    return ar.getPredefinedDictionary(getattr(ar, DICT_NAME))

def _open_cap(dev: str):
    cap = cv2.VideoCapture(dev, cv2.CAP_V4L2)
    if not cap.isOpened():
        cap.release()
        return None
    return cap

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": APP_NAME, "port": PORT, "video": VIDEO, "dict": DICT_NAME, "aruco": _aruco() is not None})

@app.get("/api/aruco/test")
def aruco_test():
    dev = request.args.get("dev", VIDEO)
    cap = _open_cap(dev)
    if cap is None:
        return jsonify({"ok": False, "err": f"open_failed VIDEO={dev}"}), 500

    time.sleep(0.05)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        return jsonify({"ok": False, "err": f"read_failed VIDEO={dev}"}), 500

    ar = _aruco()
    d = _get_dict()
    if ar is None or d is None:
        return jsonify({"ok": False, "err": "cv2.aruco_missing"}), 500

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = ar.detectMarkers(gray, d)
    n = 0 if ids is None else int(len(ids))
    id_list = [] if ids is None else [int(x) for x in ids.flatten().tolist()]
    return jsonify({"ok": True, "video": dev, "markers": n, "ids": id_list})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, threaded=True)
