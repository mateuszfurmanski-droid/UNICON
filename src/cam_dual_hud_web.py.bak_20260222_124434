# UNICON_PATH_FIX_V1
import os, sys

# ===== UNICON FRAME TAP (for ArUco, in-process; no HTTP self-call) =====
import threading
LAST_FRAME_BGR = None
LAST_FRAME_LOCK = threading.Lock()

def unicon_get_last_frame_bgr():
    global LAST_FRAME_BGR
    with LAST_FRAME_LOCK:
        if LAST_FRAME_BGR is None:
            return None
        try:
            return LAST_FRAME_BGR.copy()
        except Exception:
            return LAST_FRAME_BGR
# ================================================================

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

#!/usr/bin/env python3
import os



# --- ARUCO OVERLAY (V1) ---
from aruco_draw_v1 import ArucoOverlay
ARUCO_OVL = ArucoOverlay(dict_name="DICT_4X4_50", ttl=0.25)
# --- /ARUCO OVERLAY (V1) ---

# --- RULER_PX_STATE (V1) ---
RULER_PX_STATE = {
    "mode": None,     # "A" or "B" when armed (UI uses this)
    "A": None,        # (x_norm, y_norm) 0..1
    "B": None,        # (x_norm, y_norm) 0..1
    "ts": None
}
import threading
RULER_LOCK = threading.Lock()

def _clamp01(v: float) -> float:
    try:
        v = float(v)
    except Exception:
        return 0.5
    if v < 0.0: return 0.0
    if v > 1.0: return 1.0
    return v

def _norm_to_px(pt, w: int, h: int):
    x = int(_clamp01(pt[0]) * w)
    y = int(_clamp01(pt[1]) * h)
    return (x, y)

LAST_CLICK = None

import time
import threading
from typing import Optional, Tuple

import cv2
from flask import Flask, Response, jsonify, redirect, request

# --- UNICON_MODULES_IMPORT_V1 ---
try:
    from tools.ruler_ab import ruler_bp, draw_ruler_overlay
except Exception:
    ruler_bp = None
    def draw_ruler_overlay(frame):
        return
# --- end ---

APP_NAME = "cam_dual_hud_web"
PORT = int(os.environ.get("UNICON_PORT", "8095"))

# LOCKED BASELINE (UNICON V0):
# RIGHT camera is VIEW/HUD stream (MJPEG for humans)
# LEFT camera is MEASURE-only using RAW/YUYV for computation
VIDEO_RIGHT = os.environ.get("UNICON_VIDEO_RIGHT", "/dev/video2")
VIDEO_LEFT  = os.environ.get("UNICON_VIDEO_LEFT",  "/dev/video0")

app = Flask(APP_NAME)


# --- UNICON_PLUGIN_LOADER_V1 (AUTOMAT) ---

import json, os, importlib.util


def _unicon_load_plugins(app):

    base = os.path.join(os.path.dirname(__file__), "plugins")

    man = os.path.join(base, "manifest.json")

    if not os.path.exists(man):

        return

    try:

        with open(man, "r", encoding="utf-8") as f:

            data = json.load(f)

    except Exception as e:

        print(f"PLUGIN_MANIFEST_READ_FAIL: {e}")

        return

    enabled = data.get("enabled", [])

    if not isinstance(enabled, list):

        return

    for fname in enabled:

        if not isinstance(fname, str) or not fname.endswith(".py"):

            continue

        fpath = os.path.join(base, fname)

        if not os.path.exists(fpath):

            print(f"PLUGIN_MISSING: {fname}")

            continue

        mod_name = "unicon_plugin_" + fname.replace(".", "_")

        try:

            spec = importlib.util.spec_from_file_location(mod_name, fpath)

            if spec is None or spec.loader is None:

                print(f"PLUGIN_SPEC_FAIL: {fname}")

                continue

            mod = importlib.util.module_from_spec(spec)

            spec.loader.exec_module(mod)

            bp = getattr(mod, "bp", None)

            if bp is None:

                print(f"PLUGIN_NO_BP: {fname}")

                continue

            app.register_blueprint(bp)

            print(f"PLUGIN_OK: {fname}")

        except Exception as e:

            print(f"PLUGIN_FAIL: {fname}: {e}")


_unicon_load_plugins(app)

app.config["UNICON_FRAME_PROVIDER"] = unicon_get_last_frame_bgr

from aruco_api_v1 import aruco_bp
app.register_blueprint(aruco_bp)

# --- UNICON_REGISTER_RULER_BP_V1 ---
if ruler_bp is not None:
    app.register_blueprint(ruler_bp)
# --- end ---


@app.after_request
def _unicon_no_cache(resp):
    try:
        ct = (resp.headers.get("Content-Type") or "").lower()
        # Only force no-store for HTML pages (so phone doesn't cache old UI)
        if "text/html" in ct:
            resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
    except Exception:
        pass
    return resp

# === UNICON_RULER_V1 (tap->A/B + draw line) ===
P_A = None  # (x_norm, y_norm)
P_B = None  # (x_norm, y_norm)
STATE_LOCK = threading.Lock()

def _clamp01(v):
    try:
        v = float(v)
    except Exception:
        return None
    if v < 0.0: v = 0.0
    if v > 1.0: v = 1.0
    return v

def _get_xy_from_request(request):
    # expects ?x=0..1&y=0..1 (normalized coords from client tap)
    x = _clamp01(request.args.get("x", None))
    y = _clamp01(request.args.get("y", None))
    if x is None or y is None:
        return 0.5, 0.5
    return x, y
# === /UNICON_RULER_V1 ===
_lock = threading.RLock()
_cap_right: Optional[cv2.VideoCapture] = None
_cap_left: Optional[cv2.VideoCapture] = None
_last_err: str = ""
_status = {
    "ok": True,
    "right_open": False,
    "left_open": False,
    "right_dev": VIDEO_RIGHT,
    "left_dev": VIDEO_LEFT,
    "port": PORT,
    "last_err": "",
}

def _set_err(msg: str) -> None:
    global _last_err
    _last_err = msg
    _status["last_err"] = msg

def _open_cap(dev: str, for_view: bool) -> Tuple[Optional[cv2.VideoCapture], str]:
    # CAP_V4L2 helps on Pi
    cap = cv2.VideoCapture(dev, cv2.CAP_V4L2)
    if not cap.isOpened():
        return None, f"VideoCapture open failed: {dev}"

    # Minimal sane defaults (don’t fight driver too hard)
    # Right (view): allow default; Left (measure): try YUYV if possible
    try:
        if not for_view:
            # Try force YUYV (raw-ish); if unsupported driver will ignore
            fourcc = cv2.VideoWriter_fourcc(*"YUYV")
            cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    except Exception:
        pass

    return cap, ""

def init_cameras() -> None:
    global _cap_right, _cap_left
    with _lock:
        # RIGHT
        if _cap_right is None or not _cap_right.isOpened():
            cap, err = _open_cap(VIDEO_RIGHT, for_view=True)
            _cap_right = cap
            _status["right_open"] = bool(cap and cap.isOpened())
            if err:
                _set_err(err)

        # LEFT
        if _cap_left is None or not _cap_left.isOpened():
            cap, err = _open_cap(VIDEO_LEFT, for_view=False)
            _cap_left = cap
            _status["left_open"] = bool(cap and cap.isOpened())
            if err:
                _set_err(err)

def _ensure_right() -> cv2.VideoCapture:
    global _cap_right
    with _lock:
        if _cap_right is None or not _cap_right.isOpened():
            init_cameras()
        if _cap_right is None or not _cap_right.isOpened():
            raise RuntimeError(f"RIGHT camera not available: {VIDEO_RIGHT} :: {_last_err}")
        return _cap_right

def _ensure_left() -> cv2.VideoCapture:
    global _cap_left
    with _lock:
        if _cap_left is None or not _cap_left.isOpened():
            init_cameras()
        if _cap_left is None or not _cap_left.isOpened():
            raise RuntimeError(f"LEFT camera not available: {VIDEO_LEFT} :: {_last_err}")
        return _cap_left

def _jpeg_bytes(frame) -> Optional[bytes]:
    # UNICON DBG: show BTN2 state + draw AB line/circles (if present)
    try:
        st = globals().get("BTN2_STATE")
        if not isinstance(st, dict):
            st = {}

        A = st.get("A") if isinstance(st.get("A"), dict) else None
        B = st.get("B") if isinstance(st.get("B"), dict) else None

        h, w = frame.shape[:2]

        def _f(v):
            try:
                return float(v)
            except Exception:
                return None

        axn = _f(A.get("x")) if A else None
        ayn = _f(A.get("y")) if A else None
        bxn = _f(B.get("x")) if B else None
        byn = _f(B.get("y")) if B else None

        # Always draw a visible debug banner so we KNOW this function is running on the served frames
        dbg = f"DBG _jpeg_bytes ON | {w}x{h} | A={axn},{ayn} | B={bxn},{byn}"
        try:
            cv2.rectangle(frame, (0, 0), (w, 28), (0, 0, 0), -1)
            cv2.putText(frame, dbg[:120], (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
        except Exception:
            pass

        if axn is not None and ayn is not None and bxn is not None and byn is not None:
            ax = int(max(0, min(w - 1, axn * w)))
            ay = int(max(0, min(h - 1, ayn * h)))
            bx = int(max(0, min(w - 1, bxn * w)))
            by = int(max(0, min(h - 1, byn * h)))

            cv2.line(frame, (ax, ay), (bx, by), (0, 255, 0), 2, cv2.LINE_AA)
            cv2.circle(frame, (ax, ay), 6, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.circle(frame, (bx, by), 6, (0, 255, 0), 2, cv2.LINE_AA)

            dist_px = ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
            txt = f"AB px: {dist_px:.1f}"
            cv2.rectangle(frame, (0, 28), (220, 56), (0, 0, 0), -1)
            cv2.putText(frame, txt, (8, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)

    except Exception:
        pass

    # --- UNICON_DRAW_RULER_OVERLAY_V1 ---


    try:


        draw_ruler_overlay(frame)


    except Exception:


        pass


    # --- end ---


    ARUCO_OVL.draw_inplace(frame)


    # UNICON: tap latest frame for ArUco (BGR) after assignment
    try:
        global LAST_FRAME_BGR
        with LAST_FRAME_LOCK:
            LAST_FRAME_BGR = frame
    except Exception:
        pass
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if not ok:
        return None
    return buf.tobytes()

def mjpeg_stream(cap_getter, label: str):
    boundary = b"--frame\r\n"
    while True:
        try:
            cap = cap_getter()
            ok, frame = cap.read()
            if not ok or frame is None:
                # Try reopen once, then continue
                with _lock:
                    if label == "right":
                        try:
                            if _cap_right is not None:
                                _cap_right.release()
                        except Exception:
                            pass
                        _cap_right = None
                        _status["right_open"] = False
                    else:
                        try:
                            if _cap_left is not None:
                                _cap_left.release()
                        except Exception:
                            pass
                        _cap_left = None
                        _status["left_open"] = False
                init_cameras()
                time.sleep(0.05)
                continue

            globals()["LAST_FRAME_RIGHT"] = frame

            jb = _jpeg_bytes(frame)
            if jb is None:
                time.sleep(0.01)
                continue

            yield boundary
            yield b"Content-Type: image/jpeg\r\n"
            yield f"X-UNICON-CAM: {label}\r\n".encode("utf-8")
            yield f"Content-Length: {len(jb)}\r\n\r\n".encode("utf-8")
            yield jb
            yield b"\r\n"
        except GeneratorExit:
            return
        except Exception as e:
            _set_err(f"{label} stream error: {e}")
            time.sleep(0.1)

@app.route("/health")
def health():
    init_cameras()
    return jsonify({
        "ok": True,
        "app": APP_NAME,
        **_status,
        "client": request.remote_addr,
    })

@app.route("/")
def index():
    html = """<!doctype html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>UNICON HUD</title>
  <style>
    body { margin:0; background:#000; color:#0f0; font-family: monospace; }
    #controls { position: fixed; top: 10px; left: 10px; right: 10px; z-index: 9999; display:flex; gap:10px; }
    .btn { flex:1; padding:18px 12px; font-size:22px; border-radius:18px; border:1px solid #0a0;
           background:#061; color:#0f0; text-align:center; user-select:none; -webkit-user-select:none; }
    #wrap { padding:70px 12px 12px; }
    #stage { position: relative; width: 100%; }
    #cam { width:100%; height:auto; display:block; background:#000; }
    #tapLayer { position:absolute; left:0; top:0; right:0; bottom:0; cursor: crosshair; }
    .cross { position:absolute; width:18px; height:18px; margin-left:-9px; margin-top:-9px; border:2px solid #0f0; border-radius:999px; pointer-events:none; }
    #hud { opacity:0.92; line-height:1.25; margin-top:10px; font-size:14px; }
    a { color:#0f0; }
  </style>
</head>
<body>
  <div id="controls">
    <div class="btn" id="btnA">SET A</div>
    <div class="btn" id="btnB">SET B</div>
    <div class="btn" id="btnR">RESET</div>
  </div>

  <div id="wrap">
    <div id="stage">
      <img id="cam" src="/cam.mjpg" />
      <div id="tapLayer"></div>
      <div id="crossA" class="cross" style="display:none;"></div>
      <div id="crossB" class="cross" style="display:none;"></div>
    </div>

    <div id="hud">
      MODE: <span id="mode">A</span> |
      A=<span id="A">?</span> |
      B=<span id="B">?</span>
      <div style="margin-top:6px;">
        <a href="/health">/health</a> |
        <a href="/_i/btn2fix/state">/_i/btn2fix/state</a>
      </div>
    </div>
  </div>

<script>
let mode = 'A';

function setMode(m){
  mode = m;
  document.getElementById('mode').textContent = mode;
}

document.getElementById('btnA').onclick = ()=>setMode('A');
document.getElementById('btnB').onclick = ()=>setMode('B');
document.getElementById('btnR').onclick = ()=>{
  fetch('/_i/btn2fix/RESET').catch(()=>0);
  document.getElementById('crossA').style.display='none';
  document.getElementById('crossB').style.display='none';
};

function placeCross(id, nx, ny){
  const stage = document.getElementById('stage');
  const r = stage.getBoundingClientRect();
  const x = nx * r.width;
  const y = ny * r.height;
  const el = document.getElementById(id);
  el.style.left = x + 'px';
  el.style.top  = y + 'px';
  el.style.display = 'block';
}

document.getElementById('tapLayer').addEventListener('click', (ev)=>{
  const stage = document.getElementById('stage');
  const r = stage.getBoundingClientRect();
  const nx = (ev.clientX - r.left) / r.width;
  const ny = (ev.clientY - r.top)  / r.height;

  const x = Math.max(0, Math.min(1, nx)).toFixed(4);
  const y = Math.max(0, Math.min(1, ny)).toFixed(4);

  if(mode === 'A'){
    fetch(`/_i/btn2fix/A?x=${x}&y=${y}`).catch(()=>0);
    placeCross('crossA', parseFloat(x), parseFloat(y));
  } else {
    fetch(`/_i/btn2fix/B?x=${x}&y=${y}`).catch(()=>0);
    placeCross('crossB', parseFloat(x), parseFloat(y));
  }
});

async function poll(){
  try{
    const r = await fetch('/_i/btn2fix/state', {cache:'no-store'});
    const j = await r.json();
    document.getElementById('A').textContent = (j.A && j.A.x!=null) ? `${j.A.x.toFixed(3)},${j.A.y.toFixed(3)}` : 'None';
    document.getElementById('B').textContent = (j.B && j.B.x!=null) ? `${j.B.x.toFixed(3)},${j.B.y.toFixed(3)}` : 'None';
  }catch(e){}
  setTimeout(poll, 700);
}
poll();
</script>

</body>
</html>"""
    return Response(html, mimetype="text/html")
# --- Aliases / Compatibility ---
@app.route("/cam")
def cam_alias():
    return redirect("/cam.mjpg", code=302)

@app.route("/cam2")
def cam2_alias():
    return redirect("/cam2.mjpg", code=302)

@app.route("/cam.mjpg")
def cam_mjpg():
    init_cameras()
    return Response(mjpeg_stream(_ensure_right, "right"),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/cam2.mjpg")
def cam2_mjpg():
    init_cameras()
    return Response(mjpeg_stream(_ensure_left, "left"),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/mjpeg/right")
def mjpeg_right():
    return redirect("/cam.mjpg", code=302)

@app.route("/mjpeg/left")
def mjpeg_left():
    return redirect("/cam2.mjpg", code=302)

# Button endpoint (keeps your UI from erroring)
@app.route("/_i/btn/<name>")
def api_btn(name):

    # UNICON_FIX_BTN_STATE_GUARD
    # Some UIs call /_i/btn2fix/state (GET) without btn_name in view args.
    try:
        btn_name = locals().get('btn_name', None)
    except Exception:
        btn_name = None
    if btn_name is None:
        try:
            btn_name = (getattr(request, "view_args", None) or {}).get("btn_name")
        except Exception:
            btn_name = None

    # If this is the state endpoint (btn_name missing or equals 'state'), return current state safely.
    if btn_name in (None, "state", "STATE"):
        try:
            # Try common globals used in this file; fall back to empty.
            st = {}
            if "BTN_STATE" in globals():
                st = globals().get("BTN_STATE") or {}
            elif "BUTTON_STATE" in globals():
                st = globals().get("BUTTON_STATE") or {}
            return jsonify({"ok": True, "state": st, "ts": time.time()})
        except Exception as e:
            return jsonify({"ok": False, "err": str(e), "ts": time.time()}), 200
    # RULER PX: accept optional x,y and store for A/B/RESET
    x = request.args.get('x', None)
    y = request.args.get('y', None)
    try:
        xn = float(x) if x is not None else None
        yn = float(y) if y is not None else None
    except Exception:
        xn = None
        yn = None
    with RULER_LOCK:
        if btn_name in ('A','B') and xn is not None and yn is not None:
            RULER_PX_STATE[btn_name] = (_clamp01(xn), _clamp01(yn))
            RULER_PX_STATE['ts'] = time.time() if 'time' in globals() else None
        if btn_name == 'RESET':
            RULER_PX_STATE['A'] = None
            RULER_PX_STATE['B'] = None
            RULER_PX_STATE['mode'] = None
    return jsonify({"ok": True, "btn": name, "ts": time.time()})

def main():
    init_cameras()
    # Flask dev server (OK for V0)
    
try:
    from unicon_3d_ui import bp_3d
    if "unicon_3d" not in app.blueprints:
        if "unicon_3d" not in app.blueprints:

            if "unicon_3d" not in app.blueprints:

                app.register_blueprint(bp_3d)
except Exception as e:
    pass
# DISABLED_BY_UNICON_RUNNER app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)

# =========================
# UNICON BTN2 (safe endpoints)
# =========================
try:
    _BTN2_STATE
except NameError:
    _BTN2_STATE = {"last": None, "A": None, "B": None, "reset": 0}

def _btn2_set(name: str, xn=None, yn=None):
    global _BTN2_STATE
    _BTN2_STATE["last"] = name
    if name in ("A","B") and xn is not None and yn is not None:
        _BTN2_STATE[name] = {"x": float(xn), "y": float(yn)}
    if name == "RESET":
        _BTN2_STATE["A"] = None
        _BTN2_STATE["B"] = None
        _BTN2_STATE["reset"] = int(_BTN2_STATE.get("reset", 0)) + 1

@app.route("/_i/btn2/<name>", methods=["GET","POST"])
def api_btn2(name):
    name = (name or "").upper()
    if name not in ("A","B","RESET"):
        return jsonify({"ok": False, "err": "bad name", "name": name}), 400
    xn = request.args.get("x", None)
    yn = request.args.get("y", None)
    try:
        xn = float(xn) if xn is not None else None
        yn = float(yn) if yn is not None else None
    except Exception:
        xn = None
        yn = None
    _btn2_set(name, xn, yn)
    return jsonify({"ok": True, "btn": name, "state": _BTN2_STATE})

@app.route("/_i/btn2fix/state", methods=["GET"])
def api_btn2_state():
    return jsonify({"ok": True, "state": _BTN2_STATE})



# --- UNICON WORLD ARUCO MODULE (V1) ---
try:
    from unicon_world_aruco import bp_world
    # give module access to main globals (frames/state) without editing its code
    app.config["__UNICON_MAIN_GLOBALS__"] = globals()
    app.register_blueprint(bp_world)
except Exception as e:
    pass
if __name__ == "__main__":
    main()


# --- UNICON CLICK DEBUG (V1) ---
from flask import request, jsonify
import math

@app.route("/api/click", methods=["POST"])
def api_click():
    global LAST_CLICK
    try:
        data = request.get_json(silent=True) or {}
    except Exception:
        data = {}
    LAST_CLICK = data
    try:
        x = data.get("x"); y = data.get("y")
        w = data.get("w"); h = data.get("h")
        print(f"[CLICK] x={x} y={y} w={w} h={h} raw={data}", flush=True)
    except Exception:
        print(f"[CLICK] raw={data}", flush=True)

    # Optional: if project already has a click handler, try calling it safely
    for fname in ("handle_click", "on_click", "process_click", "register_click", "add_click_point"):
        fn = globals().get(fname)
        if callable(fn):
            try:
                fn(data)
                break
            except Exception as e:
                print(f"[CLICK] handler {fname} failed: {e}", flush=True)

    return jsonify(ok=True, got=True)



# UNICON_MODULES_LOADER_V1
# Safe: loads extra endpoints from ./modules if present.
try:
    import os
    _mods = os.path.join(os.path.dirname(__file__), "modules")
    if os.path.isdir(_mods):
        from modules.tool_luna_now import register_tool_luna_now
        register_tool_luna_now(app, globals())
except Exception:
    pass
try:
    from unicon_3d_overlay import bp_3d
    if "unicon_3d" not in app.blueprints:
        if "unicon_3d" not in app.blueprints:

            if "unicon_3d" not in app.blueprints:

                app.register_blueprint(bp_3d)
except Exception as e:
    pass
try:
    from unicon_3d_core import bp_3d
    if "unicon_3d" not in app.blueprints:
        if "unicon_3d" not in app.blueprints:

            if "unicon_3d" not in app.blueprints:

                app.register_blueprint(bp_3d)
except Exception as e:
    pass
try:
    from unicon_op_ui import bp_op
    app.register_blueprint(bp_op)
except Exception as e:
    print("OP UI load failed:", e)
