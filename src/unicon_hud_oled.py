#!/usr/bin/env python3
import os, time, threading, math
from flask import Flask, Response, jsonify
import serial

# --- OLED (SSD1306 I2C 0x3c) ---
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas

# --- IMU (MPU6050 @ 0x68) ---
import smbus

# --- Camera (OpenCV) ---
import cv2

VIDEO_DEV = "/dev/video0"
LIDAR_PORT = "/dev/serial0"
LIDAR_BAUD = 115200
IMU_ADDR   = 0x68

# HTTP
HTTP_PORT = 8090

app = Flask(__name__)

state = {
    "ts": None,
    "lidar": {"dist_cm": None, "strength": None, "temp_c": None, "ok": False},
    "imu": {"ok": False, "whoami": None, "pitch": None, "roll": None},
    "cam": {"ok": False, "dev": VIDEO_DEV},
}

# ---------------- LiDAR (TF-Luna/TFmini) ----------------
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
        state["lidar"]["ok"] = False
        return

    while True:
        try:
            b1 = ser.read(1)
            if not b1 or b1[0] != 0x59:
                continue
            b2 = ser.read(1)
            if not b2 or b2[0] != 0x59:
                continue
            payload = read_exact(ser, 7)
            if not payload:
                continue
            frame = b"\x59\x59" + payload
            if (sum(frame[:8]) & 0xFF) != frame[8]:
                continue

            dist_mm  = frame[2] | (frame[3] << 8)
            strength = frame[4] | (frame[5] << 8)
            temp     = (frame[6] | (frame[7] << 8)) / 8.0 - 256.0

            state["ts"] = time.time()
            state["lidar"].update({
                "dist_cm": round(dist_mm / 10.0, 1),
                "strength": int(strength),
                "temp_c": round(temp, 1),
                "ok": True,
            })
        except Exception:
            state["lidar"]["ok"] = False
            time.sleep(0.2)

# ---------------- IMU (MPU6050) ----------------
def twos16(h, l):
    v = (h << 8) | l
    return v - 65536 if v & 0x8000 else v

def imu_loop():
    bus = smbus.SMBus(1)
    # wake up
    try:
        bus.write_byte_data(IMU_ADDR, 0x6B, 0x00)
        who = bus.read_byte_data(IMU_ADDR, 0x75)
        state["imu"]["whoami"] = hex(who)
    except Exception:
        state["imu"]["ok"] = False
        return

    while True:
        try:
            # accel regs: 0x3B..0x40
            data = bus.read_i2c_block_data(IMU_ADDR, 0x3B, 6)
            ax = twos16(data[0], data[1])
            ay = twos16(data[2], data[3])
            az = twos16(data[4], data[5])

            # Normalize (rough; enough for HUD)
            # pitch/roll from accel only
            axf, ayf, azf = float(ax), float(ay), float(az)
            roll  = math.degrees(math.atan2(ayf, azf))
            pitch = math.degrees(math.atan2(-axf, math.sqrt(ayf*ayf + azf*azf)))

            state["imu"].update({
                "ok": True,
                "roll": round(roll, 1),
                "pitch": round(pitch, 1),
            })
        except Exception:
            state["imu"]["ok"] = False
        time.sleep(0.05)

# ---------------- Camera probe ----------------
def cam_probe_loop():
    while True:
        ok = os.path.exists(VIDEO_DEV)
        state["cam"]["ok"] = bool(ok)
        time.sleep(1.0)

# ---------------- OLED render ----------------
def oled_loop():
    serial_i2c = i2c(port=1, address=0x3c)
    device = ssd1306(serial_i2c, width=128, height=64)
    while True:
        l = state["lidar"]
        i = state["imu"]
        c = state["cam"]

        dist = l["dist_cm"]
        strn = l["strength"]
        temp = l["temp_c"]

        line1 = f"DIST:{dist if dist is not None else '--'}cm"
        line2 = f"IMU P:{i['pitch'] if i['pitch'] is not None else '--'} R:{i['roll'] if i['roll'] is not None else '--'}"
        line3 = f"CAM:{'OK' if c['ok'] else 'NO'} L:{'OK' if l['ok'] else 'NO'}"
        line4 = f"S:{strn if strn is not None else '--'} T:{temp if temp is not None else '--'}"

        with canvas(device) as draw:
            draw.text((0, 0),  "UNICON CORE", fill=255)
            draw.text((0, 16), line1,         fill=255)
            draw.text((0, 28), line2,         fill=255)
            draw.text((0, 40), line3,         fill=255)
            draw.text((0, 52), line4,         fill=255)

        time.sleep(0.2)

# ---------------- HDMI HUD (MJPEG) ----------------
def mjpeg_frames():
    cap = cv2.VideoCapture(VIDEO_DEV, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.05)
            continue

        h, w = frame.shape[:2]
        cx, cy = w//2, h//2

        # crosshair
        cv2.drawMarker(frame, (cx, cy), (0,255,0), cv2.MARKER_CROSS, 30, 2)

        # text overlay
        l = state["lidar"]; i = state["imu"]; c = state["cam"]
        txt1 = f"LiDAR: {l['dist_cm']} cm  S:{l['strength']}  T:{l['temp_c']}C"
        txt2 = f"IMU: P:{i['pitch']} R:{i['roll']}   CAM:{'OK' if c['ok'] else 'NO'}"
        cv2.putText(frame, txt1, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        cv2.putText(frame, txt2, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

        ret, jpg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ret:
            continue

        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n")

@app.get("/health")
def health():
    return jsonify({"ok": True, "state": state})

@app.get("/cam.mjpg")
def cam_mjpg():
    return Response(mjpeg_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.get("/")
def index():
    return "<html><body style='margin:0;background:#000'><img src='/cam.mjpg' style='width:100vw;height:100vh;object-fit:contain'></body></html>"

def main():
    threading.Thread(target=lidar_loop, daemon=True).start()
    threading.Thread(target=imu_loop, daemon=True).start()
    threading.Thread(target=cam_probe_loop, daemon=True).start()
    threading.Thread(target=oled_loop, daemon=True).start()

    app.run(host="0.0.0.0", port=HTTP_PORT, threaded=True)

if __name__ == "__main__":
    main()
