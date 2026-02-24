import time
import board
import busio
from adafruit_icm20x import ICM20948

i2c = busio.I2C(board.SCL, board.SDA)
imu = ICM20948(i2c)

while True:
    ax, ay, az = imu.acceleration
    gx, gy, gz = imu.gyro
    mx, my, mz = imu.magnetic

    print(f"ACC: {ax:7.2f} {ay:7.2f} {az:7.2f}  m/s^2")
    print(f"GYR: {gx:7.3f} {gy:7.3f} {gz:7.3f}  rad/s")
    print(f"MAG: {mx:7.1f} {my:7.1f} {mz:7.1f}  uT")
    print("-" * 28)
    time.sleep(0.25)
import time
import board
import busio
from adafruit_icm20x import ICM20948

i2c = busio.I2C(board.SCL, board.SDA)
imu = ICM20948(i2c)

while True:
    ax, ay, az = imu.acceleration
    gx, gy, gz = imu.gyro
    mx, my, mz = imu.magnetic

    print(f"ACC: {ax:7.2f} {ay:7.2f} {az:7.2f}  m/s^2")
    print(f"GYR: {gx:7.3f} {gy:7.3f} {gz:7.3f}  rad/s")
    print(f"MAG: {mx:7.1f} {my:7.1f} {mz:7.1f}  uT")
    print("-" * 28)
    time.sleep(0.25)
