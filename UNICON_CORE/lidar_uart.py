#!/usr/bin/env python3
import serial
import time

PORT = "/dev/ttyAMA0"
BAUD = 115200
MIN_STRENGTH = 100
READS = 10

def _read_exact(ser, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = ser.read(n - len(buf))
        if chunk:
            buf.extend(chunk)
    return bytes(buf)

def read_tf_luna_frame(ser):
    while True:
        b1 = ser.read(1)
        if not b1:
            continue
        if b1[0] != 0x59:
            continue

        b2 = ser.read(1)
        if not b2 or b2[0] != 0x59:
            continue

        payload = _read_exact(ser, 7)
        frame = bytes([0x59, 0x59]) + payload

        checksum = sum(frame[:8]) & 0xFF
        if checksum != frame[8]:
            continue

        dist = frame[2] | (frame[3] << 8)
        strength = frame[4] | (frame[5] << 8)
        temp_raw = frame[6] | (frame[7] << 8)
        temp_c = (temp_raw / 8.0) - 256.0

        return dist, strength, temp_c

def main():
    ser = serial.Serial(PORT, BAUD, timeout=0.1)
    time.sleep(0.5)  # <<< BARDZO WAŻNE

    print("TF-Luna test (filtered, stable)")
    print("------------------------------")

    good = 0
    while good < READS:
        dist, strength, temp = read_tf_luna_frame(ser)

        if strength < MIN_STRENGTH:
            continue

        print(f"Distance: {dist} mm | Strength: {strength}")
        good += 1

    ser.close()

if __name__ == "__main__":
    main()
