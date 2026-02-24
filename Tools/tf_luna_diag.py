#!/usr/bin/env python3
import serial, time, sys, argparse
from collections import deque

# TF-Luna / Benewake frame: 9 bytes
# [0]=0x59 [1]=0x59 [2]=Dist_L [3]=Dist_H [4]=Strength_L [5]=Strength_H
# [6]=Temp_L [7]=Temp_H [8]=Checksum (sum of bytes 0..7) & 0xFF

def parse_frame(frame: bytes):
    if len(frame) != 9:
        return None, "len"
    if frame[0] != 0x59 or frame[1] != 0x59:
        return None, "sync"
    checksum = (sum(frame[0:8]) & 0xFF)
    if checksum != frame[8]:
        return None, "checksum"

    dist_mm = frame[2] | (frame[3] << 8)
    strength = frame[4] | (frame[5] << 8)
    temp_c = ((frame[6] | (frame[7] << 8)) / 8.0) - 256.0
    return (dist_mm, strength, temp_c, checksum), None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="/dev/ttyAMA0", help="UART device e.g. /dev/ttyAMA0 or /dev/ttyS0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--avg", type=int, default=10, help="moving average window")
    ap.add_argument("--min_strength", type=int, default=0, help="ignore samples below strength")
    args = ap.parse_args()

    ser = serial.Serial(args.port, args.baud, timeout=0.2)

    buf = bytearray()
    ok = 0
    bad = 0
    reasons = {"len":0, "sync":0, "checksum":0}
    dist_q = deque(maxlen=max(1, args.avg))

    print(f"PORT={args.port} BAUD={args.baud} AVG={args.avg} MIN_STRENGTH={args.min_strength}")
    print("Move target closer/farther. Ctrl+C to stop.\n")

    last_print = 0.0
    try:
        while True:
            chunk = ser.read(256)
            if chunk:
                buf.extend(chunk)

            # find frames in stream
            while len(buf) >= 9:
                # align to sync bytes
                i = buf.find(b"\x59\x59")
                if i == -1:
                    # keep last byte in case of split sync
                    buf[:] = buf[-1:]
                    break
                if i > 0:
                    del buf[:i]
                if len(buf) < 9:
                    break

                frame = bytes(buf[:9])
                del buf[:9]

                parsed, err = parse_frame(frame)
                if err:
                    bad += 1
                    reasons[err] += 1
                    # show first few bad frames then be quiet
                    if bad <= 5:
                        print(f"BAD({err}) raw={frame.hex(' ')}")
                    continue

                dist_mm, strength, temp_c, checksum = parsed
                if strength < args.min_strength:
                    continue

                ok += 1
                dist_q.append(dist_mm)
                now = time.time()
                if now - last_print > 0.2:
                    avg = sum(dist_q)/len(dist_q)
                    print(f"dist={dist_mm:5d} mm  avg={avg:7.1f} mm  strength={strength:5d}  temp={temp_c:5.1f}C  ok={ok} bad={bad} (sync:{reasons['sync']} chk:{reasons['checksum']})")
                    last_print = now

    except KeyboardInterrupt:
        pass
    finally:
        ser.close()
        print("\n--- SUMMARY ---")
        print(f"OK frames: {ok}")
        print(f"BAD frames: {bad}  breakdown={reasons}")

if __name__ == "__main__":
    main()
