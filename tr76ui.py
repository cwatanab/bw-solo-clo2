import json
import serial
from loguru import logger

UPLOAD_ENABLED = False
# SERIAL_PORT = '/dev/ttyUSB0'
SERIAL_PORT = 'COM4'
SERIAL_BAUDRATE = 19200
 
SOH = 0x01
ACK = 0x06
NAK = 0x15
READ_CURRENT_VALUE = 0x33
READ_SERIAL_NUMBER = 0x58
READ_BATTERY_VOLTAGE = 0x39

def to_co2ppm(raw: int) -> int:
    if 0xf000 <= raw <= 0xf00f:
        raise ValueError(hex(raw))
    sign = (raw & 0x8000) >> 15;
    exponent = (raw & 0x7000) >> 12;
    mantissa = (raw & 0x0fff)
    n = ~(mantissa ^ 0xfff) if sign else mantissa
    return n << exponent

assert to_co2ppm(423) == 423
assert to_co2ppm(6596) == 5000
assert to_co2ppm(36852) == -12

def to_value(raw: int) -> float:
    if raw & 0xfff0 == 0xeeee:
        raise ValueError(hex(raw))
    return (raw - 1000) / 10

assert to_value(1253) == 25.3
assert to_value(695) == -30.5
assert to_value(1923) == 92.3

def send(command:int, sub_command:int=0, payload:bytes=bytes()) -> bytes:
    with serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE, timeout=1) as ser:
        send_data = bytearray([SOH, command, sub_command])
        send_data += len(payload).to_bytes(2, byteorder='little') 
        send_data += payload
        ser.write(send_data)
        ser.write(sum(send_data).to_bytes(2, byteorder='little')) # Checksum

        recv_data = ser.read(5) # SOH、コマンド、応答コード、データ長(L)、データ長(H)
        if recv_data[:3] != bytes([SOH, command, ACK]):
            raise Exception('Format error') 
        payload = ser.read(int.from_bytes(recv_data[-2:], byteorder='little'))
        # Checksum
        if sum(recv_data+payload) != int.from_bytes(ser.read(2), byteorder='little'):
           raise Exception('Invalid checksum') 

    return payload

data = {}

result = send(READ_SERIAL_NUMBER)
data['serial_no'] = int.from_bytes(result , byteorder='little')
logger.info(f"シリアル番号: {hex(data['serial_no'])}")

result = send(READ_CURRENT_VALUE)
data['co2ppm'] = to_co2ppm(int.from_bytes(result[:2], byteorder='little'))
data['temperature'] = to_value(int.from_bytes(result[2:4], byteorder='little'))
data['humidity'] = to_value((int.from_bytes(result[4:6], byteorder='little'))
logger.info(f"CO2 濃度: {data['co2ppm']}ppm, 温度: {data['temperature']}℃, 湿度: {data['humidity']}%RH")

result = send(READ_BATTERY_VOLTAGE)
data['battery_voltage'] = int.from_bytes(result[:2], byteorder='little') / 100
data['dc_voltage'] = int.from_bytes(result[4:6], byteorder='little') / 100
logger.info(f"電池電圧: {data['battery_voltage']}V, DC 電圧: {data['dc_voltage']}V")

logger.debug(json.dumps(data, indent=2))

if UPLOAD_ENABLED:
    import boto3
    import time
    import math
    import uuid

    client = boto3.client('iotsitewise')

    t = math.modf(time.time())
    timestamp = {
        'timeInSeconds': int(t[1]),
        'offsetInNanos': int(t[0] * 1000000000)
    }

    response = client.batch_put_asset_property_value(entries=[{
            'entryId': uuid.uuid4(),
            'propertyAlias': f'/device/tr76ui/{prop}',
            'propertyValues': [
                {
                    'value': {
                        'doubleValue': data[prop]
                    },
                    'timestamp': timestamp
                },
            ]
    } for prop in data])
    logger.debug(json.dumps(response, indent=2))
