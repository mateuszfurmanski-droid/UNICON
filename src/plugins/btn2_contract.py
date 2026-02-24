from flask import Blueprint, current_app

bp = Blueprint("plugin_btn2_contract_v3", __name__)

def _pick_endpoints(app):
    # Prefer INTERNAL (_i) ruler endpoints; fall back to legacy (/api/btn2).
    state_ep = None
    set_ep = None
    dbg = []

    for r in app.url_map.iter_rules():
        rule = (getattr(r, "rule", "") or "").strip()
        ep = getattr(r, "endpoint", None)
        if not rule or not ep:
            continue

        # ignore btn2fix
        if "/btn2fix" in rule:
            continue

        # collect small debug sample for first bind attempt
        if "/btn2" in rule and len(dbg) < 12:
            dbg.append((rule, ep))

        # strict preferred targets
        if rule in ("/_i/btn2/state", "/_i/btn2/state/"):
            state_ep = ep
        if rule in ("/_i/btn2/<name>", "/_i/btn2/<name>/"):
            set_ep = ep

    # heuristic fallback (covers converter variants)
    if state_ep is None:
        for r in app.url_map.iter_rules():
            rule = (getattr(r, "rule", "") or "").strip()
            if "/btn2fix" in rule:
                continue
            if rule.endswith("/btn2/state") or rule.endswith("/btn2/state/"):
                # prefer internal if present, else whatever matches
                if rule.startswith("/_i/"):
                    state_ep = r.endpoint
                    break
                state_ep = state_ep or r.endpoint

    if set_ep is None:
        for r in app.url_map.iter_rules():
            rule = (getattr(r, "rule", "") or "").strip()
            if "/btn2fix" in rule:
                continue
            if "/btn2/" in rule and "<" in rule and ">" in rule:
                if rule.startswith("/_i/") and rule.endswith(">"):
                    set_ep = r.endpoint
                    break
                set_ep = set_ep or r.endpoint

    return state_ep, set_ep, dbg

def _scan_and_bind(app):
    state_ep, set_ep, dbg = _pick_endpoints(app)

    if state_ep and state_ep in app.view_functions:
        app.config["BTN2_STATE_FN"] = app.view_functions[state_ep]
    if set_ep and set_ep in app.view_functions:
        app.config["BTN2_SET_FN"] = app.view_functions[set_ep]

    ok_state = bool(app.config.get("BTN2_STATE_FN"))
    ok_set = bool(app.config.get("BTN2_SET_FN"))
    return ok_state, ok_set, state_ep, set_ep, dbg

@bp.record_once
def _bind_once(state):
    app = state.app
    ok_state, ok_set, state_ep, set_ep, dbg = _scan_and_bind(app)
    print("BTN2_CONTRACT_BIND_V3_ONCE", ok_state, ok_set, "state_ep=", state_ep, "set_ep=", set_ep, "dbg=", dbg)

@bp.before_app_request
def _bind_lazy():
    app = current_app
    if app.config.get("BTN2_STATE_FN") and app.config.get("BTN2_SET_FN"):
        return
    ok_state, ok_set, state_ep, set_ep, _dbg = _scan_and_bind(app)
    if ok_state or ok_set:
        print("BTN2_CONTRACT_BIND_V3_LAZY", ok_state, ok_set, "state_ep=", state_ep, "set_ep=", set_ep)
