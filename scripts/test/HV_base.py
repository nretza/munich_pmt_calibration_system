import time
from devices.HV_base import HV_base
from devices.Rotation import Rotation
from devices.PSU import PSU1
from utils.util import setup_file_logging
setup_file_logging("/home/canada/Desktop/logger.log", 10)


PSU1.Instance().on()
Rotation.Instance().go_home()

print("UID:")
print(HV_base.Instance().getUID())
print("AVGReport:")
print(HV_base.Instance().getAvgReport())

HV = 0
while True:
    _ = input(f"\nSet Dy10 to {HV}")
    HV_base.Instance().setDy10(HV)
    time.sleep(2)
    print("AVGReport:")
    print(HV_base.Instance().getAvgReport())
    HV += 5