from flask import Blueprint, jsonify, request

bp = Blueprint("plugin_guard_internal_btn2_v2", __name__)

@bp.before_app_request
def _guard_internal_paths():
    p = request.path or ""
    if p.startswith("/_i/btn2/") or p.startswith("/_i/btn/"):
        return (
            jsonify(
                ok=False,
                error="internal_route_retired",
                path=p,
                client=request.remote_addr,
            ),
            410,
        )
    return None
