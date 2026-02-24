#!/usr/bin/env python3
import os, time, datetime, subprocess
import serial

LIDAR_PORT = "/dev/serial0"
LIDAR_BAUD = 115200
I2C_DEV = "/dev/i2c-1"
LOG_DIR = os.path.expanduser("~/UNICON/logs")
os.makedirs(LOG_DIR, exist_ok=True)

def imu_present():
    return os.path.exists(I2C_DEV)

def camera_present():
    for i in range(0, 64):
        if os.path.exists(f"/dev/video{i}"):
            return True
    return False

def first_camera_dev():
    for i in range(0, 64):
        p = f"/dev/video{i}"
        if os.path.exists(p):
            return p
    return None

def ffmpeg_exists():
    return subprocess.call(["bash","-lc","command -v ffmpeg >/dev/null 2>&1"]) == 0

def snap_camera(path):
    dev = first_camera_dev()
    if not dev or not ffmpeg_exists():
        return False, f"camera_dev={dev}, ffmpeg={ffmpeg_exists()}"
    # jedna klatka do jpg
    cmd = ["ffmpeg","-hide_banner","-loglevel","error","-f","v4l2","-i",dev,"-frames:v","1",path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return False, r.stderr.strip()
    return True, "ok"

def read_luna_frame(ser):
    while True:
        b1 = ser.read(1)
        if not b1:
            return None
        if b1[0] != 0x59:
            continue
        b2 = ser.read(1)
        if not b2:
            return None
        if b2[0] != 0x59:
            continue
        payload = ser.read(7)
        if len(payload) != 7:
            return None
        frame = b"\x59\x59" + payload
        if (sum(frame[:8]) & 0xFF) != frame[8]:
            continue
        dist_cm = frame[2] | (frame[3] << 8)
        strength = frame[4] | (frame[5] << 8)
        temp_c = (frame[6] | (frame[7] << 8)) / 8.0 - 256.0
        return dist_cm, strength, temp_c

def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(LOG_DIR, f"core_demo_{ts}.log")
    print("=== UNICON CORE DEMO ===")
    print(f"LOG: {log_path}")
    print(f"IMU I2C present: {imu_present()} ({I2C_DEV})")
    print(f"Camera present:  {camera_present()} (/dev/video*)")
    print(f"LiDAR: {LIDAR_PORT} @ {LIDAR_BAUD}")
    print("Press Ctrl+C to stop. Type 's' + Enter to try snapshot.\n")

    ser = serial.Serial(LIDAR_PORT, LIDAR_BAUD, timeout=1)
    time.sleep(0.2)

    last = 0.0
    try:
        with open(log_path, "w", buffering=1) as f:
            f.write("time_iso,dist_cm,strength,temp_c,imu_ok,cam_ok\n")
            while True:
                # non-blocking “snapshot command” (user can type s + Enter)
                if os.path.exists("/dev/stdin"):
                    try:
                        import select, sys
                        if select.select([sys.stdin], [], [], 0.0)[0]:
                            line = sys.stdin.readline().strip().lower()
                            if line == "s":
                                img = os.path.join(LOG_DIR, f"snap_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                                ok, info = snap_camera(img)
                                print(f"SNAP: {'OK' if ok else 'NO'} -> {img} ({info})")
                    except Exception:
                        pass

                r = read_luna_frame(ser)
                now = time.time()
                if r and (now - last) >= 0.2:
                    d, s, t = r
                    imu_ok = imu_present()
                    cam_ok = camera_present()
                    iso = datetime.datetime.now().isoformat(timespec="seconds")
                    line = f"{iso},{d},{s},{t:.1f},{int(imu_ok)},{int(cam_ok)}"
                    print(f"LiDAR: {d:4d} cm | strength {s:5d} | temp {t:4.1f} C | IMU:{'OK' if imu_ok else 'NO'} | CAM:{'OK' if cam_ok else 'NO'}")
                    f.write(line + "\n")
                    last = now
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()
        print("\nStopped.")

if __name__ == "__main__":
    main()
