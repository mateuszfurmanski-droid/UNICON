from flask import Flask, Response, request, redirect, jsonify, render_template_string
import cv2
import time
import json
import math
from pathlib import Path

import config as cfg
from hud_render import draw_hud, clamp

app = Flask(__name__)

# ===== tasks file =====
TASKS_PATH = Path("/home/pi/UNICON/UNICON_CORE/tasks.json")
ACTIVE_TASK_PATH = Path("/home/pi/UNICON/UNICON_CORE/active_task.json")

# If True: when you move to next task, system auto-switches tool to task["tool"]
AUTO_TOOL_FROM_TASK = True

state = {
    "pack_id": cfg.DEFAULT_PACK_ID,
    "tools": [],
    "tool_id": cfg.DEFAULT_TOOL_ID,

    "lock_required_s": 0.8,
    "lock_timer_s": 0.0,
    "locked": False,

    "shake": 0.2,
    "dist_mm": 800,

    "fps": 0.0,
    "last_t": time.time(),

    "task": None,   # currently active task dict
}

_bg_cache = {"ok": False, "img": None, "ts": 0.0}


# ---------------- JSON helpers ----------------
def read_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default

def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2))

def load_pack(pack_id: str):
    p = cfg.PACKS_DIR / f"{pack_id}.json"
    data = read_json(p, None)
    if not data or "tools" not in data:
        raise RuntimeError(f"Invalid pack: {p}")
    idx = {t["tool_id"].upper(): t for t in data["tools"]}
    return data, idx

def ensure_active_pack():
    # you didn't have active_pack.json → create it
    if not cfg.ACTIVE_PACK_PATH.exists():
        write_json(cfg.ACTIVE_PACK_PATH, {"pack_id": cfg.DEFAULT_PACK_ID})

def sync_tools_from_disk():
    ensure_active_pack()

    ap = read_json(cfg.ACTIVE_PACK_PATH, {"pack_id": cfg.DEFAULT_PACK_ID})
    pack_id = str(ap.get("pack_id", cfg.DEFAULT_PACK_ID)).lower()

    pack, idx = load_pack(pack_id)

    at = read_json(cfg.ACTIVE_TOOL_PATH, {"tool_id": cfg.DEFAULT_TOOL_ID})
    tool_id = str(at.get("tool_id", cfg.DEFAULT_TOOL_ID)).upper()

    if tool_id not in idx:
        tool_id = str(pack["tools"][0]["tool_id"]).upper()
        write_json(cfg.ACTIVE_TOOL_PATH, {"tool_id": tool_id})

    state["pack_id"] = pack_id
    state["tools"] = pack["tools"]
    state["tool_id"] = tool_id

    return pack, idx

def set_active_tool(tool_id: str):
    tool_id = str(tool_id or "").strip().upper()
    if not tool_id:
        return False, "tool_id empty"

    pack, idx = sync_tools_from_disk()
    if tool_id not in idx:
        return False, "tool not in active pack"

    write_json(cfg.ACTIVE_TOOL_PATH, {"tool_id": tool_id})
    state["tool_id"] = tool_id
    return True, "ok"


# ---------------- TASKS ----------------
def ensure_tasks_files():
    if not TASKS_PATH.exists():
        # create minimal demo file if user forgot step
        write_json(TASKS_PATH, {
            "tasks": [
                {"id": 1, "title": "Install door frame", "location": "Wall A", "tool": "LEVEL_MEASURE"},
                {"id": 2, "title": "Check vertical alignment", "location": "Door B", "tool": "PLUMB"},
                {"id": 3, "title": "Measure opening width", "location": "Window C", "tool": "DISTANCE_MEASURE"},
            ]
        })

    if not ACTIVE_TASK_PATH.exists():
        write_json(ACTIVE_TASK_PATH, {"active_task_id": 1})

def load_tasks():
    ensure_tasks_files()
    data = read_json(TASKS_PATH, {"tasks": []})
    tasks = data.get("tasks", [])
    # normalize ids as int when possible
    norm = []
    for t in tasks:
        if isinstance(t, dict) and "id" in t:
            try:
                t2 = dict(t)
                t2["id"] = int(t2["id"])
                norm.append(t2)
            except Exception:
                norm.append(t)
    return norm

def get_active_task_id():
    ensure_tasks_files()
    data = read_json(ACTIVE_TASK_PATH, {"active_task_id": 1})
    try:
        return int(data.get("active_task_id", 1))
    except Exception:
        return 1

def set_active_task_id(task_id: int):
    ensure_tasks_files()
    write_json(ACTIVE_TASK_PATH, {"active_task_id": int(task_id)})

def get_current_task():
    tasks = load_tasks()
    if not tasks:
        return None
    active_id = get_active_task_id()
    for t in tasks:
        try:
            if int(t.get("id")) == active_id:
                return t
        except Exception:
            pass
    # fallback: first task
    return tasks[0]

def next_task():
    tasks = load_tasks()
    if not tasks:
        return None

    active_id = get_active_task_id()
    ids = []
    for t in tasks:
        try:
            ids.append(int(t.get("id")))
        except Exception:
            pass
    ids = sorted(list(set(ids)))
    if not ids:
        return None

    if active_id not in ids:
        new_id = ids[0]
    else:
        i = ids.index(active_id)
        new_id = ids[(i + 1) % len(ids)]

    set_active_task_id(new_id)
    return get_current_task()

def apply_task_autotool(task):
    if not AUTO_TOOL_FROM_TASK:
        return
    if not isinstance(task, dict):
        return
    tool = str(task.get("tool", "")).strip().upper()
    if not tool:
        return
    # switch tool only if valid in current pack
    ok, _ = set_active_tool(tool)
    # if not ok, ignore silently


# ---------------- mock sensors ----------------
def update_mock(dt: float):
    t = time.time() % 6.0
    if t < 3.0:
        state["shake"] = 0.18 + 0.04 * math.sin(time.time() * 2.0)
    else:
        state["shake"] = 0.75 + 0.15 * math.sin(time.time() * 12.0)

    if state["shake"] < 0.45:
        state["dist_mm"] += 7
        if state["dist_mm"] > 2200:
            state["dist_mm"] = 600

def update_lock(dt: float):
    stable = state["shake"] < 0.35
    if stable:
        state["lock_timer_s"] += dt
    else:
        state["lock_timer_s"] -= dt * 2.5

    state["lock_timer_s"] = clamp(state["lock_timer_s"], 0.0, state["lock_required_s"])
    state["locked"] = state["lock_timer_s"] >= state["lock_required_s"]


# ---------------- background image (optional) ----------------
def get_bg_image(w, h):
    if not cfg.THEME_BG_ENABLE:
        return None
    now = time.time()
    if now - _bg_cache["ts"] < 2.0 and _bg_cache["ok"]:
        return _bg_cache["img"]

    _bg_cache["ts"] = now
    p = cfg.HUD_BG_IMAGE
    if p.exists():
        img = cv2.imread(str(p), cv2.IMREAD_COLOR)
        if img is not None:
            img = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
            _bg_cache["ok"] = True
            _bg_cache["img"] = img
            return img

    _bg_cache["ok"] = True
    _bg_cache["img"] = None
    return None


# ---------------- camera ----------------
cap = cv2.VideoCapture(cfg.CAM_INDEX, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.H)
if not cap.isOpened():
    raise RuntimeError("Camera not available (check /dev/video0).")

def gen():
    # initial sync
    sync_tools_from_disk()
    state["task"] = get_current_task()

    last_sync = time.time()

    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.05)
            continue

        now = time.time()
        dt = now - state["last_t"]
        state["last_t"] = now
        if dt <= 0:
            dt = 0.016
        state["fps"] = 0.9 * state["fps"] + 0.1 * (1.0 / dt)

        # refresh tool selection + current task periodically
        if now - last_sync > 0.5:
            try:
                sync_tools_from_disk()
                state["task"] = get_current_task()
            except Exception:
                pass
            last_sync = now

        update_mock(dt)
        update_lock(dt)

        h, w = frame.shape[:2]
        bg = get_bg_image(w, h)

        # feed task to renderer (so TASKS tool can show real text)
        render_state = dict(state)
        render_state["task"] = state["task"]

        frame = draw_hud(frame, render_state, cfg, bg_img=bg)

        ok, jpg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if ok:
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n")


# ---------------- web ----------------
PAGE = """
<html>
<head><title>UNICON HUD</title></head>
<body style="background:black;color:#0f0;font-family:monospace;">
<h3>UNICON HUD (Turbo)</h3>
<p>Version: {{ver}} | Built: {{built}}</p>

<div style="display:flex;gap:16px;align-items:flex-start;">
  <div><img src="/stream" style="border:2px solid #0f0;max-width:960px;"></div>

  <div style="min-width:360px;">
    <p><b>Active pack:</b> {{pack_id}}</p>
    <p><b>Active tool:</b> {{tool_id}}</p>

    <p><b>Pick tool</b></p>
    <form action="/tool/set" method="post">
      {% for t in tools %}
        <button name="tool_id" value="{{t['tool_id']}}">{{t['tool_id']}}</button><br><br>
      {% endfor %}
    </form>

    <hr>

    <p><b>Current task</b></p>
    <p>ID: {{task_id}}<br>
       Title: {{task_title}}<br>
       Location: {{task_loc}}<br>
       Suggested tool: {{task_tool}}</p>

    <form action="/tasks/next" method="post">
      <button>Next task</button>
    </form>

    <hr>

    <p><b>API</b></p>
    <ul>
      <li>GET /api/health</li>
      <li>GET /api/packs</li>
      <li>POST /api/tool/set</li>
      <li>GET /api/tasks/current</li>
      <li>POST /api/tasks/next</li>
      <li>POST /api/tasks/set</li>
    </ul>

    <p><b>Theme BG</b></p>
    <ul>
      <li>THEME_BG_ENABLE: {{bg_en}}</li>
      <li>HUD_BG_IMAGE: {{bg_path}}</li>
      <li>exists: {{bg_exists}}</li>
    </ul>
  </div>
</div>
</body>
</html>
"""

@app.route("/")
def index():
    sync_tools_from_disk()
    task = get_current_task() or {}
    return render_template_string(
        PAGE,
        ver=cfg.VERSION,
        built=cfg.BUILT_UTC,
        pack_id=state["pack_id"],
        tool_id=state["tool_id"],
        tools=state["tools"],
        task_id=str(task.get("id", "-")),
        task_title=str(task.get("title", "-")),
        task_loc=str(task.get("location", "-")),
        task_tool=str(task.get("tool", "-")),
        bg_en=str(cfg.THEME_BG_ENABLE),
        bg_path=str(cfg.HUD_BG_IMAGE),
        bg_exists=str(cfg.HUD_BG_IMAGE.exists())
    )

@app.route("/tool/set", methods=["POST"])
def tool_set_form():
    tool_id = (request.form.get("tool_id") or "").strip().upper()
    if tool_id:
        set_active_tool(tool_id)
    return redirect("/")

@app.route("/tasks/next", methods=["POST"])
def tasks_next_form():
    t = next_task()
    state["task"] = t
    # optional: switch to TASKS tool so user sees task
    set_active_tool("TASKS")
    # optional: auto tool from task (for next action after viewing)
    apply_task_autotool(t)
    return redirect("/")

@app.route("/stream")
def stream():
    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")


# ---------- JSON API ----------
@app.route("/api/health")
def api_health():
    sync_tools_from_disk()
    return jsonify({
        "ok": True,
        "version": cfg.VERSION,
        "built_utc": cfg.BUILT_UTC,
        "pack_id": state["pack_id"],
        "tool_id": state["tool_id"]
    })

@app.route("/api/packs")
def api_packs():
    packs = []
    if cfg.PACKS_DIR.exists():
        for p in cfg.PACKS_DIR.glob("*.json"):
            packs.append(p.stem)
    return jsonify({"packs": sorted(packs)})

@app.route("/api/tool/set", methods=["POST"])
def api_tool_set():
    if not request.is_json:
        return jsonify({"ok": False, "error": "expected JSON"}), 400
    tool_id = str(request.json.get("tool_id", "")).strip().upper()
    ok, msg = set_active_tool(tool_id)
    if not ok:
        return jsonify({"ok": False, "error": msg}), 400
    return jsonify({"ok": True, "pack_id": state["pack_id"], "tool_id": state["tool_id"]})

@app.route("/api/tasks/current", methods=["GET"])
def api_tasks_current():
    t = get_current_task()
    return jsonify({"ok": True, "task": t})

@app.route("/api/tasks/next", methods=["POST"])
def api_tasks_next():
    t = next_task()
    state["task"] = t
    if AUTO_TOOL_FROM_TASK:
        apply_task_autotool(t)
    return jsonify({"ok": True, "task": t, "active_tool": state["tool_id"]})

@app.route("/api/tasks/set", methods=["POST"])
def api_tasks_set():
    if not request.is_json:
        return jsonify({"ok": False, "error": "expected JSON"}), 400
    try:
        task_id = int(request.json.get("task_id"))
    except Exception:
        return jsonify({"ok": False, "error": "task_id required (int)"}), 400

    tasks = load_tasks()
    ids = []
    for t in tasks:
        try:
            ids.append(int(t.get("id")))
        except Exception:
            pass
    if task_id not in ids:
        return jsonify({"ok": False, "error": "task_id not found"}), 404

    set_active_task_id(task_id)
    t = get_current_task()
    state["task"] = t
    if AUTO_TOOL_FROM_TASK:
        apply_task_autotool(t)

    return jsonify({"ok": True, "task": t, "active_tool": state["tool_id"]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=cfg.PORT, threaded=True)
