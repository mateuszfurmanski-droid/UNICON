#!/usr/bin/env python3
import json, os, time
from http.server import BaseHTTPRequestHandler, HTTPServer

LUNA_JSON = "/tmp/unicon_luna.json"
HOST = "0.0.0.0"
PORT = 8088

HUD_HTML = b"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>UNICON HUD</title>
  <style>
    html,body{margin:0;height:100%;background:#000;color:#0f0;font-family:ui-monospace,Consolas,monospace}
    .wrap{display:flex;align-items:center;justify-content:center;height:100%}
    .box{border:1px solid rgba(0,255,0,.35);padding:18px 22px;border-radius:10px;text-align:center}
    .big{font-size:56px;letter-spacing:1px}
    .sub{opacity:.75;margin-top:10px;font-size:14px}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="box">
      <div class="big" id="d">----</div>
      <div class="sub" id="s">loading...</div>
    </div>
  </div>
<script>
async function tick(){
  try{
    const r = await fetch('/api/luna',{cache:'no-store'});
    const j = await r.json();
    document.getElementById('d').textContent = (j.dist_mm ?? '----') + ' mm';
    document.getElementById('s').textContent =
      'raw:'+(j.dist_mm_raw??'--')+'  str:'+(j.strength??'--')+'  frames:'+(j.frames_ok??'--');
  }catch(e){
    document.getElementById('d').textContent = '----';
    document.getElementById('s').textContent = 'no data';
  }
}
setInterval(tick, 100);
tick();
</script>
</body>
</html>
"""

def read_json(path):
  try:
    with open(path,"r",encoding="utf-8") as f:
      return json.load(f)
  except Exception:
    return {"ok": False, "err": "no_data", "ts": int(time.time()*1000)}

class H(BaseHTTPRequestHandler):
  def _send(self, code, ctype, data: bytes):
    self.send_response(code)
    self.send_header("Content-Type", ctype)
    self.send_header("Cache-Control", "no-store")
    self.send_header("Content-Length", str(len(data)))
    self.end_headers()
    self.wfile.write(data)

  def do_GET(self):
    if self.path in ("/", "/hud"):
      return self._send(200, "text/html; charset=utf-8", HUD_HTML)

    if self.path == "/api/luna":
      j = read_json(LUNA_JSON)
      j["ok"] = True if j.get("dist_mm") is not None else j.get("ok", False)
      data = json.dumps(j, separators=(",",":")).encode("utf-8")
      return self._send(200, "application/json; charset=utf-8", data)

    return self._send(404, "text/plain; charset=utf-8", b"not found")

  def log_message(self, format, *args):
    return

def main():
  httpd = HTTPServer((HOST, PORT), H)
  print(f"UNICON API listening on http://{HOST}:{PORT}")
  httpd.serve_forever()

if __name__ == "__main__":
  main()
