from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np
from flask import Blueprint, jsonify, request, current_app

bp = Blueprint("stereo_depth_api", __name__, url_prefix="/api/stereo")

CALIB_PATH = Path(__file__).with_name("stereo_calib.json")


def _load_calib() -> Dict[str, Any]:
    try:
        d = json.loads(CALIB_PATH.read_text(encoding="utf-8"))
        if not isinstance(d, dict):
            return {}
        return d
    except Exception:
        return {}


def _save_calib(d: Dict[str, Any]) -> None:
    CALIB_PATH.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _get_frames() -> Tuple[Optional[np.ndarray], Optional[np.ndarray], float, float]:
    # host must provide these hooks
    get_r = current_app.config.get("GET_LAST_FRAME_BGR")
    get_l = current_app.config.get("GET_LAST_FRAME_LEFT_BGR")
    ts_r = current_app.config.get("LAST_FRAME_TS")
    ts_l = current_app.config.get("LAST_FRAME_LEFT_TS")
    if not callable(get_r) or not callable(get_l):
        return None, None, float(ts_r or 0.0), float(ts_l or 0.0)
    fr = get_r()
    fl = get_l()
    return fr, fl, float(ts_r or 0.0), float(ts_l or 0.0)


def _clamp_int(v: float, lo: int, hi: int) -> int:
    return int(max(lo, min(hi, round(v))))


def _disparity_at_point(
    left_bgr: np.ndarray,
    right_bgr: np.ndarray,
    x: int,
    y: int,
    patch_px: int,
    search_px: int,
) -> Optional[Tuple[float, int]]:
    # Match a right patch against a left strip (same y), return (disp_px, x_left_best)
    h, w = right_bgr.shape[:2]
    half = patch_px // 2

    x = _clamp_int(x, half + 1, w - half - 2)
    y = _clamp_int(y, half + 1, h - half - 2)

    # right patch
    rp = right_bgr[y - half : y + half + 1, x - half : x + half + 1]
    rp_g = cv2.cvtColor(rp, cv2.COLOR_BGR2GRAY)

    # left search window along row, only to the left (typical stereo)
    x0 = max(0, x - search_px - half - 1)
    x1 = min(w - 1, x + half + 1)
    ls = left_bgr[y - half : y + half + 1, x0:x1]
    if ls.shape[1] < rp.shape[1] + 2:
        return None
    ls_g = cv2.cvtColor(ls, cv2.COLOR_BGR2GRAY)

    # template match: left strip (image) vs right patch (template)
    res = cv2.matchTemplate(ls_g, rp_g, cv2.TM_CCOEFF_NORMED)
    _, maxv, _, maxloc = cv2.minMaxLoc(res)
    best_x_in_strip = int(maxloc[0])  # top-left in strip coords
    x_left_best = x0 + best_x_in_strip + half

    disp = float(x - x_left_best)
    return disp, x_left_best


@bp.get("/state")
def stereo_state():
    calib = _load_calib()
    fr, fl, ts_r, ts_l = _get_frames()
    ok = (fr is not None) and (fl is not None)
    return jsonify(
        ok=bool(ok),
        calib=calib,
        frame_right_ts=ts_r,
        frame_left_ts=ts_l,
        frame_right_shape=(list(fr.shape) if fr is not None else None),
        frame_left_shape=(list(fl.shape) if fl is not None else None),
    )


@bp.get("/calib")
def get_calib():
    return jsonify(ok=True, calib=_load_calib())


@bp.post("/calib")
def post_calib():
    calib = _load_calib()
    j = request.get_json(silent=True) or {}
    if not isinstance(j, dict):
        return jsonify(ok=False, err="json must be object"), 400
    for k in ["baseline_m", "fx_px", "fy_px", "cx_px", "cy_px", "search_px", "patch_px", "min_disp_px"]:
        if k in j:
            calib[k] = j[k]
    _save_calib(calib)
    return jsonify(ok=True, calib=calib)


@bp.get("/point")
def point_3d():
    # input x,y in normalized [0..1] or pixels (if px=1)
    calib = _load_calib()
    fr, fl, ts_r, ts_l = _get_frames()
    if fr is None or fl is None:
        return jsonify(ok=False, err="frames not available (missing hooks or no frames yet)"), 503

    x = request.args.get("x", type=float)
    y = request.args.get("y", type=float)
    px = request.args.get("px", default=0, type=int)  # px=1 means x,y are pixels
    if x is None or y is None:
        return jsonify(ok=False, err="need x,y"), 400

    h, w = fr.shape[:2]
    if px == 1:
        xi = int(round(x))
        yi = int(round(y))
    else:
        xi = int(round(x * (w - 1)))
        yi = int(round(y * (h - 1)))

    baseline = float(calib.get("baseline_m", 0.06))
    fx = float(calib.get("fx_px", 700.0))
    fy = float(calib.get("fy_px", fx))
    cx = float(calib.get("cx_px", w / 2))
    cy = float(calib.get("cy_px", h / 2))
    search_px = int(calib.get("search_px", 140))
    patch_px = int(calib.get("patch_px", 15))
    min_disp = float(calib.get("min_disp_px", 2))

    r = _disparity_at_point(fl, fr, xi, yi, patch_px=patch_px, search_px=search_px)
    if r is None:
        return jsonify(ok=False, err="disparity_match_failed", x=xi, y=yi), 422
    disp, x_left_best = r

    if disp < min_disp:
        return jsonify(ok=False, err="disparity_too_small", disp_px=disp, min_disp_px=min_disp), 422

    Z = (fx * baseline) / disp  # meters
    X = (xi - cx) * Z / fx
    Y = (yi - cy) * Z / fy

    return jsonify(
        ok=True,
        x_px=xi,
        y_px=yi,
        x_left_px=int(x_left_best),
        disp_px=disp,
        XYZ_m={"x": X, "y": Y, "z": Z},
        frame_right_ts=ts_r,
        frame_left_ts=ts_l,
        calib=calib,
    )


@bp.get("/ab")
def ab_distance():
    # Uses btn2fix state A,B (normalized) and returns 3D distance (meters + mm)
    calib = _load_calib()
    fr, fl, ts_r, ts_l = _get_frames()
    if fr is None or fl is None:
        return jsonify(ok=False, err="frames not available (missing hooks or no frames yet)"), 503

    # host should provide BTN2FIX_STATE hook if available; otherwise caller supplies ax,ay,bx,by
    get_btn = current_app.config.get("GET_BTN2FIX_STATE")
    st = get_btn() if callable(get_btn) else {}
    A = (st.get("A") or {})
    B = (st.get("B") or {})

    ax = request.args.get("ax", default=A.get("x"), type=float)
    ay = request.args.get("ay", default=A.get("y"), type=float)
    bx = request.args.get("bx", default=B.get("x"), type=float)
    by = request.args.get("by", default=B.get("y"), type=float)
    if ax is None or ay is None or bx is None or by is None:
        return jsonify(ok=False, err="need A and B (btn2fix state missing and no ax/ay/bx/by provided)"), 400

    h, w = fr.shape[:2]
    pts = [("A", ax, ay), ("B", bx, by)]

    baseline = float(calib.get("baseline_m", 0.06))
    fx = float(calib.get("fx_px", 700.0))
    fy = float(calib.get("fy_px", fx))
    cx = float(calib.get("cx_px", w / 2))
    cy = float(calib.get("cy_px", h / 2))
    search_px = int(calib.get("search_px", 140))
    patch_px = int(calib.get("patch_px", 15))
    min_disp = float(calib.get("min_disp_px", 2))

    out = {}
    XYZ = {}
    for name, xn, yn in pts:
        xi = int(round(xn * (w - 1)))
        yi = int(round(yn * (h - 1)))
        r = _disparity_at_point(fl, fr, xi, yi, patch_px=patch_px, search_px=search_px)
        if r is None:
            return jsonify(ok=False, err=f"{name}_disparity_match_failed", name=name, x_px=xi, y_px=yi), 422
        disp, x_left_best = r
        if disp < min_disp:
            return jsonify(ok=False, err=f"{name}_disparity_too_small", name=name, disp_px=disp, min_disp_px=min_disp), 422

        Z = (fx * baseline) / disp
        X = (xi - cx) * Z / fx
        Y = (yi - cy) * Z / fy
        XYZ[name] = (X, Y, Z)
        out[name] = {
            "x_px": xi,
            "y_px": yi,
            "x_left_px": int(x_left_best),
            "disp_px": float(disp),
            "XYZ_m": {"x": X, "y": Y, "z": Z},
        }

    Ax, Ay, Az = XYZ["A"]
    Bx, By, Bz = XYZ["B"]
    d = float(((Ax - Bx) ** 2 + (Ay - By) ** 2 + (Az - Bz) ** 2) ** 0.5)

    return jsonify(
        ok=True,
        A=out["A"],
        B=out["B"],
        dist_m=d,
        dist_mm=d * 1000.0,
        frame_right_ts=ts_r,
        frame_left_ts=ts_l,
        calib=calib,
        btn2fix_state=st,
    )
