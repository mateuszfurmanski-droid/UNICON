from flask import Blueprint, Response
import math, json

bp_3d = Blueprint("unicon_3d", __name__)

@bp_3d.route("/api/3d/demo")
def demo_3d():
    A = (0.2, 0.3, 1.0)
    B = (0.8, 0.6, 1.2)
    dx = B[0]-A[0]
    dy = B[1]-A[1]
    dz = B[2]-A[2]
    dist = math.sqrt(dx*dx + dy*dy + dz*dz)
    return Response(json.dumps({
        "A": A,
        "B": B,
        "distance_3d_units": round(dist,4)
    }), mimetype="application/json")
