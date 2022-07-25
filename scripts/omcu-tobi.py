#!/usr/bin/python3
# Author:  Tobias Pertl <tobias.pertl@tum.de>

from devices.Picoscope import Picoscope
from devices.Picoamp import Picoamp
from devices.PSU import PSU
from devices.Laser import Laser
from devices.Rotation import Rotation
from util.Occupancy import Occupancy
import time
import os
import numpy as np
import h5py


Ps = Picoscope()
##PSU0 = PSU(dev="/dev/PSU_0")
PSU1 = PSU(dev="/dev/PSU_1")
Rot = Rotation()
L = Laser()
oc = Occupancy()

##PSU0.settings(1, voltage=12.0, current=3.0)
PSU1.settings(1, voltage=12.0, current=1.5)
##V0ctrl = 3.6  # HV_out = Vctrl*250
##Psu1.settings(2, voltage=V0ctrl, current=0.1)  # psu for PMT, Vcontrol
##PSU0.on()
PSU1.on()
L.on_pulsed()



PMT = 'PMT-Base-Test1'
timestr = time.strftime("%Y%m%d-%H%M%S")
print(timestr)
directory = 'data/' + Tobi + PMT + timestr
os.mkdir(directory)
suf = '.hdf5'
filename = PMT + suf
filename_with_folder = directory + '/' + filename
h5 = h5py.File(filename_with_folder, 'w')





##data_sgnl, data_trg = Ps.block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=2000, number=100)

print(f'home')
Rot.go_home()
time.sleep(1)


Vctrl = np.arange(3.6, 5.6, 0.4)
##HV = np.arange(1000, 1600, 100)
number = 100000
nSamples = Ps.get_nSamples()
t1 = time.time()



##h5.create_dataset   Here!!!



for i in range(0, 100, 10):
    print(f'move to {i} degree')
    Rot.set_theta(i)
    time.sleep(1)
    for V in Vctrl:
    	Psu1.settings(2, voltage=V, current=0.1)
    	hv = int(round(V*250))
    	print('HV =', hv)
    	time.sleep(0.1)
    	data_sgnl, data_trg  = Ps.block_measurement(trgchannel=0, sgnlchannel=2, number=number)
    	Pa_data = Pa.read_ch1(100) 
    	arr_sgnl = h5.create_dataset(f"HV{hv}/signal", (number, nSamples, 2), 'f')
    	arr_sgnl[:] = data_sgnl
    	arr_trg = h5.create_dataset(f"HV{hv}/trigger", (number, nSamples, 2), 'f')
    	arr_trg[:] = data_trg
    	arr_Pa = h5.create_dataset(f"HV{hv}/pa", (100, 2), 'f')
    	arr_Pa[:] = Pa_data
    	#arr_sgnl.attrs['Vctrl'] = f"{V}"
    	#arr_sgnl.attrs['HV'] = f"{hv}"
    	#arr_sgnl.attrs['Position'] = 'Home'
    	#arr_sgnl.attrs['Baseline'] = 'yes'
    	#arr_sgnl.attrs['Units_voltage'] = 'mV'
    	#arr_sgnl.attrs['Units_time'] = 'ns'
    	Ps.stop_scope()
    	time.sleep(1)

print(f'home')    
Rot.go_home()

h5.close()
Ps.close_scope()
PSU1.off()
##PSU0.off()
L.off_pulsed()
