#!/usr/bin/env python3
import os, time, statistics
import serial

PORT = os.environ.get("LUNA_PORT", "/dev/serial0")   # ttyAMA0 alias
BAUD = int(os.environ.get("LUNA_BAUD", "115200"))
# FORCE_SCALE: ustaw na 10 jeśli chcesz na sztywno (cm->mm), albo 1 jeśli mm->mm
FORCE_SCALE = os.environ.get("FORCE_SCALE", "").strip()

def read_frame(ser):
    # TF-Luna: 9 bytes frame, header 0x59 0x59
    # [0]=0x59 [1]=0x59 [2]=dist_L [3]=dist_H [4]=strength_L [5]=strength_H [6]=temp_L [7]=temp_H [8]=checksum
    b = ser.read(9)
    if len(b) != 9:
        return None
    if b[0] != 0x59 or b[1] != 0x59:
        return None
    chk = sum(b[0:8]) & 0xFF
    if chk != b[8]:
        return None
    dist = b[2] | (b[3] << 8)
    strength = b[4] | (b[5] << 8)
    return dist, strength

def main():
    print(f"[LUNA] PORT={PORT} BAUD={BAUD}")
    ser = serial.Serial(PORT, BAUD, timeout=0.2)
    time.sleep(0.1)
    buf = []
    last_print = 0.0

    # zbierz próbki do autokalibracji skali
    while len(buf) < 25:
        fr = read_frame(ser)
        if fr:
            d, s = fr
            # odfiltruj totalny syf
            if 0 < d < 12000:
                buf.append(d)

    med = int(statistics.median(buf))
    # heurystyka:
    # jeśli typowo 200..600 przy Twoich “metrach”, to prawie na pewno cm -> mm (×10)
    auto_scale = 10 if 80 <= med <= 800 else 1

    if FORCE_SCALE:
        scale = int(FORCE_SCALE)
        reason = f"FORCE_SCALE={scale}"
    else:
        scale = auto_scale
        reason = f"AUTO(median_raw={med} => scale={scale})"

    print(f"[LUNA] SCALE: {reason}")
    print("[LUNA] Output: raw | scaled_mm | strength")

    good = 0
    while True:
        fr = read_frame(ser)
        if not fr:
            continue
        d_raw, strength = fr
        d_mm = d_raw * scale
        good += 1
        # wypisuj ~20 Hz max
        now = time.time()
        if now - last_print >= 0.05:
            print(f"{d_raw:5d} | {d_mm:5d} mm | {strength}")
            last_print = now

if __name__ == "__main__":
    main()
