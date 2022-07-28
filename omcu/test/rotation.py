#!/usr/bin/python3
from devices.Rotation import Rotation
from devices.PSU import PSU1
from utils.util import setup_file_logging
import itertools

setup_file_logging("/home/canada/logfile.log", logging_level=20)

PSU1.Instance().on()
err_count = 0

#TODO: proper pytest stuff

for i in range(3):
    try:
        print(f"rotation {i}")
        Rotation.Instance().go_home()
    except:
        print(f"ERROR in go home run {i}")
        err_count +=1

for i,j in itertools.product(range(5), range(5)):
    try:
        Rotation.Instance().set_position(j*20, i*20)
        posy, posx = Rotation.Instance().get_position()
        print (f"posy: {posy}, posx: {posx}")
    except:
           print(f"ERROR in angular run {i}")
           err_count +=1

for i in range(3):
    try:
        Rotation.Instance().go_home()
    except:
        print(f"ERROR in go home run {i}")
        err_count +=1

print(f"finished process with {err_count} Errors")