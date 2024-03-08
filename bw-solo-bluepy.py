import time
from bluepy import btle
from loguru import logger
from bw-solo-common import *

class NotifyDelegate(btle.DefaultDelegate):

    def handleNotification(self, hnd, data):
        notification_handler(hnd, data)


peripheral = btle.Peripheral(BLE_ADDRESS)
peripheral.withDelegate(NotifyDelegate())
peripheral.setMTU(256)
peripheral.writeCharacteristic(0x26, b'\x01\x00', True) # Enable Notification

model_number = peripheral.readCharacteristic(0x0f).decode()
logger.info(f'Model Number: {model_number}')

serial_number = peripheral.readCharacteristic(0x11).decode()
logger.info(f'Serial Number: {serial_number}')

battery_level = int.from_bytes(peripheral.readCharacteristic(0x20), 'little')
logger.info(f'Battery Level: {battery_level}')

peripheral.writeCharacteristic(0x28, WRITE_DATA1, True)
peripheral.waitForNotifications(1)
peripheral.writeCharacteristic(0x28, WRITE_DATA2, True)
peripheral.waitForNotifications(1)
while True:
    peripheral.writeCharacteristic(0x28, WRITE_DATA3, True)
    peripheral.waitForNotifications(1)
    time.sleep(INTERVAL)
