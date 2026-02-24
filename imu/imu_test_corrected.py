import time, json, os
import board, busio
from adafruit_icm20x import ICM20948

ADDR = 0x68
BIAS_PATH = os.path.expanduser("~/unicon/imu/imu_bias_0x68.json")

with open(BIAS_PATH, "r") as f:
    bias = json.load(f)

gb = bias["gyro_bias"]
ao = bias["acc_offset"]

i2c = busio.I2C(board.SCL, board.SDA)
imu = ICM20948(i2c, address=ADDR)

print("Hold IMU still. Printing corrected values (should be near 0 for gyro).")
t0 = time.time()
for i in range(50):  # ~10s at 0.2s
    ax, ay, az = imu.acceleration
    gx, gy, gz = imu.gyro

    axc = ax - ao["ax_m_s2"]
    ayc = ay - ao["ay_m_s2"]
    azc = az - ao["az_m_s2"]

    gxc = gx - gb["gx_rad_s"]
    gyc = gy - gb["gy_rad_s"]
    gzc = gz - gb["gz_rad_s"]

    print(f"{i+1:02d} ACCc {axc:+6.3f} {ayc:+6.3f} {azc:+6.3f}  |  GYRc {gxc:+7.4f} {gyc:+7.4f} {gzc:+7.4f}")
    time.sleep(0.2)
