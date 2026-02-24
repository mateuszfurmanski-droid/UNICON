#!/usr/bin/env python3
import time, math
import smbus

from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas

IMU_ADDR = 0x68

def twos16(h, l):
    v = (h << 8) | l
    return v - 65536 if v & 0x8000 else v

def main():
    # OLED
    serial_i2c = i2c(port=1, address=0x3c)
    device = ssd1306(serial_i2c, width=128, height=64)

    # IMU
    bus = smbus.SMBus(1)
    # wake up
    bus.write_byte_data(IMU_ADDR, 0x6B, 0x00)
    who = bus.read_byte_data(IMU_ADDR, 0x75)

    # proste filtrowanie
    pitch_f = 0.0
    roll_f  = 0.0
    alpha = 0.85  # im wyżej, tym spokojniej

    while True:
        # accel regs 0x3B..0x40
        data = bus.read_i2c_block_data(IMU_ADDR, 0x3B, 6)
        ax = twos16(data[0], data[1])
        ay = twos16(data[2], data[3])
        az = twos16(data[4], data[5])

        axf, ayf, azf = float(ax), float(ay), float(az)

        # pitch/roll z samego akcelerometru
        roll  = math.degrees(math.atan2(ayf, azf))
        pitch = math.degrees(math.atan2(-axf, math.sqrt(ayf*ayf + azf*azf)))

        # filtr
        roll_f  = alpha * roll_f  + (1 - alpha) * roll
        pitch_f = alpha * pitch_f + (1 - alpha) * pitch

        with canvas(device) as draw:
            draw.text((0, 0),  "UNICON IMU LIVE", fill=255)
            draw.text((0, 14), f"WHO: 0x{who:02X}", fill=255)
            draw.text((0, 30), f"PITCH: {pitch_f:6.1f}", fill=255)
            draw.text((0, 44), f"ROLL : {roll_f:6.1f}", fill=255)

        time.sleep(0.05)

if __name__ == "__main__":
    main()
