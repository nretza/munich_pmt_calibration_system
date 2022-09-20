from utils.util import measure_occ, setup_file_logging
from utils.testing_procedure import tune_parameters
import matplotlib.pyplot as plt
from devices.Rotation import Rotation
from devices.PSU import PSU1
from devices.HV_supply import HV_supply
from devices.Laser import Laser
import time

setup_file_logging("/home/canada/logfile.log", logging_level=10)

Laser.Instance().on_pulsed()
HV_supply.Instance().on()
PSU1.Instance().on()
Rotation.Instance().go_home()

occs = []
for i in range(100):
    print(f"loop {i}")
    time.sleep(5)
    occs.append(measure_occ())

plt.hist(occs)
plt.show()
