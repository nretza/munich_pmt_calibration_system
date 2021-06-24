#
# Copyright (C) 2019 Pico Technology Ltd. See LICENSE file for terms.
#
# ps6000a Series STREAMING MODE EXAMPLE
# This example demonstrates how to call the ps6000a driver API functions in order to open a device, setup 2 channels
# and collects streamed data (1 buffer).
# This data is then plotted as mV against time in ns.

import ctypes
import numpy as np
from picosdk.ps6000a import ps6000a as ps
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok
from picosdk.PicoDeviceEnums import picoEnum as enums
import time

# Create chandle and status ready for use
chandle = ctypes.c_int16()
status = {}

# Open PicoScope 6000 Series device
# Returns handle to chandle for use in future API functions
resolution = enums.PICO_DEVICE_RESOLUTION["PICO_DR_8BIT"]
status["openunit"] = ps.ps6000aOpenUnit(ctypes.byref(chandle), None, resolution)
assert_pico_ok(status["openunit"])



enabled = 1
disabled = 0
analogue_offset = 0.0

# Set up channel A
# handle = chandle
# channel = ps6000a_CHANNEL_A = 0
# enabled = 1
# coupling type = ps6000a_DC = 1
# range = ps6000a_2V = 7
# analogue offset = 0 V
channel_range = 7
bandwidth = enums.PICO_BANDWIDTH_LIMITER["PICO_BW_FULL"]
status["setChA"] = ps.ps6000aSetChannelOn(chandle,
                                        enums.PICO_CHANNEL["PICO_CHANNEL_A"],
                                        enums.PICO_COUPLING["PICO_DC"],
                                        channel_range,
                                        analogue_offset,
										bandwidth)
assert_pico_ok(status["setChA"])

# Set up channel B
# handle = chandle
# channel = ps6000a_CHANNEL_B = 1
# enabled = 1
# coupling type = ps6000a_DC = 1
# range = ps6000a_2V = 7
# analogue offset = 0 V
# bandwidth = enums.PICO_BANDWIDTH_LIMITER["PICO_BW_FULL"]
status["setChB"] = ps.ps6000aSetChannelOn(chandle,
                                        enums.PICO_CHANNEL["PICO_CHANNEL_B"],
                                        enums.PICO_COUPLING["PICO_DC"],
                                        channel_range,
                                        analogue_offset,
										bandwidth)
assert_pico_ok(status["setChB"])

# Size of capture
sizeOfOneBuffer = 500
numBuffersToCapture = 10

totalSamples = sizeOfOneBuffer * numBuffersToCapture

# Create buffers ready for assigning pointers for data collection
bufferAMax = np.zeros(shape=sizeOfOneBuffer, dtype=np.int16)
bufferBMax = np.zeros(shape=sizeOfOneBuffer, dtype=np.int16)

# Set data buffer location for data collection from channel A
# handle = chandle
# source = ps6000a_CHANNEL_A = 0
# pointer to buffer max = ctypes.byref(bufferAMax)
# pointer to buffer min = ctypes.byref(bufferAMin)
# buffer length = maxSamples
dataType = enums.PICO_DATA_TYPE["PICO_INT16_T"]
waveform = 0  # segment index
# ratio mode = ps6000a_RATIO_MODE_NONE = 0
clear = enums.PICO_ACTION["PICO_CLEAR_ALL"]
add = enums.PICO_ACTION["PICO_ADD"]
action = clear | add  # PICO_ACTION["PICO_CLEAR_WAVEFORM_CLEAR_ALL"] | PICO_ACTION["PICO_ADD"]
status["setDataBuffersA"] = ps.ps6000aSetDataBuffers(chandle,
                                                     enums.PICO_CHANNEL["PICO_CHANNEL_A"],
                                                     bufferAMax.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                                                     None,
                                                     sizeOfOneBuffer,
                                                     dataType,
                                                     waveform,
                                                     enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"],
                                                     action)
assert_pico_ok(status["setDataBuffersA"])

# Set data buffer location for data collection from channel B
# handle = chandle
# source = ps6000a_CHANNEL_B = 1
# pointer to buffer max = ctypes.byref(bufferBMax)
# pointer to buffer min = ctypes.byref(bufferBMin)
# buffer length = maxSamples
# segment index = 0
# ratio mode = ps6000a_RATIO_MODE_NONE = 0
status["setDataBuffersB"] = ps.ps6000aSetDataBuffers(chandle,
                                                     enums.PICO_CHANNEL["PICO_CHANNEL_B"],
                                                     bufferBMax.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                                                     None,
                                                     sizeOfOneBuffer,
                                                     dataType,
                                                     waveform,
                                                     enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"],
                                                     action)
assert_pico_ok(status["setDataBuffersB"])

# Get fastest available timebase
# handle = chandle
enabledChannelFlags = enums.PICO_CHANNEL_FLAGS["PICO_CHANNEL_A_FLAGS"]
timebase = ctypes.c_uint32(0)
timeInterval = ctypes.c_double(0)
# resolution = resolution
status["getMinimumTimebaseStateless"] = ps.ps6000aGetMinimumTimebaseStateless(chandle, enabledChannelFlags, ctypes.byref(timebase), ctypes.byref(timeInterval), resolution)
assert_pico_ok(status["getMinimumTimebaseStateless"])
print("timebase = ", timebase.value)
print("sample interval =", timeInterval.value, "s")

# Begin streaming mode:
sampleInterval = ctypes.c_int32(250)
sampleUnits = enums.PICO_TIME_UNITS['PICO_US']
# We are not triggering:
maxPreTriggerSamples = 0
autoStopOn = 1
# No downsampling:
downsampleRatio = 1
status["runStreaming"] = ps.ps6000aRunStreaming(chandle,
                                                ctypes.byref(timeInterval),
                                                sampleUnits,
                                                maxPreTriggerSamples,
                                                totalSamples,
                                                autoStopOn,
                                                downsampleRatio,
                                                enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"],
                                                sizeOfOneBuffer)
assert_pico_ok(status["runStreaming"])

actualSampleInterval = sampleInterval.value
actualSampleIntervalNs = actualSampleInterval * 1000

print("Capturing at sample interval %s ns" % actualSampleIntervalNs)

# We need a big buffer, not registered with the driver, to keep our complete capture in.
bufferCompleteA = np.zeros(shape=totalSamples, dtype=np.int16)
bufferCompleteB = np.zeros(shape=totalSamples, dtype=np.int16)
nextSample = 0
autoStopOuter = False
wasCalledBack = False


def streaming_callback(handle, noOfSamples, startIndex, overflow, triggerAt, triggered, autoStop, param):
    global nextSample, autoStopOuter, wasCalledBack
    wasCalledBack = True
    destEnd = nextSample + noOfSamples
    sourceEnd = startIndex + noOfSamples
    bufferCompleteA[nextSample:destEnd] = bufferAMax[startIndex:sourceEnd]
    bufferCompleteB[nextSample:destEnd] = bufferBMax[startIndex:sourceEnd]
    nextSample += noOfSamples
    if autoStop:
        autoStopOuter = True


# Convert the python function into a C function pointer.
cFuncPtr = ps.StreamingReadyType(streaming_callback)

# Fetch data from the driver in a loop, copying it out of the registered buffers and into our complete one.
while nextSample < totalSamples and not autoStopOuter:
    wasCalledBack = False
    status["getStreamingLastestValues"] = ps.ps6000aGetStreamingLatestValues(chandle, cFuncPtr, None)
    if not wasCalledBack:
        # If we weren't called back by the driver, this means no data is ready. Sleep for a short while before trying
        # again.
        time.sleep(0.01)

print("Done grabbing values.")

# Find maximum ADC count value
# handle = chandle
# pointer to value = ctypes.byref(maxADC)
maxADC = ctypes.c_int16(32512)

# Convert ADC counts data to mV
adc2mVChAMax = adc2mV(bufferCompleteA, channel_range, maxADC)
adc2mVChBMax = adc2mV(bufferCompleteB, channel_range, maxADC)

# Create time data
time = np.linspace(0, (totalSamples) * actualSampleIntervalNs, totalSamples)

# Plot data from channel A and B
plt.plot(time, adc2mVChAMax[:])
plt.plot(time, adc2mVChBMax[:])
plt.xlabel('Time (ns)')
plt.ylabel('Voltage (mV)')
plt.show()

# Stop the scope
# handle = chandle
status["stop"] = ps.ps6000aStop(chandle)
assert_pico_ok(status["stop"])

# Disconnect the scope
# handle = chandle
status["close"] = ps.ps6000aCloseUnit(chandle)
assert_pico_ok(status["close"])

# Display status returns
print(status)