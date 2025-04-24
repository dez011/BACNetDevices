import logging
import socket
from threading import Timer

from bacpypes.core import run, deferred
from bacpypes.local.device import LocalDeviceObject
from bacpypes.app import BIPSimpleApplication
from bacpypes.object import AnalogInputObject, BinaryInputObject
from bacpypes.service.device import WhoIsIAmServices
from bacpypes.service.object import ReadWritePropertyServices, ReadWritePropertyMultipleServices
from bacpypes.pdu import Address
from bacpypes.debugging import ModuleLogger

logging.basicConfig(level=logging.DEBUG)
_debug = 0
_log = ModuleLogger(globals())

# --- Custom Application Class ---
class RoomControllerApplication(BIPSimpleApplication, WhoIsIAmServices, ReadWritePropertyMultipleServices):
    def __init__(self, device, address):
        super().__init__(device, address)
        self.temp_sensor = AnalogInputObject(
            objectIdentifier=("analogInput", 1),
            objectName="RoomTemp",
            presentValue=70.0,
            units="degreesFahrenheit",
            outOfService=True
        )

        self.fan_output = BinaryInputObject(
            objectIdentifier=("binaryInput", 1),
            objectName="Fan",
            presentValue=0,
            outOfService=True
        )

        # Add objects to the device
        self.add_object(self.temp_sensor)
        self.add_object(self.fan_output)

        # Start logic loop
        deferred(self.logic_loop)

        def request(self, apdu):
            BIPSimpleApplication.request(self, apdu)

        def indication(self, apdu):
            BIPSimpleApplication.indication(self, apdu)

        def response(self, apdu):
            BIPSimpleApplication.response(self, apdu)

        def confirmation(self, apdu):
            BIPSimpleApplication.confirmation(self, apdu)

    def logic_loop(self):
        self.temp_sensor.presentValue += 0.5
        if self.temp_sensor.presentValue > 80.0:
            self.temp_sensor.presentValue = 68.0

        self.fan_output.presentValue = 1 if self.temp_sensor.presentValue > 75.0 else 0

        print(f"Temp: {self.temp_sensor.presentValue:.1f}°F, Fan: {'On' if self.fan_output.presentValue else 'Off'}")
        print("Python bound to:", socket.gethostbyname(socket.gethostname()))

        Timer(5, deferred, [self.logic_loop]).start()


# --- Initialization ---
def main():
    if _debug: _log.debug("initialization")

    this_device = LocalDeviceObject(
        objectName="RoomController",
        objectIdentifier=("device", 12345),
        maxApduLengthAccepted=1024,
        segmentationSupported="segmentedBoth",
        vendorIdentifier=15,
        vendorName="B612"
    )

    address = Address("0.0.0.0:47808")
    app = RoomControllerApplication(this_device, address)

    if _debug: _log.debug("running")
    run()

# --- Main Entry ---
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        _log.exception("an error has occurred: %s", e)
    finally:
        _log.debug("finally")
