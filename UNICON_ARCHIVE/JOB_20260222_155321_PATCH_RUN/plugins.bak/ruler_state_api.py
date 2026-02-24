from flask import Blueprint, current_app, jsonify

bp = Blueprint("plugin_ruler_state_api_v4", __name__)

_STATE_EP = None
_TRIED = False

def _bind_once(app):
    global _STATE_EP, _TRIED
    if _TRIED:
        return
    _TRIED = True
    try:
        for r in app.url_map.iter_rules():
            rule = getattr(r, "rule", "") or ""
            if rule == "/api/btn2fix/state":
                _STATE_EP = getattr(r, "endpoint", None)
                break
    except Exception:
        _STATE_EP = None

def _call_btn2fix_state():
    _bind_once(current_app)
    if not _STATE_EP:
        return jsonify(ok=False, error="btn2fix_state_endpoint_not_found"), 500
    fn = current_app.view_functions.get(_STATE_EP)
    if not fn:
        return jsonify(ok=False, error="btn2fix_state_view_fn_missing"), 500
    return fn()

@bp.get("/ruler/state")
def ruler_state():
    return _call_btn2fix_state()

# If loader does NOT add /api prefix, this guarantees the exact path exists too.
@bp.get("/api/ruler/state")
def api_ruler_state():
    return _call_btn2fix_state()
