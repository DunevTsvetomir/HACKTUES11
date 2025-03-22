import asyncio
from bleak import BleakScanner, BleakClient

async def discover_services(address):
    async with BleakClient(address) as client:
        services = await client.get_services()
        for service in services:
            print(f"Service: {service.uuid}")
            for characteristic in service.characteristics:
                print(f"  Characteristic: {characteristic.uuid}")
                print(f"    Properties: {characteristic.properties}")

async def main():
    print("Scanning for devices...")
    devices = await BleakScanner.discover()
    for i, device in enumerate(devices):
        print(f"{i}: {device.name} ({device.address})")

    # Ask the user to select a device
    device_index = int(input("Select a device by index: "))
    address = devices[device_index].address

    print(f"Connecting to {address}...")
    await discover_services(address)

asyncio.run(main())