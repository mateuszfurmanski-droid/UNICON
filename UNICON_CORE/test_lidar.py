#!/usr/bin/env python3
import serial
import time

PORT = "/dev/ttyUSB0"
BAUD = 115200

def read_tfluna_mm(ser: serial.Serial) -> int | None:
    # TF-Luna frame: 0x59 0x59 + 7 bytes
    b = ser.read(1)
    if not b:
        return None
    if b[0] != 0x59:
        return None

    b2 = ser.read(1)
    if not b2 or b2[0] != 0x59:
        return None

    payload = ser.read(7)
    if len(payload) != 7:
        return None

    dist_l, dist_h = payload[0], payload[1]
    # strength_l, strength_h = payload[2], payload[3]
    # temp_l, temp_h = payload[4], payload[5]
    checksum = payload[6]

    frame = bytes([0x59, 0x59]) + payload[:6]
    calc = sum(frame) & 0xFF
    if calc != checksum:
        return None

    distance_mm = dist_l + (dist_h << 8)
    return distance_mm

def main():
    print(f"Opening {PORT} @ {BAUD} ...")
    ser = serial.Serial(PORT, BAUD, timeout=0.2)
    time.sleep(0.2)
    ser.reset_input_buffer()

    last_print = 0.0
    while True:
        d = read_tfluna_mm(ser)
        now = time.time()
        if d is not None and (now - last_print) > 0.05:  # ~20 Hz print
            print(f"Distance: {d} mm")
            last_print = now

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBye")
