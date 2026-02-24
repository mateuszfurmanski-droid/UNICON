#!/usr/bin/env bash
set -euo pipefail
SVC="unicon-master.service"
echo "== SERVICE STATUS =="
sudo systemctl status "$SVC" --no-pager | sed -n '1,25p' || true
echo
echo "== PORT 8090 =="
ss -lntp | grep ':8090' || echo "Port 8090 NOT listening"
echo
echo "== LOCAL HEALTH =="
curl -sS -m 2 -D- http://127.0.0.1:8090/health -o /dev/null || true
echo
echo "== LOCAL / (first 5 lines) =="
curl -sS -m 2 http://127.0.0.1:8090/ | head -n 5 || true
