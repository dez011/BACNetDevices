import logging
import socket

from bacpypes.core import run, stop, deferred
from bacpypes.local.device import LocalDeviceObject
from bacpypes.service.device import WhoIsIAmServices
from bacpypes.object import AnalogInputObject, BinaryInputObject
from bacpypes.app import BIPSimpleApplication
from bacpypes.pdu import Address
from threading import Timer
import logging

logging.basicConfig(level=logging.DEBUG)


def create_virtual_device(device_id=12345, port=47808):
    this_device = LocalDeviceObject(
        objectName = "RoomController",
        objectIdentifier= ("device", device_id),
        maxApduLengthAcepted = 1024,
        segmentationSupported = "segmentedBoth",
        vendorIdentifier = 15
    )

    temp_sensor = AnalogInputObject(
        objectIdentifier=("analogInput", 1),
        objectName="RoomTemp",
        presentValue=70.0,
        units="degreesFahrenheit",
        outOfService=True # allow programmatic control
    )

    fan_output = BinaryInputObject(
        objectIdentifier=("binaryInput", 1),
        objectName="Fan",
        presentValue=0,  # Fan is off initially
        outOfService=True  # allow programmatic control
    )

    this_device.objectList.append(temp_sensor)
    this_device.objectList.append(fan_output)

    # address = Address('192.168.1.100:47808')  # replace with your local IP
    address = Address(f"0.0.0.0:{port}")
    application = BIPSimpleApplication(this_device, address)
    application.add_object(temp_sensor)
    application.add_object(fan_output)
    application.add_capability(WhoIsIAmServices)

    return application, temp_sensor, fan_output

def logic_loop(temp_sensor, fan_output):
    #temperature changing
    temp_sensor.presentValue += 0.5
    if temp_sensor.presentValue > 80.0:
        temp_sensor.presentValue = 68.0

    if temp_sensor.presentValue > 75.0:
        fan_output.presentValue = 1 # Turn fan on
    else:
        fan_output.presentValue = 0 # Turn fan off

    print(f"Temp: {temp_sensor.presentValue:.1f}°F, Fan: {'On' if fan_output.presentValue else 'Off'}")
    print("Python bound to:", socket.gethostbyname(socket.gethostname()))

    Timer(5, deferred, [logic_loop, temp_sensor, fan_output]).start()


if __name__ == "__main__":
    app, temp, fan = create_virtual_device(device_id=12345, port=47808)

    deferred(logic_loop, temp, fan)

    run()
