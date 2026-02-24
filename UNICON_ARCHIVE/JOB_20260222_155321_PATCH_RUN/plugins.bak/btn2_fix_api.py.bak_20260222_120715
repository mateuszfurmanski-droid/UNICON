import time
from flask import Blueprint, jsonify, request, current_app, make_response

bp = Blueprint("plugin_btn2_fix_api_v2", __name__, url_prefix="/api/btn2fix")

def _no_store(resp):
    try:
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
    except Exception:
        pass
    return resp

@bp.get("/state")
def state():
    vf = getattr(current_app, "view_functions", {}) or {}
    fn = vf.get("api_btn2_state")  # main endpoint name from master
    if callable(fn):
        try:
            resp = fn()
            return _no_store(resp)
        except Exception as e:
            r = make_response(jsonify({"ok": False, "err": f"proxy_state_failed:{e}", "ts": time.time()}), 200)
            return _no_store(r)
    r = make_response(jsonify({"ok": False, "err": "api_btn2_state not found", "ts": time.time()}), 200)
    return _no_store(r)

@bp.route("/<name>", methods=["GET","POST"])
def set_btn(name):
    vf = getattr(current_app, "view_functions", {}) or {}
    fn = vf.get("api_btn2")  # main endpoint name from master
    if callable(fn):
        try:
            resp = fn(name)
            return _no_store(resp)
        except Exception as e:
            r = make_response(jsonify({"ok": False, "err": f"proxy_set_failed:{e}", "ts": time.time()}), 200)
            return _no_store(r)
    r = make_response(jsonify({"ok": False, "err": "api_btn2 not found", "ts": time.time()}), 200)
    return _no_store(r)
