#!/usr/bin/env python3
from flask import Flask, send_file, make_response
import time, os

app = Flask(__name__)

@app.get("/")
def index():
    return """
<!doctype html>
<html>
<head>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>UNICON – Stereo</title>
<style>
html,body{margin:0;background:#000;color:#9fe}
.wrap{display:flex;gap:6px;padding:6px;height:100vh;box-sizing:border-box}
.cam{flex:1;position:relative;border:1px solid #133;border-radius:10px;overflow:hidden}
.lbl{position:absolute;left:8px;top:8px;background:rgba(0,0,0,.6);padding:4px 8px;border-radius:8px;font:14px system-ui}
img{width:100%;height:100%;object-fit:contain}
</style>
<script>
setInterval(()=>{
  document.getElementById('L').src='/snap/left?'+Date.now()
  document.getElementById('R').src='/snap/right?'+Date.now()
},100)
</script>
</head>
<body>
<div class="wrap">
  <div class="cam"><div class="lbl">LEFT /dev/video0</div><img id="L"></div>
  <div class="cam"><div class="lbl">RIGHT /dev/video2</div><img id="R"></div>
</div>
</body>
</html>
"""

def serve(path):
    if not os.path.exists(path):
        return ("", 204)
    resp = make_response(send_file(path, mimetype="image/jpeg"))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp

@app.get("/snap/left")
def left():
    return serve("/tmp/stereo/left.jpg")

@app.get("/snap/right")
def right():
    return serve("/tmp/stereo/right.jpg")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8095, threaded=True)
