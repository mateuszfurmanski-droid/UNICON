#!/usr/bin/env python3

from flask import Flask, jsonify
import time

try:
    from lidar_uart import find_lidar_port, read_tfluna_frame
    import serial
except Exception as e:
    lidar_error = str(e)
    find_lidar_port = None

app = Flask(__name__)

# === KONFIGURACJA ===
LIDAR_SCALE = 10      # <<< TO JEST TA ZMIANA (50 -> 505)
LIDAR_OFFSET = 0      # mm (jakbyś chciał jeszcze doprecyzować)

@app.route("/api/lidar")
def api_lidar():
    if not find_lidar_port:
        return jsonify({
            "error": "lidar_not_available",
            "reason": lidar_error,
            "timestamp": time.time()
        })

    try:
        port = find_lidar_port()
        ser = serial.Serial(port, baudrate=115200, timeout=1)
        distance_mm, strength, temperature = read_tfluna_frame(ser)
        ser.close()

        distance_mm = int(distance_mm * LIDAR_SCALE + LIDAR_OFFSET)

        return jsonify({
            "distance_mm": distance_mm,
            "strength": strength,
            "temperature_c": round(temperature, 1),
            "timestamp": time.time()
        })

    except Exception as e:
        return jsonify({
            "error": "lidar_read_failed",
            "reason": str(e),
            "timestamp": time.time()
        })


@app.route("/status")
def status():
    return jsonify({
        "system": "UNICON",
        "lidar": "scaled_x10",
        "timestamp": time.time()
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)
