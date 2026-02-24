#!/usr/bin/env python3
import serial
import time
import struct
import glob

# === KONFIGURACJA ===
BAUDRATE = 115200
TIMEOUT = 1

def find_lidar_port():
    ports = glob.glob("/dev/serial/by-id/*")
    if not ports:
        raise RuntimeError("❌ Nie znaleziono LiDAR na /dev/serial/by-id/")
    return ports[0]

def read_tfluna_frame(ser):
    while True:
        b = ser.read(1)
        if b != b'\x59':
            continue
        b2 = ser.read(1)
        if b2 != b'\x59':
            continue

        frame = ser.read(7)
        if len(frame) != 7:
            continue

        dist_l, dist_h, strength_l, strength_h, temp_l, temp_h, checksum = struct.unpack(
            "7B", frame
        )

        data = [0x59, 0x59] + list(frame[:-1])
        if (sum(data) & 0xFF) != checksum:
            continue

        distance_mm = dist_l + (dist_h << 8)
        strength = strength_l + (strength_h << 8)
        temperature = (temp_l + (temp_h << 8)) / 8.0 - 256

        return distance_mm, strength, temperature

def main():
    port = find_lidar_port()
    print(f"✅ LiDAR port: {port}")

    ser = serial.Serial(
        port=port,
        baudrate=BAUDRATE,
        timeout=TIMEOUT
    )

    time.sleep(0.5)
    print("📡 Start odczytu TF-Luna (Ctrl+C aby zakończyć)\n")

    try:
        while True:
            dist, strength, temp = read_tfluna_frame(ser)
            print(f"Distance: {dist:4d} mm | Strength: {strength:5d} | Temp: {temp:5.1f} °C")
    except KeyboardInterrupt:
        print("\n👋 Bye")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
