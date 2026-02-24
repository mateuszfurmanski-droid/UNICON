import serial, time

PORT = "/dev/ttyUSB0"
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=0.2)
time.sleep(0.4)

def read_exact(n):
    b = bytearray()
    while len(b) < n:
        c = ser.read(n - len(b))
        if c:
            b.extend(c)
    return bytes(b)

def read_frame():
    while True:
        b1 = ser.read(1)
        if not b1:
            continue
        if b1[0] != 0x59:
            continue

        b2 = ser.read(1)
        if not b2 or b2[0] != 0x59:
            continue

        payload = read_exact(7)
        frame = b"\x59\x59" + payload

        if (sum(frame[:8]) & 0xFF) != frame[8]:
            continue

        dist = frame[2] | (frame[3] << 8)
        strength = frame[4] | (frame[5] << 8)
        return dist, strength

print("NO-FILTER frames (dist_mm, strength):")
for i in range(10):
    d, s = read_frame()
    print(f"{i+1:02d}: {d}  {s}")

ser.close()
