import time
from flask import jsonify

def _pick_luna_mm(g):
    """
    Tries to find an existing Luna reading in globals() without assuming exact variable names.
    Returns (mm, source_key) or (None, None).
    """
    candidates = [
        "luna_mm", "LUNA_MM", "luna_last_mm", "LUNA_LAST_MM",
        "luna_distance_mm", "LUNA_DISTANCE_MM",
        "luna_state", "LUNA_STATE",
        "last_luna_mm", "LAST_LUNA_MM",
    ]

    for k in candidates:
        if k in g:
            v = g.get(k)
            # allow dict-like (e.g., {"mm":123})
            if isinstance(v, dict):
                for kk in ("mm", "dist_mm", "distance_mm", "value_mm"):
                    if kk in v and isinstance(v[kk], (int, float)):
                        return float(v[kk]), f"{k}.{kk}"
            if isinstance(v, (int, float)):
                return float(v), k

    # heuristic: if there is an object with attribute like .mm or .distance_mm
    for k, v in list(g.items()):
        try:
            if hasattr(v, "mm") and isinstance(getattr(v, "mm"), (int, float)):
                return float(getattr(v, "mm")), f"{k}.mm"
            if hasattr(v, "distance_mm") and isinstance(getattr(v, "distance_mm"), (int, float)):
                return float(getattr(v, "distance_mm")), f"{k}.distance_mm"
        except Exception:
            pass

    return None, None

def register_tool_luna_now(app, g):
    @app.get("/api/luna/now")
    def api_luna_now():
        mm, src = _pick_luna_mm(g)
        if mm is None:
            return jsonify({
                "ok": False,
                "mm": None,
                "source": None,
                "ts": time.time(),
                "error": "no luna value found in globals() yet"
            }), 200
        return jsonify({
            "ok": True,
            "mm": mm,
            "source": src,
            "ts": time.time()
        }), 200
