import time, json, os, math
import board, busio
from adafruit_icm20x import ICM20948

ADDR = 0x68
BIAS_PATH = os.path.expanduser("~/unicon/imu/imu_bias_0x68.json")

# Complementary filter tuning
ALPHA = 0.98          # gyro weight (0.95..0.99 typical)
DT_TARGET = 0.01      # 100 Hz target loop

RAD2DEG = 180.0 / math.pi

def accel_to_rp(ax, ay, az):
    # roll: rotation around X axis (right-hand)
    # pitch: rotation around Y axis
    # Using standard equations (assuming ax,ay,az in m/s^2)
    roll = math.atan2(ay, az)
    pitch = math.atan2(-ax, math.sqrt(ay*ay + az*az))
    return roll, pitch

with open(BIAS_PATH, "r") as f:
    bias = json.load(f)

gb = bias["gyro_bias"]
ao = bias["acc_offset"]

i2c = busio.I2C(board.SCL, board.SDA)
imu = ICM20948(i2c, address=ADDR)

print("Complementary Filter: ROLL/PITCH")
print(f"addr=0x{ADDR:02x}  ALPHA={ALPHA}  target_dt={DT_TARGET}s")
print("Move IMU slowly. Ctrl+C to stop.\n")

# init from accel
ax, ay, az = imu.acceleration
ax -= ao["ax_m_s2"]; ay -= ao["ay_m_s2"]; az -= ao["az_m_s2"]
roll, pitch = accel_to_rp(ax, ay, az)

t_prev = time.time()

while True:
    t_now = time.time()
    dt = t_now - t_prev
    t_prev = t_now
    if dt <= 0:
        dt = DT_TARGET

    ax, ay, az = imu.acceleration
    gx, gy, gz = imu.gyro  # rad/s

    # apply offsets
    ax -= ao["ax_m_s2"]; ay -= ao["ay_m_s2"]; az -= ao["az_m_s2"]
    gx -= gb["gx_rad_s"]; gy -= gb["gy_rad_s"]; gz -= gb["gz_rad_s"]

    # accel angles
    roll_acc, pitch_acc = accel_to_rp(ax, ay, az)

    # gyro integrate (note: roll uses gx, pitch uses gy in this frame)
    roll_gyro = roll + gx * dt
    pitch_gyro = pitch + gy * dt

    # complementary fuse
    roll = ALPHA * roll_gyro + (1 - ALPHA) * roll_acc
    pitch = ALPHA * pitch_gyro + (1 - ALPHA) * pitch_acc

    print(f"roll={roll*RAD2DEG:+7.2f}°  pitch={pitch*RAD2DEG:+7.2f}°   dt={dt*1000:5.1f}ms", end="\r")

    # pacing
    sleep = DT_TARGET - (time.time() - t_now)
    if sleep > 0:
        time.sleep(sleep)
