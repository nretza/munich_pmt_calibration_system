#!/usr/bin/python3
import ctypes
import numpy as np
from picosdk.ps6000a import ps6000a as ps
from picosdk.PicoDeviceEnums import picoEnum as enums
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok

chandle = ctypes.c_int16()
resolution = enums.PICO_DEVICE_RESOLUTION["PICO_DR_12BIT"]  # 12bit works for 2 channels, "PICO_DR_8BIT" for all 4

class Picoscope:

    def __init__(self):
        self.chandle = chandle
        self.resolution = resolution
        ps.ps6000aOpenUnit(ctypes.byref(self.chandle), None, self.resolution)
