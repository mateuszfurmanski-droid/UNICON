import time, json, os
import board, busio
from adafruit_icm20x import ICM20948

ADDR = 0x68
SAMPLE_HZ = 100          # 100 Hz
DURATION_S = 15          # 15 sekund -> 1500 próbek
OUT_PATH = os.path.expanduser("~/unicon/imu/imu_bias_0x68.json")

def mean(vals):
    return sum(vals) / len(vals)

print("IMU CALIBRATION (BIAS)")
print(f"- addr: 0x{ADDR:02x}")
print(f"- sample: {SAMPLE_HZ} Hz, duration: {DURATION_S} s")
print("POŁÓŻ IMU PŁASKO I NIE RUSZAJ. Start za 3 sekundy...")

time.sleep(3)

i2c = busio.I2C(board.SCL, board.SDA)
imu = ICM20948(i2c, address=ADDR)

n = SAMPLE_HZ * DURATION_S
dt = 1.0 / SAMPLE_HZ

gx_l, gy_l, gz_l = [], [], []
ax_l, ay_l, az_l = [], [], []

t0 = time.time()
for i in range(n):
    ax, ay, az = imu.acceleration   # m/s^2
    gx, gy, gz = imu.gyro           # rad/s

    ax_l.append(ax); ay_l.append(ay); az_l.append(az)
    gx_l.append(gx); gy_l.append(gy); gz_l.append(gz)

    # prosty pacing
    target = t0 + (i + 1) * dt
    now = time.time()
    if target > now:
        time.sleep(target - now)

# średnie (bias)
gyro_bias = {
    "gx_rad_s": mean(gx_l),
    "gy_rad_s": mean(gy_l),
    "gz_rad_s": mean(gz_l),
}
acc_mean = {
    "ax_m_s2": mean(ax_l),
    "ay_m_s2": mean(ay_l),
    "az_m_s2": mean(az_l),
}

# ACC offset: chcemy, żeby po korekcji było (0,0,+9.80665) przy leżeniu płasko
G = 9.80665
acc_offset = {
    "ax_m_s2": acc_mean["ax_m_s2"] - 0.0,
    "ay_m_s2": acc_mean["ay_m_s2"] - 0.0,
    "az_m_s2": acc_mean["az_m_s2"] - G,
}

payload = {
    "sensor": "ICM20948",
    "i2c_address": f"0x{ADDR:02x}",
    "sample_hz": SAMPLE_HZ,
    "duration_s": DURATION_S,
    "gravity_assumed_m_s2": G,
    "gyro_bias": gyro_bias,
    "acc_mean_at_rest": acc_mean,
    "acc_offset": acc_offset,
    "notes": "Gyro bias: subtract from gyro. Acc offset: subtract from accel to get ~[0,0,+g] at rest (flat)."
}

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w") as f:
    json.dump(payload, f, indent=2)

print("\nDONE. Saved:")
print(OUT_PATH)

print("\nGyro bias (rad/s) — ODEJMUJ od odczytu:")
print(gyro_bias)

print("\nAccel mean at rest (m/s^2):")
print(acc_mean)

print("\nAccel offset (m/s^2) — ODEJMUJ od odczytu:")
print(acc_offset)
