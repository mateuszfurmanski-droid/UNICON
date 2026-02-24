from __future__ import annotations

import os
import cv2
from flask import Flask, jsonify, request

APP_NAME = "unicon_aruco_server"
app = Flask(APP_NAME)

PORT = int(os.environ.get("UNICON_ARUCO_PORT", "8096"))
DEFAULT_DEV = os.environ.get("UNICON_ARUCO_VIDEO", "/dev/video0")
DICT_NAME = os.environ.get("UNICON_ARUCO_DICT", "DICT_4X4_50")

def _get_dict():
    if not hasattr(cv2, "aruco"):
        return None
    aruco = cv2.aruco
    if not hasattr(aruco, DICT_NAME):
        return None
    return aruco.getPredefinedDictionary(getattr(aruco, DICT_NAME))

def _open_cap(dev: str):
    cap = cv2.VideoCapture(dev, cv2.CAP_V4L2)
    if not cap.isOpened():
        try:
            cap.release()
        except Exception:
            pass
        return None
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    return cap

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "unicon_aruco_8096", "dict": DICT_NAME, "video": DEFAULT_DEV})

@app.get("/api/aruco/test")
def aruco_test():
    dev = request.args.get("dev", DEFAULT_DEV)

    d = _get_dict()
    if d is None:
        return jsonify({"ok": False, "err": f"aruco_unavailable_or_bad_dict DICT={DICT_NAME}"}), 500

    cap = _open_cap(dev)
    if cap is None:
        return jsonify({"ok": False, "err": f"open_failed VIDEO={dev}"}), 200

    try:
        ok, frame = cap.read()
        if not ok or frame is None:
            return jsonify({"ok": False, "err": f"read_failed VIDEO={dev}"}), 200

        aruco = cv2.aruco
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if hasattr(aruco, "ArucoDetector"):
            params = aruco.DetectorParameters()
            detector = aruco.ArucoDetector(d, params)
            corners, ids, _rej = detector.detectMarkers(gray)
        else:
            params = aruco.DetectorParameters_create()
            corners, ids, _rej = aruco.detectMarkers(gray, d, parameters=params)

        found = 0 if ids is None else int(len(ids))
        ids_list = [] if ids is None else [int(x) for x in ids.flatten().tolist()]

        return jsonify({"ok": True, "video": dev, "found": found, "ids": ids_list, "shape": [int(frame.shape[1]), int(frame.shape[0])]})
    finally:
        try:
            cap.release()
        except Exception:
            pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, threaded=True)
