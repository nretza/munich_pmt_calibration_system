#
# Copyright (C) 2020 Pico Technology Ltd. See LICENSE file for terms.
#
# PS6000 A BLOCK MODE EXAMPLE
# This example opens a 6000a driver device, sets up two channels and a trigger then collects a block of data.
# This data is then plotted as mV against time in ns.

import ctypes
import numpy as np
from picosdk.ps6000a import ps6000a as ps
from picosdk.PicoDeviceEnums import picoEnum as enums
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok, splitMSODataFast

# Create chandle and status ready for use
chandle = ctypes.c_int16()

# Open 6000 A series PicoScope
# returns handle to chandle for use in future API functions
resolution = enums.PICO_DEVICE_RESOLUTION["PICO_DR_8BIT"]
ps.ps6000aOpenUnit(ctypes.byref(chandle), None, resolution)

# Set channel A on
# handle = chandle
channelA = enums.PICO_CHANNEL["PICO_CHANNEL_A"]
coupling = enums.PICO_COUPLING["PICO_DC"]
channelRange = 7
# analogueOffset = 0 V
bandwidth = enums.PICO_BANDWIDTH_LIMITER["PICO_BW_FULL"]
ps.ps6000aSetChannelOn(chandle, channelA, coupling, channelRange, 0, bandwidth)

# set channel B, C, D off
for x in range(1, 3, 1):
    channel = x
    ps.ps6000aSetChannelOff(chandle, channel)

# set MSO pod 1 on
# handle = chandle
port = enums.PICO_CHANNEL["PICO_PORT0"]
# logic level needs to be set individually for all digital channels/pins in the port
pins = 8
logicThresholdLevel = (ctypes.c_int16 * pins)(0)
logicThresholdLevel[0] = 1000
logicThresholdLevelLength = len(logicThresholdLevel)
hysteresis = enums.PICO_DIGITAL_PORT_HYSTERESIS["PICO_LOW_50MV"]
ps.ps6000aSetDigitalPortOn(chandle, port, ctypes.byref(logicThresholdLevel),
                                                        logicThresholdLevelLength, hysteresis)

# Set MSO pod 2 off
port2 = enums.PICO_CHANNEL["PICO_PORT1"]
ps.ps6000aSetDigitalPortOff(chandle, port2)

# Set simple trigger on channel A, 1 V rising with 1 s autotrigger
# handle = chandle
# enable = 1
source = channelA
# threshold = 1000 mV
direction = enums.PICO_THRESHOLD_DIRECTION["PICO_RISING"]
# delay = 0 s
# autoTriggerMicroSeconds = 1000000 us
ps.ps6000aSetSimpleTrigger(chandle, 1, source, 1000, direction, 0, 1000000)

# Set number of samples to be collected
noOfPreTriggerSamples = 500000
noOfPostTriggerSamples = 1000000
nSamples = noOfPostTriggerSamples + noOfPreTriggerSamples

# Check timebase is valid
# handle = chandle
timebase = ctypes.c_uint32(1)
timeInterval = ctypes.c_double(0)
returnedMaxSamples = ctypes.c_uint64()
# segment = 0
ps.ps6000aGetTimebase(chandle, timebase, nSamples, ctypes.byref(timeInterval),
                                              ctypes.byref(returnedMaxSamples), 0)
print("timebase = ", timebase.value)
print("sample interval =", timeInterval.value, "ns")

# Create buffers
bufferAMax = (ctypes.c_int16 * nSamples)()
bufferAMin = (ctypes.c_int16 * nSamples)()  # used for downsampling which isn't in the scope of this example

bufferDPort0Max = (ctypes.c_int16 * nSamples)()
bufferDPort0Min = (ctypes.c_int16 * nSamples)()

# Set data buffers
# handle = chandle
# channel = channelA
# bufferMax = bufferAMax
# bufferMin = bufferAMin
# nSamples = nSamples
dataType = enums.PICO_DATA_TYPE["PICO_INT16_T"]
waveform = 0
downSampleMode = enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"]
clear = enums.PICO_ACTION["PICO_CLEAR_ALL"]
add = enums.PICO_ACTION["PICO_ADD"]
action = clear | add  # PICO_ACTION["PICO_CLEAR_WAVEFORM_CLEAR_ALL"] | PICO_ACTION["PICO_ADD"]
ps.ps6000aSetDataBuffers(chandle, channelA, ctypes.byref(bufferAMax),
                                                       ctypes.byref(bufferAMin), nSamples, dataType, waveform,
                                                       downSampleMode, action)

ps.ps6000aSetDataBuffers(chandle, port, ctypes.byref(bufferDPort0Max),
                                                       ctypes.byref(bufferDPort0Min), nSamples, dataType, waveform,
                                                       downSampleMode, action)

# Run block capture
# handle = chandle
# timebase = timebase
timeIndisposedMs = ctypes.c_double(0)
# segmentIndex = 0
# lpReady = None   Using IsReady rather than a callback
# pParameter = None
ps.ps6000aRunBlock(chandle, noOfPreTriggerSamples, noOfPostTriggerSamples, timebase,
                                        ctypes.byref(timeIndisposedMs), 0, None, None)

# Check for data collection to finish using ps5000aIsReady
ready = ctypes.c_int16(0)
check = ctypes.c_int16(0)
while ready.value == check.value:
    ps.ps6000aIsReady(chandle, ctypes.byref(ready))

# Get data from scope
# handle = chandle
# startIndex = 0
noOfSamples = ctypes.c_uint64(nSamples)
# downSampleRatio = 1
# segmentIndex = 0
overflow = ctypes.c_int16(0)
ps.ps6000aGetValues(chandle, 0, ctypes.byref(noOfSamples), 1, downSampleMode, 0,
                                          ctypes.byref(overflow))

# get max ADC value
# handle = chandle
minADC = ctypes.c_int16()
maxADC = ctypes.c_int16()
ps.ps6000aGetAdcLimits(chandle, resolution, ctypes.byref(minADC), ctypes.byref(maxADC))

# convert ADC counts data to mV
adc2mVChAMax = adc2mV(bufferAMax, channelRange, maxADC)

# Obtain binary for Digital Port 0
# The tuple returned contains the channels in order (D7, D6, D5, ... D0).
bufferDPort0 = splitMSODataFast(noOfSamples, bufferDPort0Max)

# Create time data
time = np.linspace(0, (nSamples) * timeInterval.value * 1000000000, nSamples)

# plot data from channel A and B
plt.figure(num='Channel A Data')
plt.plot(time, adc2mVChAMax[:])
plt.xlabel('Time (ns)')
plt.ylabel('Voltage (mV)')
plt.title('Channel A data')
# plt.show()

# Plot the data from digital channels onto a graph
plt.figure(num='Digital Port 0 Data')
plt.title('Plot of Digital Port 0 digital channels vs. time')
plt.plot(time, bufferDPort0[0], label='D7')  # D7 is the first array in the tuple.
plt.plot(time, bufferDPort0[1], label='D6')
plt.plot(time, bufferDPort0[2], label='D5')
plt.plot(time, bufferDPort0[3], label='D4')
plt.plot(time, bufferDPort0[4], label='D3')
plt.plot(time, bufferDPort0[5], label='D2')
plt.plot(time, bufferDPort0[6], label='D1')
plt.plot(time, bufferDPort0[7], label='D0')  # D0 is the last array in the tuple.
plt.xlabel('Time (ns)')
plt.ylabel('Logic Level')
plt.legend(loc="upper right")
plt.show()

# Close the scope
ps.ps6000aCloseUnit(chandle)
