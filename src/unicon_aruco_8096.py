#!/usr/bin/env python3
import os
import time
from typing import Dict, Any, List

import cv2
import numpy as np
from flask import Flask, jsonify, request

APP_HOST = os.environ.get("ARUCO_HOST", "0.0.0.0")
APP_PORT = int(os.environ.get("ARUCO_PORT", "8096"))
VIDEO_DEFAULT = os.environ.get("ARUCO_VIDEO", "/dev/video3")  # avoid HUD /dev/video2

DICT_NAME = os.environ.get("ARUCO_DICT", "DICT_4X4_50")
DICT_MAP = {
    "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
    "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
    "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
    "DICT_7X7_50": cv2.aruco.DICT_7X7_50,
}
ARUCO_DICT = cv2.aruco.getPredefinedDictionary(DICT_MAP.get(DICT_NAME, cv2.aruco.DICT_4X4_50))
PARAMS = cv2.aruco.DetectorParameters()

app = Flask("unicon_aruco_server")

def _open_cap(dev: str) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(dev, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cap

def _grab(dev: str) -> Dict[str, Any]:
    cap = _open_cap(dev)
    try:
        if not cap.isOpened():
            return {"ok": False, "err": f"open_failed VIDEO={dev}"}
        ok, frame = cap.read()
        if not ok or frame is None:
            return {"ok": False, "err": f"read_failed VIDEO={dev}"}
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = cv2.aruco.detectMarkers(gray, ARUCO_DICT, parameters=PARAMS)

        markers: List[Dict[str, Any]] = []
        if ids is not None and len(ids) > 0:
            for i, mid in enumerate(ids.flatten().tolist()):
                pts = corners[i].reshape(-1, 2).tolist()
                markers.append({"id": int(mid), "corners": pts})

        return {
            "ok": True,
            "video": dev,
            "dict": DICT_NAME,
            "w": int(w),
            "h": int(h),
            "count": int(0 if ids is None else len(ids)),
            "ids": [] if ids is None else ids.flatten().astype(int).tolist(),
            "markers": markers,
            "ts": time.time(),
        }
    finally:
        cap.release()

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "unicon_aruco_8096", "dict": DICT_NAME, "video": VIDEO_DEFAULT})

@app.get("/")
def root():
    return jsonify({"ok": True, "routes": ["/health", "/api/aruco", "/api/aruco/test"]})

@app.get("/api/aruco")
def aruco_alias():
    return aruco_test()

@app.get("/api/aruco/test")
def aruco_test():
    dev = request.args.get("dev", VIDEO_DEFAULT)
    return jsonify(_grab(dev))

if __name__ == "__main__":
    app.run(host=APP_HOST, port=APP_PORT, threaded=True)
