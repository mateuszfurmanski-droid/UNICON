import time
import serial


class TFLuna:
    """
    TF-Luna UART reader.
    Frame: 0x59 0x59 Dist_L Dist_H Strength_L Strength_H Temp_L Temp_H Checksum
    """

    def __init__(self, port: str = "/dev/ttyUSB0", baud: int = 115200, timeout: float = 0.2):
        self.port = port
        self.baud = baud
        self.timeout = timeout

        self.ser = None
        self.distance_mm = None
        self.strength = None
        self.temp_c = None
        self.last_ok_ts = 0.0

    def open(self):
        self.ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
        time.sleep(0.2)

    def close(self):
        try:
            if self.ser:
                self.ser.close()
        except Exception:
            pass
        self.ser = None

    def is_alive(self) -> bool:
        return (time.time() - self.last_ok_ts) < 1.0

    def _read_exact(self, n: int) -> bytes:
        data = self.ser.read(n)
        return data if len(data) == n else b""

    def read_once(self):
        """
        Blocking read for one valid frame. Returns (distance_mm, strength, temp_c) or None.
        """
        if not self.ser:
            return None

        # sync to header 0x59 0x59
        b1 = self._read_exact(1)
        if not b1 or b1[0] != 0x59:
            return None

        b2 = self._read_exact(1)
        if not b2 or b2[0] != 0x59:
            return None

        payload = self._read_exact(7)  # includes checksum as last byte
        if not payload:
            return None

        frame = bytes([0x59, 0x59]) + payload  # 9 bytes total
        checksum = sum(frame[:8]) & 0xFF
        if checksum != frame[8]:
            return None

        dist = frame[2] | (frame[3] << 8)
        strength = frame[4] | (frame[5] << 8)
        temp_raw = frame[6] | (frame[7] << 8)

        # Common TF-Luna conversion used in many examples:
        temp_c = (temp_raw / 8.0) - 256.0
        # If conversion is nonsense, fall back:
        if temp_c < -40 or temp_c > 140:
            temp_c = temp_raw / 100.0

        self.distance_mm = dist
        self.strength = strength
        self.temp_c = temp_c
        self.last_ok_ts = time.time()

        return dist, strength, temp_c

