#!/usr/bin/python3
# from picoscope import ps6000
# from scipy.stats import invweibull
import matplotlib.pyplot as plt
import numpy as np
import time
from scipy.optimize import curve_fit
from scipy import asarray as ar, exp
import serial
import sys

import ctypes
from picosdk.ps6000 import ps6000 as ps


# colored prints
def print_r(text):
    print('\033[0;31m' + text + '\033[0m')


def print_g(text):
    print('\033[0;32m' + text + '\033[0m')


def print_b(text):
    print('\033[0;34m' + text + '\033[0m')


def print_w(text):
    print('\033[1;37m' + text + '\033[0m')


def print_gr(text):
    print('\033[1;30m' + text + '\033[0m')


def print_y(text):
    print('\033[0;33m' + text + '\033[0m')


def make_bold(text):
    return '\033[1m' + text + '\033[0m'


class Scope:
    timebases = {0.2: 0, 0.4: 1, 0.8: 2, 1.6: 3}  # 0.2*2**x

    def __init__(self):
        self.chandle = ctypes.c_int16()
        ps.ps6000OpenUnit(ctypes.byref(self.chandle), None)
        self.timebase = 2

        self.trglvl = 3000  # ADC units
        self.trgchannel = 0  # 0=1=A, 1=2=B, 2=3=C, 3=4=D
        self.trgtype = 2  # 0=ABOVE, 1=BELOW, 2=RISING, 3=FALLING, 4=R+F
        self.autotrig = 10  # ms

        self.vranges = {5: 8, 2: 7, 1: 6, 0.5: 5, 0.2: 4, 0.1: 3, 0.05: 2}
        self.vranges_k = {2: 0.05, 3: 0.1, 4: 0.2, 5: 0.5, 6: 1, 7: 2, 8: 5}
        self.n_captures = 10000
        self.preTriggerSamples = 50
        self.postTriggerSamples = 400
        self.maxsamples = self.preTriggerSamples + self.postTriggerSamples

        # CHANNEL SETUP
        self.enable = [1, 1, 1, 1]
        self.vrange = [5, 0.05, 0.05, 0.05]
        self.coupling = ['50', '50', '50', '50']

    def channel_setup(self, channel, enable, vrange, coupling):
        self.maxsamples = self.preTriggerSamples + self.postTriggerSamples
        if enable == 1 or enable == True:
            vrange = self.vranges[vrange]
            if coupling == '50':
                coupling = 2
            if coupling == 'ac':
                coupling = 0
            if coupling == '1m':
                coupling = 1

            ps.ps6000SetChannel(self.chandle, channel, 1, coupling, vrange, 0, 0)
        else:
            ps.ps6000SetChannel(self.chandle, channel, 0, 2, 8, 0, 0)

    def data_setup(self, channel):
        self.maxsamples = self.preTriggerSamples + self.postTriggerSamples
        data = ((ctypes.c_int16 * self.maxsamples) * self.n_captures)()
        for n in range(self.n_captures):
            ps.ps6000SetDataBufferBulk(self.chandle, channel, ctypes.byref(data[n]), self.maxsamples, n, 0)
        return np.array(data)

    def measurement(self, n_captures=None):
        if n_captures != None: self.n_captures = n_captures
        for ch in [0, 1, 2, 3]:
            self.channel_setup(ch, self.enable[ch], self.vrange[ch], self.coupling[ch])
        # Trigger on channel A, trigger level dependant on voltage range
        ps.ps6000SetSimpleTrigger(self.chandle, 1, self.trgchannel, self.trglvl, 2, 0, self.autotrig)

        # Setting up the time resolution of the scope
        timeIntervalns = ctypes.c_float()
        returnedMaxSamples = ctypes.c_int16()
        ps.ps6000GetTimebase2(self.chandle, self.timebase, self.maxsamples, ctypes.byref(timeIntervalns), 1,
                              ctypes.byref(returnedMaxSamples), 0)

        # Splitting the internal memory into segments
        cmaxSamples = ctypes.c_int32(self.maxsamples)
        ps.ps6000MemorySegments(self.chandle, self.n_captures, ctypes.byref(cmaxSamples))
        ps.ps6000SetNoOfCaptures(self.chandle, self.n_captures)

        # Starting the measurement run
        ps.ps6000RunBlock(self.chandle, self.preTriggerSamples, self.postTriggerSamples, self.timebase,
                          1, None, 0, None, None)

        # Data Setup
        ch0 = ((ctypes.c_int16 * self.maxsamples) * self.n_captures)()
        ch1 = ((ctypes.c_int16 * self.maxsamples) * self.n_captures)()
        ch2 = ((ctypes.c_int16 * self.maxsamples) * self.n_captures)()
        ch3 = ((ctypes.c_int16 * self.maxsamples) * self.n_captures)()
        for i, ch in enumerate([ch0, ch1, ch2, ch3]):
            if self.enable[i] == 1 or self.enable[i] == True:
                for n in range(self.n_captures):
                    ps.ps6000SetDataBufferBulk(self.chandle, i, ctypes.byref(ch[n]), self.maxsamples, n, 0)
                ch = np.array(ch)

        overflow = (ctypes.c_int16 * self.n_captures)()
        cmaxSamples = ctypes.c_int32(self.maxsamples)

        # Checking if measurement run has completed
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            ps.ps6000IsReady(self.chandle, ctypes.byref(ready))

        # Copying data from scope memory into local buffers
        ps.ps6000GetValuesBulk(self.chandle, ctypes.byref(cmaxSamples), 0, self.n_captures - 1, 0, 0,
                               ctypes.byref(overflow))
        return ch0, ch1, ch2, ch3

    def adc2v(self, data, vrange):
        maxADC = ctypes.c_int32(32512)
        vranges = {2: 0.05, 3: 0.1, 4: 0.2, 5: 0.5, 6: 1, 7: 2, 8: 5}
        data = np.array(data)
        data = data * (vranges[vrange] / maxADC.value)
        return data

    def close(self):
        ps.ps6000Stop(self.chandle)
        ps.ps6000CloseUnit(self.chandle)

    def pmt_gaincal(self):
        n_captures = 1000  # 100000
        vrange = 2
        trglvl = -500
        timebase = 0
        preTriggerSamples = 10
        postTriggerSamples = 80
        maxsamples = preTriggerSamples + postTriggerSamples
        ps.ps6000SetChannel(self.chandle, 2, 1, 2, vrange, 0, 0)
        ps.ps6000SetChannel(self.chandle, 0, 0, 2, vrange, 0, 0)
        ps.ps6000SetChannel(self.chandle, 1, 0, 2, vrange, 0, 0)
        ps.ps6000SetChannel(self.chandle, 3, 0, 2, vrange, 0, 0)
        # Trigger on channel A, trigger level dependant on voltage range
        ps.ps6000SetSimpleTrigger(self.chandle, 1, 2, trglvl, 3, 0, 1000)

        # Setting up the time resolution of the scope
        timeIntervalns = ctypes.c_float()
        returnedMaxSamples = ctypes.c_int16()
        ps.ps6000GetTimebase2(self.chandle, timebase, maxsamples, ctypes.byref(timeIntervalns),
                              1, ctypes.byref(returnedMaxSamples), 0)
        print(timeIntervalns, returnedMaxSamples)
        # Splitting the internal memory into segments
        cmaxSamples = ctypes.c_int32(maxsamples)
        ps.ps6000MemorySegments(self.chandle, n_captures, ctypes.byref(cmaxSamples))
        ps.ps6000SetNoOfCaptures(self.chandle, n_captures)

        start = time.time()
        # Starting the measurement run
        ps.ps6000RunBlock(self.chandle, preTriggerSamples, postTriggerSamples, timebase,
                          1, None, 0, None, None)
        # Create a 2-dimensional buffer for every used scope channel on local machine
        pmt = ((ctypes.c_int16 * maxsamples) * n_captures)()
        for n in range(n_captures):
            ps.ps6000SetDataBufferBulk(self.chandle, 2, ctypes.byref(pmt[n]), maxsamples, n, 0)

        overflow = (ctypes.c_int16 * n_captures)()
        cmaxSamples = ctypes.c_int32(maxsamples)

        # Checking if measurement run has completed
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            ps.ps6000IsReady(self.chandle, ctypes.byref(ready))

        print("Run time: %.2f" % (time.time() - start))
        # Copying data from scope memory into local buffers
        ps.ps6000GetValuesBulk(self.chandle, ctypes.byref(cmaxSamples), 0, n_captures - 1, 0, 0,
                               ctypes.byref(overflow))
        return pmt


if __name__ == "__main__":
    scope = Scope()
    Data = np.array(scope.measurement())
    print(Data)
