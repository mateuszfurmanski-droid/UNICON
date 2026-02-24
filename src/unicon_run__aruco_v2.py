import cv2
import os
import sys
import importlib.util

TARGET = os.environ.get("UNICON_TARGET", "/home/pi/UNICON/src/cam_dual_hud_web.py")

def _load(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"spec fail for {path}")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

if __name__ == "__main__":
    m = _load(TARGET, "unicon_target_app")
    app = getattr(m, "app", None)
    if app is None:
        raise RuntimeError("target has no global 'app'")
    app.run(host="0.0.0.0", port=8095, threaded=True)

# =========================
# UNICON_ARUCO_IN_MASTER_V1
# Master is the ONLY camera owner. ArUco reads a shared frame if the master exposes one.
# Endpoints:
#   GET /api/aruco/test
#   GET /api/aruco/test?dict=DICT_4X4_50
# =========================
try:
    import time
    from typing import Any, Dict, Optional, Tuple, List

    import numpy as np  # type: ignore
    import cv2  # type: ignore
    from flask import jsonify, request  # type: ignore

    _ARUCO_DICT_MAP = {
        "DICT_4X4_50": getattr(cv2.aruco, "DICT_4X4_50", None),
        "DICT_4X4_100": getattr(cv2.aruco, "DICT_4X4_100", None),
        "DICT_5X5_50": getattr(cv2.aruco, "DICT_5X5_50", None),
        "DICT_6X6_50": getattr(cv2.aruco, "DICT_6X6_50", None),
    }

    def _unicon_try_get_shared_frame_bgr() -> Tuple[bool, str, Optional[np.ndarray]]:
        """
        Tries to obtain a BGR frame from common master globals without opening /dev/videoX.
        Returns: (ok, src, frame_bgr)
        """
        g = globals()

        # Common patterns: already a numpy BGR frame
        for k in ("LEFT_FRAME_BGR", "left_frame_bgr", "frame_left_bgr", "LAST_LEFT_BGR", "latest_left_bgr"):
            v = g.get(k, None)
            if isinstance(v, np.ndarray) and v.ndim == 3:
                return True, f"globals:{k}", v

        # Common patterns: JPEG bytes
        for k in ("LEFT_JPEG", "left_jpeg", "frame_left_jpeg", "LAST_LEFT_JPEG", "latest_left_jpeg"):
            v = g.get(k, None)
            if isinstance(v, (bytes, bytearray)) and len(v) > 64:
                arr = np.frombuffer(v, dtype=np.uint8)
                img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if img is not None:
                    return True, f"globals:{k}", img

        # Common patterns: object holding frames (dict/namespace)
        for k in ("STATE", "state", "APP_STATE", "app_state"):
            st = g.get(k, None)
            if isinstance(st, dict):
                for kk in ("left_bgr", "left_frame_bgr", "LEFT_BGR", "left_jpeg", "LEFT_JPEG"):
                    vv = st.get(kk, None)
                    if isinstance(vv, np.ndarray) and vv.ndim == 3:
                        return True, f"{k}[{kk}]", vv
                    if isinstance(vv, (bytes, bytearray)) and len(vv) > 64:
                        arr = np.frombuffer(vv, dtype=np.uint8)
                        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                        if img is not None:
                            return True, f"{k}[{kk}]", img

        return False, "no_shared_frame", None

    def _unicon_aruco_detect(frame_bgr: np.ndarray, dict_name: str) -> Dict[str, Any]:
        dconst = _ARUCO_DICT_MAP.get(dict_name) or _ARUCO_DICT_MAP.get("DICT_4X4_50")
        if not dconst:
            return {"ok": False, "err": f"dict_not_available:{dict_name}"}

        aruco_dict = cv2.aruco.getPredefinedDictionary(dconst)
        params = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(aruco_dict, params)

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = detector.detectMarkers(gray)

        out: Dict[str, Any] = {"ok": True, "dict": dict_name, "markers": 0, "ids": []}
        if ids is not None and len(ids) > 0:
            out["markers"] = int(len(ids))
            out["ids"] = [int(x) for x in ids.flatten().tolist()]
        out["h"] = int(frame_bgr.shape[0])
        out["w"] = int(frame_bgr.shape[1])
        return out

    if "app" in globals():
        @app.get("/api/aruco/test")  # type: ignore[name-defined]
        def unicon_aruco_test() -> Any:
            dict_name = (request.args.get("dict") or "DICT_4X4_50").strip()
            ok, src, frame = _unicon_try_get_shared_frame_bgr()
            if not ok or frame is None:
                return jsonify({"ok": False, "err": src})

            t0 = time.time()
            res = _unicon_aruco_detect(frame, dict_name)
            res["src"] = src
            res["ms"] = int((time.time() - t0) * 1000)
            return jsonify(res)

except Exception as _e:
    # Never break baseline if optional ArUco block fails
    try:
        print(f"[UNICON_ARUCO_IN_MASTER_V1] disabled due to error: {_e}")
    except Exception:
        pass

# ===== UNICON ARUCO V2 (isolated block) =====
try:
    import cv2
    import numpy as np
    from flask import jsonify

    _aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    _aruco_params = cv2.aruco.DetectorParameters()

    @app.route("/api/aruco/test_v2")
    def api_aruco_test_v2():
        try:
            if 'frame_right' in globals() and frame_right is not None:
                frame = frame_right.copy()
            elif 'frame_left' in globals() and frame_left is not None:
                frame = frame_left.copy()
            else:
                return jsonify({"ok": False, "err": "no_shared_frame"})

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            corners, ids, _ = cv2.aruco.detectMarkers(gray, _aruco_dict, parameters=_aruco_params)

            if ids is None:
                return jsonify({"ok": True, "markers": 0, "ids": []})

            return jsonify({
                "ok": True,
                "markers": len(ids),
                "ids": [int(x) for x in ids.flatten()]
            })
        except Exception as e:
            return jsonify({"ok": False, "err": str(e)})
except Exception:
    pass

# ===== END ARUCO V2 =====

