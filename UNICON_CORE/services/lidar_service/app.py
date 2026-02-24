from flask import Flask, jsonify
import serial
import time

PORT = "/dev/ttyUSB0"
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=1)

app = Flask(__name__)

def read_lidar():
    while True:
        if ser.in_waiting >= 9:
            data = ser.read(9)
            if data[0] == 0x59 and data[1] == 0x59:
                dist = data[2] + data[3] * 256
                strength = data[4] + data[5] * 256
                return dist, strength

@app.route("/api/lidar")
def lidar():
    dist, strength = read_lidar()
    return jsonify({
        "distance_mm": dist,
        "strength": strength,
        "timestamp": time.time()
    })

if __name__ == "__main__":
    print("LiDAR service running on port 8090")
    app.run(host="0.0.0.0", port=8090)

