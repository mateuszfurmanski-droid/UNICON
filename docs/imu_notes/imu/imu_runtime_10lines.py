import time
import board, busio
from adafruit_icm20x import ICM20948

ADDR = 0x68
LINES = 10
DT = 0.2

i2c = busio.I2C(board.SCL, board.SDA)
imu = ICM20948(i2c, address=ADDR)

for i in range(LINES):
    ax, ay, az = imu.acceleration
    gx, gy, gz = imu.gyro
    mx, my, mz = imu.magnetic
    print(f"{i+1:02d} ACC {ax:7.2f} {ay:7.2f} {az:7.2f} m/s^2 | "
          f"GYR {gx:7.3f} {gy:7.3f} {gz:7.3f} rad/s | "
          f"MAG {mx:7.1f} {my:7.1f} {mz:7.1f} uT")
    time.sleep(DT)
