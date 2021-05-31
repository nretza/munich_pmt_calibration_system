#!/usr/bin/python3
import ctypes
import numpy as np
from picosdk.ps6000a import ps6000a as ps
from picosdk.PicoDeviceEnums import picoEnum as enums
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok

chandle = ctypes.c_int16()
resolution = enums.PICO_DEVICE_RESOLUTION["PICO_DR_12BIT"]  # 12bit works for 2 channels, "PICO_DR_8BIT" for all 4
status = {}

class Picoscope:

    def __init__(self):
        self.chandle = chandle
        self.resolution = resolution
        status["openunit"] = ps.ps6000aOpenUnit(ctypes.byref(self.chandle), None, self.resolution)
        assert_pico_ok(status["openunit"])

    def set_ch_on(self):
        # Set channel A on
        # handle = chandle
        channelA = enums.PICO_CHANNEL["PICO_CHANNEL_A"]
        coupling = enums.PICO_COUPLING["PICO_DC"]
        channelRange = 7  # defines the voltage range that can be displayed, 0-1000mV
        # analogueOffset = 0 V
        bandwidth = enums.PICO_BANDWIDTH_LIMITER["PICO_BW_FULL"]
        status["setChannelA"] = ps.ps6000aSetChannelOn(self.chandle, channelA, coupling, channelRange, 0, bandwidth)
        assert_pico_ok(status["setChannelA"])
        print(status)