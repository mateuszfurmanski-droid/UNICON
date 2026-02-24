from flask import Blueprint, Response
import json, urllib.request

bp_op = Blueprint("unicon_op", __name__)

def _j(u):
    try:
        with urllib.request.urlopen(u, timeout=0.6) as r:
            return json.loads(r.read().decode("utf-8","ignore"))
    except Exception:
        return {}

@bp_op.route("/op")
def op():
    st = _j("http://127.0.0.1:8095/api/btn2/state")
    html = """<!doctype html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>UNICON OP</title>
<style>
body{margin:0;background:#000;color:#0f0;font-family:monospace}
.pad{padding:14px}
pre{white-space:pre-wrap}
a{color:#0f0}
</style>
</head>
<body>
<div class="pad">
<div>UNICON /op</div>
<div><a href="/">/</a> | <a href="/health">/health</a> | <a href="/api/btn2/state">/api/btn2/state</a></div>
<pre id="j"></pre>
</div>
<script>
document.getElementById("j").textContent = JSON.stringify(%s,null,2);
</script>
</body></html>""" % (json.dumps(st))
    return Response(html, mimetype="text/html")
