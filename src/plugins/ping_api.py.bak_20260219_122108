from __future__ import annotations
import time
from flask import Blueprint, jsonify

bp = Blueprint("plugin_ping_api_v1", __name__, url_prefix="/api")

@bp.get("/ping")
def ping():
    return jsonify(ok=True, plugin="ping_api", ts=time.time())
