import time, threading, json
from http.server import BaseHTTPRequestHandler, HTTPServer

# ---- TF-Luna (UART) ----
def parse_tfluna_frame(ser):
    while True:
        b1 = ser.read(1)
        if not b1:
            return None
        if b1[0] != 0x59:
            continue
        b2 = ser.read(1)
        if not b2 or b2[0] != 0x59:
            continue
        data = ser.read(7)
        if len(data) != 7:
            continue
        frame = b"\x59\x59" + data
        if (sum(frame[:8]) & 0xFF) != frame[8]:
            continue
        dist = frame[2] | (frame[3] << 8)      # cm
        strength = frame[4] | (frame[5] << 8)
        temp_c = (frame[6] | (frame[7] << 8)) / 8.0 - 256
        return dist, strength, temp_c

class TFLunaWorker(threading.Thread):
    def __init__(self, port="/dev/serial0", baud=115200):
        super().__init__(daemon=True)
        self.port, self.baud = port, baud
        self.latest = None  # (ts, dist, strength, temp)
        self.err = None
        self.stop_flag = False

    def run(self):
        try:
            import serial
            ser = serial.Serial(self.port, self.baud, timeout=1)
        except Exception as e:
            self.err = f"serial open failed: {e}"
            return
        while not self.stop_flag:
            try:
                r = parse_tfluna_frame(ser)
                if r:
                    self.latest = (time.time(),) + r
            except Exception as e:
                self.err = f"read failed: {e}"
                break
        try: ser.close()
        except Exception: pass

# ---- IMU (I2C WHO_AM_I) ----
class IMUWorker(threading.Thread):
    def __init__(self, addr=0x68, bus_id=1):
        super().__init__(daemon=True)
        self.addr, self.bus_id = addr, bus_id
        self.latest = None  # (ts, who, backend)
        self.err = None
        self.stop_flag = False

    def run(self):
        try:
            from smbus2 import SMBus
            bus = SMBus(self.bus_id)
            backend = "smbus2"
        except Exception:
            try:
                import smbus
                bus = smbus.SMBus(self.bus_id)
                backend = "smbus"
            except Exception as e:
                self.err = f"no smbus/smbus2: {e}"
                return

        while not self.stop_flag:
            try:
                try:
                    bus.write_byte_data(self.addr, 0x6B, 0x00)
                except Exception:
                    pass
                who = bus.read_byte_data(self.addr, 0x75)
                self.latest = (time.time(), who, backend)
            except Exception as e:
                self.err = f"imu read failed: {e}"
            time.sleep(1.0)

        try: bus.close()
        except Exception: pass

def age_ms(ts):
    return int((time.time() - ts) * 1000)

def build_state(tf, imu, started_ts):
    st = {"uptime_s": round(time.time() - started_ts, 3), "lidar": None, "imu": None, "errors": {}}
    if tf.latest:
        ts, d, s, t = tf.latest
        st["lidar"] = {"distance_cm": int(d), "strength": int(s), "temp_c": round(float(t), 2), "age_ms": age_ms(ts)}
    else:
        st["errors"]["lidar"] = tf.err or "no_data"

    if imu.latest:
        ts, who, backend = imu.latest
        st["imu"] = {"whoami": hex(who), "backend": backend, "age_ms": age_ms(ts)}
    else:
        st["errors"]["imu"] = imu.err or "no_data"
    return st

# ---- HTTP ----
class Handler(BaseHTTPRequestHandler):
    tf = None
    imu = None
    started_ts = None

    def _send_json(self, code, obj):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"UNICON CORE v0.2\n/health\n/sensors\n")
            return
        if self.path.startswith("/health"):
            st = build_state(self.tf, self.imu, self.started_ts)
            ok = (st["lidar"] is not None) and (st["imu"] is not None)
            self._send_json(200, {"ok": ok, **st})
            return
        if self.path.startswith("/sensors"):
            self._send_json(200, build_state(self.tf, self.imu, self.started_ts))
            return
        self._send_json(404, {"error": "not_found", "path": self.path})

    def log_message(self, format, *args):
        return

def main():
    started_ts = time.time()

    tf = TFLunaWorker("/dev/serial0", 115200)
    imu = IMUWorker(0x68, 1)
    tf.start()
    imu.start()

    Handler.tf = tf
    Handler.imu = imu
    Handler.started_ts = started_ts

    host, port = "0.0.0.0", 8081
    httpd = HTTPServer((host, port), Handler)

    print("[HTTP] Listening on 0.0.0.0:8081")
    print("Press Ctrl+C to stop.")
    try:
        while True:
            httpd.handle_request()
    except KeyboardInterrupt:
        pass
    finally:
        tf.stop_flag = True
        imu.stop_flag = True

if __name__ == "__main__":
    main()
