#!/usr/bin/env python3
import time, threading
import serial
import cv2
from flask import Flask, Response, jsonify

LIDAR_PORT = "/dev/serial0"
LIDAR_BAUD = 115200
VIDEO_DEV  = "/dev/video0"

app = Flask(__name__)

latest = {
    "ts": None,
    "dist_cm": None,
    "strength": None,
    "temp_c": None,
    "cam_ok": False,
}

def read_exact(ser, n):
    buf = bytearray()
    while len(buf) < n:
        b = ser.read(n - len(buf))
        if not b:
            return None
        buf.extend(b)
    return bytes(buf)

def lidar_loop():
    try:
        ser = serial.Serial(LIDAR_PORT, LIDAR_BAUD, timeout=0.2)
    except Exception:
        return
    while True:
        b1 = ser.read(1)
        if not b1 or b1[0] != 0x59: continue
        b2 = ser.read(1)
        if not b2 or b2[0] != 0x59: continue
        payload = read_exact(ser, 7)
        if not payload: continue
        frame = b"\x59\x59" + payload
        if (sum(frame[:8]) & 0xFF) != frame[8]: continue

        dist_mm = frame[2] | (frame[3] << 8)
        strength = frame[4] | (frame[5] << 8)
        temp = (frame[6] | (frame[7] << 8)) / 8.0 - 256.0

        latest["ts"] = time.time()
        latest["dist_cm"] = round(dist_mm / 10.0, 1)
        latest["strength"] = int(strength)
        latest["temp_c"] = round(temp, 1)

def camera_stream():
    cap = cv2.VideoCapture(VIDEO_DEV)
    while True:
        ok, frame = cap.read()
        if not ok:
            latest["cam_ok"] = False
            time.sleep(0.1)
            continue

        latest["cam_ok"] = True
        h, w = frame.shape[:2]
        cx, cy = w//2, h//2
        cv2.drawMarker(frame, (cx, cy), (0,255,0), cv2.MARKER_CROSS, 30, 2)
        txt = f"{latest['dist_cm']} cm"
        cv2.putText(frame, txt, (20,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        ret, jpg = cv2.imencode(".jpg", frame)
        if not ret: continue
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n")

@app.route("/")
def index():
    return "<img src='/cam.mjpg' style='width:100%'>"

@app.route("/cam.mjpg")
def cam():
    return Response(camera_stream(),
        mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/health")
def health():
    return jsonify(latest)

if __name__ == "__main__":
    threading.Thread(target=lidar_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8090)
