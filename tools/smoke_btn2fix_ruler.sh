#!/usr/bin/env bash
set -euo pipefail

BASE="http://127.0.0.1:8095"
TS="$(date +%Y%m%d_%H%M%S)"
SNAP="/home/pi/UNICON/UNICON_ARCHIVE/SMOKE_${TS}_BTN2FIX_RULER_MATCH"
mkdir -p "$SNAP"

curl -fsS -m 2 "$BASE/api/btn2fix/RESET" >/dev/null
curl -fsS -m 2 "$BASE/api/btn2fix/A?x=0.12&y=0.34" >/dev/null
curl -fsS -m 2 "$BASE/api/btn2fix/B?x=0.78&y=0.65" >/dev/null

BTN="$(curl -fsS -m 2 "$BASE/api/btn2fix/state")"
RUL="$(curl -fsS -m 2 "$BASE/api/ruler/state")"

printf "%s\n" "$BTN" > "$SNAP/btn2fix_state.json"
printf "%s\n" "$RUL" > "$SNAP/ruler_state.json"

python3 -c 'import json,sys; from pathlib import Path; snap=Path(sys.argv[1]); btn=json.loads((snap/"btn2fix_state.json").read_text()); rul=json.loads((snap/"ruler_state.json").read_text()); bs=btn.get("state") or {}; rs=rul.get("state") or {}; keys=("A","B","last","reset"); bad=[(k,bs.get(k),rs.get(k)) for k in keys if bs.get(k)!=rs.get(k)]; print("ASSERT OK" if not bad else "ASSERT FAIL"); [print(f"- {k}: btn2fix={b!r} ruler={r!r}") for k,b,r in bad]; sys.exit(0 if not bad else 2)' "$SNAP"

ls -la "$SNAP"
echo "OK: proof in $SNAP"
