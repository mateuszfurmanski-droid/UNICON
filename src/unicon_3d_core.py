from flask import Blueprint, Response
import math, json

bp_3d = Blueprint("unicon_3d", __name__)

STATE = {
    "A": None,
    "B": None
}

@bp_3d.route("/api/3d/setA/<float:x>/<float:y>/<float:z>")
def setA(x,y,z):
    STATE["A"] = (x,y,z)
    return Response("OK", mimetype="text/plain")

@bp_3d.route("/api/3d/setB/<float:x>/<float:y>/<float:z>")
def setB(x,y,z):
    STATE["B"] = (x,y,z)
    return Response("OK", mimetype="text/plain")

@bp_3d.route("/api/3d/dist")
def dist():
    A = STATE["A"]
    B = STATE["B"]
    if not A or not B:
        return Response(json.dumps({"error":"A_or_B_missing"}), mimetype="application/json")
    dx = B[0]-A[0]
    dy = B[1]-A[1]
    dz = B[2]-A[2]
    d = math.sqrt(dx*dx + dy*dy + dz*dz)
    return Response(json.dumps({
        "A": A,
        "B": B,
        "distance_3d": round(d,6)
    }), mimetype="application/json")
