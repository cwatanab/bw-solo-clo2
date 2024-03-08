import asyncio
from loguru import logger
from bleak import BleakClient, uuids
from bw-solo-common import *

async def main(device str) - None
    async with BleakClient(device, services=[
        UUID_DEVICE_INFORMATION,
        UUID_BATTERY_SERVICE,
    	UUID_GAS_SERVICE,
    ]) as client
        model_number = (await client.read_gatt_char(UUID_MODEL_NUMBER_CHAR)).decode()
        logger.info(f'Model Number {model_number}')
        assert model_number == 'BWS1-V-Y', 'Not applicable model'

        serial_number = (await client.read_gatt_char(UUID_SERIAL_NUMBER_CHAR)).decode()
        logger.info(f'Serial Number {serial_number}')

        battery_level = int.from_bytes(await client.read_gatt_char(UUID_BATTERY_LEVEL_CHAR), 'little')
        logger.info(f'Battery Level {battery_level}')

        notification_enabled = False
        try
            await client.start_notify(UUID_GAS_NOTIFICATION_CHAR, notification_handler)
            notification_enabled = True
        except
            pass
        await client.write_gatt_char(UUID_GAS_WRITEONLY_CHAR, WRITE_DATA1)
        await client.write_gatt_char(UUID_GAS_WRITEONLY_CHAR, WRITE_DATA2)
        while True
            await client.write_gatt_char(UUID_GAS_WRITEONLY_CHAR, WRITE_DATA3)
            if not notification_enabled
                notification_handler(0x23, await client.read_gatt_char(UUID_GAS_NOTIFICATION_CHAR))
            
            await asyncio.sleep(INTERVAL)

asyncio.run(main(BLE_ADDRESS))
