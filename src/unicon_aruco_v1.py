import cv2
from flask import jsonify

_ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
_ARUCO_PARAMS = cv2.aruco.DetectorParameters()

def register(app, get_frame_fn):
    @app.get("/api/aruco/state_v1")
    def aruco_state_v1():
        ok_frame = False
        try:
            f = get_frame_fn()
            ok_frame = (f is not None and getattr(f, "size", 0) > 0)
        except Exception:
            ok_frame = False
        return jsonify({
            "ok": True,
            "has_cv2": True,
            "has_aruco": hasattr(cv2, "aruco"),
            "frame_available": ok_frame
        })

    @app.get("/api/aruco/test_v1")
    def aruco_test_v1():
        frame = None
        try:
            frame = get_frame_fn()
        except Exception:
            frame = None

        if frame is None or getattr(frame, "size", 0) == 0:
            return jsonify({"ok": False, "err": "no_frame_available"}), 503

        if getattr(frame, "ndim", 0) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        corners, ids, _ = cv2.aruco.detectMarkers(gray, _ARUCO_DICT, parameters=_ARUCO_PARAMS)
        ids_list = [] if ids is None else [int(x) for x in ids.flatten().tolist()]
        return jsonify({"ok": True, "markers": len(ids_list), "ids": ids_list})
