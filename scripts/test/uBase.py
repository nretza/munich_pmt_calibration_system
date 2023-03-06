import os
import config
from devices.uBase import uBase
from devices.Rotation import Rotation
from devices.Picoscope import Picoscope
from devices.Laser import Laser
from utils.util import setup_file_logging

laser_tune = 715
HV = 85

uBase_name = input("Enter uBase Name: ")
datapath = os.path.join(config.OUT_PATH, "uBase")
filepath = os.path.join(datapath, uBase_name)
os.makedirs(filepath)
setup_file_logging(os.path.join(filepath, "out.log"), 10)


Rotation.Instance().go_home()
Laser.Instance().off_pulsed()

print()
print(">> Attemting to connect to uBase")
uBase.Instance()
print(f"UID: {uBase.Instance().getUID()}")
print(f"AVGReport: {uBase.Instance().getAvgReport()}")
print(">> Connection successfull")
print()

print(">> Measuring at Dy10=0V")
dataset = Picoscope.Instance().block_measurement(10000)
dataset.meassure_metadict(-4)
dataset.setFilepath(filepath)
dataset.setFilename("0_Dy10.hdf5")
dataset.write_to_file()
print(">> Data written to file")
dataset.plot_hist("amplitude_all")
print(">> noise histogram plotted")
print()

print(f">> Measuring at Dy10={HV}V")
uBase.Instance().SetVoltage(HV)
dataset = Picoscope.Instance().block_measurement(10000)
dataset.meassure_metadict(-4)
dataset.setFilepath(filepath)
dataset.setFilename(f"{HV}_Dy10.hdf5")
dataset.write_to_file()
print(">> Data written to file")
dataset.plot_hist("amplitude_all")
print(">> noise histogram plotted")
print()

print(">> turning laser on")
Laser.Instance().on_pulsed()
Laser.Instance().set_tune_value(laser_tune)
print(f">> tuned laser to {laser_tune}")
print()

print(f">> Measuring at Dy10={HV}V")
uBase.Instance().SetVoltage(HV)
dataset = Picoscope.Instance().block_measurement(10000)
dataset.meassure_metadict(-4)
dataset.setFilepath(filepath)
dataset.setFilename(f"{HV}_Dy10_laser_on.hdf5")
dataset.write_to_file()
print(">> Data written to file")
dataset.plot_hist("amplitude_all")
dataset.filter_by_threshold(-4)
dataset.plot_average_wfs()
print(">> noise histogram and average wf plotted")
print()







