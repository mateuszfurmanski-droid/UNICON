#!/usr/bin/env python3
# TF-Luna stable output for HUD
# Reads /dev/serial0 (115200), parses YY frames, outputs JSON to /tmp/unicon_luna.json
# Units: mm (TF-Luna reports cm -> *10)

import json, time
from collections import deque
import serial

PORT = "/dev/serial0"
BAUD = 115200

# TF-Luna frame: dist is in cm -> convert to mm
CM_TO_MM = 10

# Output
OUT_PATH = "/tmp/unicon_luna.json"
WRITE_HZ = 20  # write rate (20Hz is enough for HUD)

# Filters / stabilization
MEDIAN_WIN = 7           # 5/7/9
EMA_ALPHA = 0.25         # 0.15 smoother, 0.30 snappier
DEADBAND_MM = 30         # ignore tiny changes (<3cm) to stop jitter on HUD
MAX_STEP_MM = 300        # clamp jumps per update (30cm per sample)
MIN_MM = 0
MAX_MM = 12000           # 12m cap (adjust if you want)

# Optional quantize to sensor step (TF-Luna often 10mm steps)
QUANT_MM = 10            # set 1 for no quantize

def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

def median(vals):
    s = sorted(vals)
    return s[len(s)//2]

def write_json(payload):
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))
    # atomic replace
    import os
    os.replace(tmp, OUT_PATH)

def main():
    ser = serial.Serial(PORT, BAUD, timeout=0.2)
    buf = bytearray()

    win = deque(maxlen=MEDIAN_WIN)
    ema = None
    last_out = None

    last_write = 0.0
    write_period = 1.0 / float(WRITE_HZ)

    frames_ok = 0
    last_dist_raw = None
    last_strength = None

    while True:
        chunk = ser.read(64)
        if chunk:
            buf += chunk

        # parse as many frames as available
        while True:
            i = buf.find(b"\x59\x59")
            if i < 0:
                # keep buffer from growing forever
                if len(buf) > 2000:
                    buf.clear()
                break
            if len(buf) < i + 9:
                break

            frame = buf[i:i+9]
            del buf[:i+9]

            dist_cm = frame[2] | (frame[3] << 8)
            strength = frame[4] | (frame[5] << 8)

            dist_mm = int(dist_cm) * CM_TO_MM
            dist_mm = clamp(dist_mm, MIN_MM, MAX_MM)

            frames_ok += 1
            last_dist_raw = dist_mm
            last_strength = int(strength)

            # --- Filtering ---
            win.append(dist_mm)
            m = median(win) if len(win) >= 3 else dist_mm

            if ema is None:
                ema = float(m)
            else:
                ema = (EMA_ALPHA * float(m)) + ((1.0 - EMA_ALPHA) * ema)

            filt = int(round(ema))

            # clamp too fast steps (anti-teleport)
            if last_out is not None:
                step = filt - last_out
                if step > MAX_STEP_MM:
                    filt = last_out + MAX_STEP_MM
                elif step < -MAX_STEP_MM:
                    filt = last_out - MAX_STEP_MM

            # deadband (ignore tiny wiggles)
            if last_out is not None and abs(filt - last_out) < DEADBAND_MM:
                filt = last_out

            # quantize
            if QUANT_MM > 1:
                filt = int(round(filt / QUANT_MM) * QUANT_MM)

            last_out = filt

        # write JSON at fixed rate (even if no new frames, keep last known)
        now = time.time()
        if now - last_write >= write_period:
            last_write = now
            payload = {
                "ts": int(now * 1000),
                "dist_mm_raw": last_dist_raw,
                "dist_mm": last_out,
                "strength": last_strength,
                "frames_ok": frames_ok,
            }
            try:
                write_json(payload)
            except Exception:
                pass

        # tiny sleep to reduce CPU
        time.sleep(0.001)

if __name__ == "__main__":
    main()
