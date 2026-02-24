import cv2
import numpy as np
from flask import Blueprint, jsonify, request

bp_world = Blueprint("unicon_world", __name__)

DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
PARAMS = cv2.aruco.DetectorParameters()

@bp_world.route("/api/world/aruco_test")
def aruco_test():
    return jsonify({"ok": True, "aruco": True, "dict": "DICT_4X4_50"})

@bp_world.route("/api/world/aruco_detect")
def aruco_detect():
    # expects: /api/world/aruco_detect?img=/home/pi/snap.jpg
    img_path = request.args.get("img", "")
    if not img_path:
        return jsonify({"ok": False, "err": "missing img=PATH"}), 400
    img = cv2.imread(img_path)
    if img is None:
        return jsonify({"ok": False, "err": "cannot read image", "img": img_path}), 400
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    detector = cv2.aruco.ArucoDetector(DICT, PARAMS)
    corners, ids, _ = detector.detectMarkers(gray)
    ids_list = [] if ids is None else [int(x) for x in ids.flatten().tolist()]
    return jsonify({"ok": True, "markers": len(ids_list), "ids": ids_list})
