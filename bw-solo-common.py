import struct
import time
import boto3
import math
import uuid
import json
from bleak import uuids
from loguru import logger

BLE_ADDRESS = '00:12:9f:07:2e:96'

INTERVAL = 15
UPLOAD_ENABLED = False

UUID_DEVICE_INFORMATION = uuids.normalize_uuid_16(0x180a)
UUID_MODEL_NUMBER_CHAR = uuids.normalize_uuid_16(0x2a24)
UUID_SERIAL_NUMBER_CHAR = uuids.normalize_uuid_16(0x2a25)
UUID_BATTERY_SERVICE =  uuids.normalize_uuid_16(0x180f)
UUID_BATTERY_LEVEL_CHAR = uuids.normalize_uuid_16(0x2a19)
UUID_GAS_SERVICE = 'fc247940-6e08-11e4-80fc-0002a5d5c51b'
UUID_GAS_WRITEONLY_CHAR = '3d115840-6e0b-11e4-b24f-0002a5d5c51b'
UUID_GAS_NOTIFICATION_CHAR = 'f833d6c0-6e0b-11e4-9136-0002a5d5c51b'

def crc16(data: bytes, poly=0x8005, init=0x011a, xorout=0x0000) -> bytes:
    for x in data:
        init ^= x << 8
        for _ in range(8):
            if init & 0x8000:
                init = ((init << 1) ^ poly) & 0xffff
            else:
                init = (init << 1) & 0xffff
    return (init ^ xorout).to_bytes(2, 'big')


def build_data(command: bytes) -> bytes:
    command = b'\x41\x00' + command
    return b'\x7b' + command + crc16(command) + b'\x7d'

WRITE_DATA1 = build_data(b'\x08\x40\xa2\x02\x01\x01')
WRITE_DATA2 = build_data(b'\x06\x40\xa1\x01')
WRITE_DATA3 = build_data(b'\x06\x40\xa0\x01')

if UPLOAD_ENABLED:
    client = boto3.client('iotsitewise')

def notification_handler(hnd, data: bytes) -> None:
    logger.debug(f'{hnd} : {data.hex()}')
    if len(data) != 37:
        return
    
    if data[0] != 0x7b or data[-1] != 0x7d:
        raise('Invalid Format')

    if data[1:3] != b'\x41\00':
        raise('Invalid Header')

    if crc16(data[1:-3]) != data[-3:-1]:
        raise('Incorrect CRC')

    value = struct.unpack('<f', data[27:31])[0]
    alerm = data[32:34]
    logger.info(f"ClO2: {value:.2f} [ppm], Alerm: {alerm.hex()}")

    if UPLOAD_ENABLED:
        t = math.modf(time.time())
        timestamp = {
            'timeInSeconds': int(t[1]),
            'offsetInNanos': int(t[0] * 1000000000)
        }
        response = client.batch_put_asset_property_value(entries=[
            {
                'entryId': uuid.uuid4(),
                'propertyAlias': '/device/bw-solo/ClO2',
                'propertyValues': [
                    {
                        'value': {
                            'doubleValue': value
                        },
                        'timestamp': timestamp
                    }
                ]
            }
        ])
        logger.debug(f'response: {json.dumps(response, indent=2)}')