import cv2
import math
import time

try:
    import numpy as np
except Exception:
    np = None

# ---------- helpers ----------
def clamp(x, a, b):
    return a if x < a else b if x > b else x

def hud_color_bgr(locked: bool, shake: float):
    if locked:
        return (0, 255, 0)      # green
    if shake < 0.55:
        return (0, 255, 255)    # yellow
    return (0, 0, 255)          # red

def draw_bar(frame, x, y, w, h, ratio, col):
    ratio = clamp(ratio, 0.0, 1.0)
    cv2.rectangle(frame, (x, y), (x + w, y + h), col, 2)
    fw = int(w * ratio)
    cv2.rectangle(frame, (x, y), (x + fw, y + h), col, -1)

# ---------- theme ----------
_vig_cache = {"w": 0, "h": 0, "mask": None}

def _vignette_mask(w, h):
    if np is None:
        return None
    if _vig_cache["w"] == w and _vig_cache["h"] == h and _vig_cache["mask"] is not None:
        return _vig_cache["mask"]
    x = np.linspace(-1, 1, w)
    y = np.linspace(-1, 1, h)
    xx, yy = np.meshgrid(x, y)
    r = np.sqrt(xx * xx + yy * yy)
    mask = 1.0 - (r * 0.35)
    mask = np.clip(mask, 0.65, 1.0)
    mask = np.dstack([mask, mask, mask])
    _vig_cache.update({"w": w, "h": h, "mask": mask})
    return mask

def apply_theme(frame, col, theme_cfg, bg_img=None):
    if not theme_cfg["enable"]:
        return frame

    h, w = frame.shape[:2]

    if theme_cfg["bg_enable"] and bg_img is not None:
        frame = cv2.addWeighted(frame, 1.0 - theme_cfg["bg_alpha"], bg_img, theme_cfg["bg_alpha"], 0)

    # glow
    blur = cv2.GaussianBlur(frame, (0, 0), 3)
    frame = cv2.addWeighted(frame, 0.85, blur, 0.15, 0)

    # grid
    if theme_cfg["grid_enable"]:
        step = 40
        for x in range(0, w, step):
            cv2.line(frame, (x, 0), (x, h), col, 1)
        for y in range(0, h, step):
            cv2.line(frame, (0, y), (w, y), col, 1)

    # vignette
    if theme_cfg["vignette_enable"]:
        mask = _vignette_mask(w, h)
        if mask is not None:
            frame = (frame * mask).astype("uint8")

    return frame

# ---------- overlays ----------
def draw_hud(frame, state, cfg, bg_img=None):
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2

    col = hud_color_bgr(state["locked"], state["shake"])

    theme_cfg = {
        "enable": cfg.THEME_ENABLE,
        "bg_enable": cfg.THEME_BG_ENABLE,
        "bg_alpha": cfg.THEME_BG_ALPHA,
        "grid_enable": cfg.THEME_GRID_ENABLE,
        "vignette_enable": cfg.THEME_VIGNETTE_ENABLE,
    }
    frame = apply_theme(frame, col, theme_cfg, bg_img=bg_img)

    # reticle
    cv2.line(frame, (cx - 25, cy), (cx + 25, cy), col, 2)
    cv2.line(frame, (cx, cy - 25), (cx, cy + 25), col, 2)
    cv2.circle(frame, (cx, cy), 4, col, 2)

    # header
    cv2.putText(frame, f"UNICON {cfg.VERSION}", (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, col, 2)
    cv2.putText(frame, f"PACK: {state['pack_id']}  TOOL: {state['tool_id']}", (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.85, col, 2)

    # lock bar
    ratio = state["lock_timer_s"] / state["lock_required_s"] if state["lock_required_s"] else 1.0
    draw_bar(frame, 20, 85, 220, 18, ratio, col)
    msg = "LOCKED" if state["locked"] else f"HOLD STEADY... {state['lock_required_s']-state['lock_timer_s']:.1f}s"
    cv2.putText(frame, msg, (260, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.75, col, 2)

    # tool overlays
    tool = state["tool_id"]

    if tool == "DISTANCE_MEASURE":
        if state["locked"]:
            cv2.putText(frame, f"DIST: {state['dist_mm']:4d} mm  [VALID]", (20, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.95, col, 2)
        else:
            cv2.putText(frame, "DIST: ---- mm  [HOLD STEADY]", (20, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.95, col, 2)

    elif tool == "LEVEL_MEASURE":
        offset = int((state["shake"] - 0.5) * 60)
        cv2.line(frame, (100, cy + offset), (w - 100, cy - offset), col, 3)
        cv2.putText(frame, "LEVEL", (20, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.95, col, 2)

    elif tool == "PLUMB":
        offset = int((state["shake"] - 0.5) * 60)
        cv2.line(frame, (cx + offset, 100), (cx - offset, h - 100), col, 3)
        cv2.putText(frame, "PLUMB", (20, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.95, col, 2)

    elif tool == "TASKS":
        cv2.putText(frame, "TASK:", (20, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.95, col, 2)
        cv2.putText(frame, "Install door frame – wall A", (20, 190),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, col, 2)

    else:
        cv2.putText(frame, f"{tool} (no overlay)", (20, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.95, col, 2)

    cv2.putText(frame, f"SHAKE: {state['shake']:.2f}  FPS: {state['fps']:.1f}", (20, 230),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2)

    return frame
