#!/usr/bin/env python3
"""
UNICON v1 – HUD DEBUG (HEADLESS) + TOOL ENGINE
- Headless MJPEG HUD (browser)
- Tool packs + active tool (JSON)
- One process: HUD + API
"""

from flask import Flask, Response, request, redirect, jsonify, render_template_string
import cv2
import time
import json
import math
from pathlib import Path

# ================= VERSION (DO NOT SEARCH ANYWHERE ELSE) =================
HUD_DEBUG_VERSION = "v1.0.0"
HUD_DEBUG_BUILT_UTC = "2025-12-30 19:30Z"
# ========================================================================

app = Flask(__name__)

PORT = 8081
CAM_INDEX = 0
W, H = 640, 480

BASE = Path("/home/pi/UNICON/UNICON_CORE")
TOOLS_DIR = BASE / "tools"
PACKS_DIR = TOOLS_DIR / "packs"
ACTIVE_PACK_PATH = TOOLS_DIR / "active_pack.json"
ACTIVE_TOOL_PATH = TOOLS_DIR / "active_tool.json"

state = {
    "pack_id": "carpentry",
    "tools": [],
    "tool_id": "DISTANCE_MEASURE",
    "tool_name": "Distance Measure",

    # HOLD STEADY (mock IMU)
    "lock_required_s": 0.8,
    "lock_timer_s": 0.0,
    "locked": False,
    "shake": 0.2,
    "dist_mm": 800,
    "fps": 0.0,
    "last_t": time.time(),
}

# ---------------- helpers ----------------
def clamp(x, a, b):
    return a if x < a else b if x > b else x

def read_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default

def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2))

def load_pack(pack_id: str):
    p = PACKS_DIR / f"{pack_id}.json"
    data = read_json(p, None)
    if not data or "tools" not in data:
        raise RuntimeError(f"Invalid pack: {p}")
    idx = {t["tool_id"].upper(): t for t in data["tools"]}
    return data, idx

def sync_from_disk():
    ap = read_json(ACTIVE_PACK_PATH, {"pack_id": "carpentry"})
    pack_id = ap.get("pack_id", "carpentry").lower()
    pack, idx = load_pack(pack_id)

    at = read_json(ACTIVE_TOOL_PATH, {"tool_id": pack["tools"][0]["tool_id"]})
    tool_id = at.get("tool_id", pack["tools"][0]["tool_id"]).upper()

    if tool_id not in idx:
        tool_id = pack["tools"][0]["tool_id"].upper()
        write_json(ACTIVE_TOOL_PATH, {"tool_id": tool_id})

    state.update({
        "pack_id": pack_id,
        "tools": pack["tools"],
        "tool_id": tool_id,
        "tool_name": idx[tool_id].get("name", tool_id),
    })

# ---------------- mock sensors ----------------
def update_mock(dt):
    t = time.time() % 6.0
    state["shake"] = 0.2 if t < 3 else 0.8
    if state["shake"] < 0.45:
        state["dist_mm"] = 600 + int((time.time() * 50) % 1600)

def update_lock(dt):
    if state["shake"] < 0.35:
        state["lock_timer_s"] += dt
    else:
        state["lock_timer_s"] -= dt * 2
    state["lock_timer_s"] = clamp(state["lock_timer_s"], 0, state["lock_required_s"])
    state["locked"] = state["lock_timer_s"] >= state["lock_required_s"]

def hud_color():
    return (0,255,0) if state["locked"] else (0,255,255) if state["shake"] < 0.55 else (0,0,255)

# ---------------- camera ----------------
cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
if not cap.isOpened():
    raise RuntimeError("Camera not available")

def gen():
    sync_from_disk()
    last_sync = time.time()

    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.05)
            continue

        now = time.time()
        dt = now - state["last_t"]
        state["last_t"] = now

        if now - last_sync > 0.5:
            sync_from_disk()
            last_sync = now

        update_mock(dt)
        update_lock(dt)
        col = hud_color()
        h, w = frame.shape[:2]
        cx, cy = w//2, h//2

        # reticle
        cv2.line(frame,(cx-25,cy),(cx+25,cy),col,2)
        cv2.line(frame,(cx,cy-25),(cx,cy+25),col,2)

        # header
        cv2.putText(frame,f"UNICON {HUD_DEBUG_VERSION}",(20,30),
                    cv2.FONT_HERSHEY_SIMPLEX,0.7,col,2)
        cv2.putText(frame,f"PACK:{state['pack_id']} TOOL:{state['tool_id']}",(20,65),
                    cv2.FONT_HERSHEY_SIMPLEX,0.8,col,2)

        # lock
        msg = "LOCKED" if state["locked"] else "HOLD STEADY"
        cv2.putText(frame,msg,(20,105),
                    cv2.FONT_HERSHEY_SIMPLEX,0.8,col,2)

        # tool overlays
        if state["tool_id"] == "DISTANCE_MEASURE":
            txt = f"{state['dist_mm']} mm" if state["locked"] else "--- mm"
            cv2.putText(frame,txt,(20,150),
                        cv2.FONT_HERSHEY_SIMPLEX,1.0,col,2)

        elif state["tool_id"] == "LEVEL_MEASURE":
            cv2.line(frame,(100,cy),(w-100,cy),col,3)
            cv2.putText(frame,"LEVEL",(20,150),
                        cv2.FONT_HERSHEY_SIMPLEX,1.0,col,2)

        elif state["tool_id"] == "PLUMB":
            cv2.line(frame,(cx,100),(cx,h-100),col,3)
            cv2.putText(frame,"PLUMB",(20,150),
                        cv2.FONT_HERSHEY_SIMPLEX,1.0,col,2)

        elif state["tool_id"] == "TASKS":
            cv2.putText(frame,"TASK:",(20,150),
                        cv2.FONT_HERSHEY_SIMPLEX,1.0,col,2)
            cv2.putText(frame,"Install door frame – wall A",(20,190),
                        cv2.FONT_HERSHEY_SIMPLEX,0.8,col,2)

        ok,jpg = cv2.imencode(".jpg",frame,[int(cv2.IMWRITE_JPEG_QUALITY),80])
        if ok:
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n")

# ---------------- web ----------------
PAGE = """
<html><body style="background:black;color:#0f0;font-family:monospace;">
<h3>UNICON HUD</h3>
<img src="/stream" style="border:2px solid #0f0;"><br><br>
<form action="/tool/set" method="post">
{% for t in tools %}
<button name="tool_id" value="{{t['tool_id']}}">{{t['tool_id']}}</button><br><br>
{% endfor %}
</form>
</body></html>
"""

@app.route("/")
def index():
    sync_from_disk()
    return render_template_string(PAGE, tools=state["tools"])

@app.route("/tool/set", methods=["POST"])
def tool_set():
    tool = request.form.get("tool_id","").upper()
    write_json(ACTIVE_TOOL_PATH, {"tool_id": tool})
    return redirect("/")

@app.route("/stream")
def stream():
    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/api/health")
def api_health():
    sync_from_disk()
    return jsonify({
        "ok": True,
        "version": HUD_DEBUG_VERSION,
        "built_utc": HUD_DEBUG_BUILT_UTC,
        "pack_id": state["pack_id"],
        "tool_id": state["tool_id"]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, threaded=True)
