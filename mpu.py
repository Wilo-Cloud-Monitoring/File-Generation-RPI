import smbus
import logging


class MPU:
    def __init__(self):
        self.PWR_MGMT_1 = 0x6B
        self.SMPLRT_DIV = 0x19
        self.CONFIG = 0x1A
        self.GYRO_CONFIG = 0x1B
        self.INT_ENABLE = 0x38
        self.ACCEL_XOUT_H = 0x3B
        self.ACCEL_YOUT_H = 0x3D
        self.ACCEL_ZOUT_H = 0x3F
        self.GYRO_XOUT_H = 0x43
        self.GYRO_YOUT_H = 0x45
        self.GYRO_ZOUT_H = 0x47
        self.BUS = smbus.SMBus(1)
        self.DEVICE_ADDRESS = 0x68
        self.mpu_init()

    def mpu_init(self):
        try:
            self.BUS.write_byte_data(self.DEVICE_ADDRESS, self.SMPLRT_DIV, 7)
            self.BUS.write_byte_data(self.DEVICE_ADDRESS, self.PWR_MGMT_1, 1)
            self.BUS.write_byte_data(self.DEVICE_ADDRESS, self.CONFIG, 0)
            self.BUS.write_byte_data(self.DEVICE_ADDRESS, self.GYRO_CONFIG, 24)
            self.BUS.write_byte_data(self.DEVICE_ADDRESS, self.INT_ENABLE, 1)
        except Exception as e:
            logging.exception("An exception occurred in MPU_Init: %s", e)

    def read_raw_data(self, addr):
        try:
            high = self.BUS.read_byte_data(self.DEVICE_ADDRESS, addr)
            low = self.BUS.read_byte_data(self.DEVICE_ADDRESS, addr + 1)
            value = (high << 8) | low
            if value > 32768:
                value = value - 65536
            return value
        except Exception as e:
            logging.exception("An exception occurred in read_raw_data: %s", e)
