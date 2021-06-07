#!/usr/bin/python3
import ctypes
import numpy as np
from picosdk.ps6000a import ps6000a as ps
from picosdk.PicoDeviceEnums import picoEnum as enums
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok

chandle = ctypes.c_int16()
resolution = enums.PICO_DEVICE_RESOLUTION["PICO_DR_12BIT"]
# "PICO_DR_12BIT" works for 1 or 2 channels, "PICO_DR_8BIT" when 3 or 4 channels are used
status = {}  # dictionary with status reports


class Picoscope:
    """
    This is a class for the PicoTech Picoscope 6424E
    """

    def __init__(self):
        self.chandle = chandle
        self.resolution = resolution
        status["openunit"] = ps.ps6000aOpenUnit(ctypes.byref(self.chandle), None, self.resolution)  # opens connection
        assert_pico_ok(status["openunit"])  # entry to dictionary status

    def single_measurement(self, thresh=1000):
        """
        PS6000 A BLOCK MODE EXAMPLE
        ---
        This example opens a 6000a driver device, sets up channel A and a trigger then collects a block of data.
        This data is then plotted as mV against time in ns.
        :param thresh: int [mV] trigger value
        :return:
        """
        # Set channel A on
        # handle = chandle
        channelA = enums.PICO_CHANNEL["PICO_CHANNEL_A"]
        coupling = enums.PICO_COUPLING["PICO_DC_50OHM"]  # PICO_DC / PICO_AC / PICO_DC_50OHM
        channelRange = 8  # 1: +-20mV, 2: +-50mV, 3: +- 100mV, 4: +- 200mV, 5: +-500mV, 6: +-1V, 7: +-2V, 8: +-5V,
                          # 9: +-10V, 10: +-20V (not for DC_50OHM)
        # analogueOffset = 0 V
        bandwidth = enums.PICO_BANDWIDTH_LIMITER["PICO_BW_FULL"]
        status["setChannelA"] = ps.ps6000aSetChannelOn(self.chandle, channelA, coupling, channelRange, 0, bandwidth)
        assert_pico_ok(status["setChannelA"])

        # set channel B,C,D off
        for x in range(1, 3, 1):
            channel = x
            status["setChannel", x] = ps.ps6000aSetChannelOff(self.chandle, channel)
            assert_pico_ok(status["setChannel", x])

        # Set simple trigger on channel A, [thresh] mV rising with 1 s autotrigger
        # handle = chandle
        # enable = 1
        source = channelA
        threshold = thresh  # [mV], default value: 1000 mV
        direction = enums.PICO_THRESHOLD_DIRECTION["PICO_RISING"]
        # delay = 0 s
        # autoTriggerMicroSeconds = 1000000 us
        status["setSimpleTrigger"] = ps.ps6000aSetSimpleTrigger(self.chandle, 1, source, threshold, direction, 0,
                                                                1000000)
        assert_pico_ok(status["setSimpleTrigger"])

        # Get fastest available timebase
        # handle = chandle
        enabledChannelFlags = enums.PICO_CHANNEL_FLAGS["PICO_CHANNEL_A_FLAGS"]
        timebase = ctypes.c_uint32(0)
        timeInterval = ctypes.c_double(0)
        # resolution = resolution
        status["getMinimumTimebaseStateless"] = ps.ps6000aGetMinimumTimebaseStateless(self.chandle, enabledChannelFlags,
                                                                                      ctypes.byref(timebase),
                                                                                      ctypes.byref(timeInterval),
                                                                                      resolution)
        print("timebase = ", timebase.value)
        print("sample interval =", timeInterval.value, "s")

        # Set number of samples to be collected
        noOfPreTriggerSamples = 2000
        noOfPostTriggerSamples = 5000
        nSamples = noOfPostTriggerSamples + noOfPreTriggerSamples

        # Create buffers
        bufferAMax = (ctypes.c_int16 * nSamples)()
        bufferAMin = (ctypes.c_int16 * nSamples)()  # used for downsampling which isn't in the scope of this example

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
        status["setDataBuffers"] = ps.ps6000aSetDataBuffers(self.chandle, channelA, ctypes.byref(bufferAMax),
                                                            ctypes.byref(bufferAMin), nSamples, dataType, waveform,
                                                            downSampleMode, action)
        assert_pico_ok(status["setDataBuffers"])

        # Run block capture
        # handle = chandle
        # timebase = timebase
        timeIndisposedMs = ctypes.c_double(0)
        # segmentIndex = 0
        # lpReady = None   Using IsReady rather than a callback
        # pParameter = None
        status["runBlock"] = ps.ps6000aRunBlock(self.chandle, noOfPreTriggerSamples, noOfPostTriggerSamples, timebase,
                                                ctypes.byref(timeIndisposedMs), 0, None, None)
        assert_pico_ok(status["runBlock"])

        # Check for data collection to finish using ps6000aIsReady
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            status["isReady"] = ps.ps6000aIsReady(self.chandle, ctypes.byref(ready))

        # Get data from scope
        # handle = chandle
        # startIndex = 0
        noOfSamples = ctypes.c_uint64(nSamples)
        # downSampleRatio = 1
        # segmentIndex = 0
        overflow = ctypes.c_int16(0)
        status["getValues"] = ps.ps6000aGetValues(self.chandle, 0, ctypes.byref(noOfSamples), 1, downSampleMode, 0,
                                                  ctypes.byref(overflow))
        assert_pico_ok(status["getValues"])

        # get max ADC value
        # handle = chandle
        minADC = ctypes.c_int16()
        maxADC = ctypes.c_int16()
        status["getAdcLimits"] = ps.ps6000aGetAdcLimits(self.chandle, resolution, ctypes.byref(minADC),
                                                        ctypes.byref(maxADC))
        assert_pico_ok(status["getAdcLimits"])

        # convert ADC counts data to mV
        adc2mVChAMax = adc2mV(bufferAMax, channelRange, maxADC)

        # Create time data
        time = np.linspace(0, (nSamples) * timeInterval.value * 1000000000, nSamples)

        # create array of data
        data = np.zeros((nSamples, 2))
        for i, values in enumerate(adc2mVChAMax):
            timeval = time[i]
            mV = values
            data[i] = [timeval, mV]
        np.savetxt('data.txt', data)

        # plot data from channel A and B
        plt.plot(time, adc2mVChAMax[:])
        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')
        plt.show()

        print(status)

    def block_measurement(self):
        # Set channel A on
        # handle = chandle
        channelA = enums.PICO_CHANNEL["PICO_CHANNEL_A"]
        coupling = enums.PICO_COUPLING["PICO_DC_50OHM"]  # PICO_DC / PICO_AC / PICO_DC_50OHM
        channelRange = 8  # 1: +-20mV, 2: +-50mV, 3: +- 100mV, 4: +- 200mV, 5: +-500mV, 6: +-1V, 7: +-2V, 8: +-5V,
        # 9: +-10V, 10: +-20V (not for DC_50OHM)
        # analogueOffset = 0 V
        bandwidth = enums.PICO_BANDWIDTH_LIMITER["PICO_BW_FULL"]
        status["setChannelA"] = ps.ps6000aSetChannelOn(self.chandle, channelA, coupling, channelRange, 0, bandwidth)
        assert_pico_ok(status["setChannelA"])

        # set channel B,C,D off
        for x in range(1, 3, 1):
            channel = x
            status["setChannel", x] = ps.ps6000aSetChannelOff(self.chandle, channel)
            assert_pico_ok(status["setChannel", x])

        # Set simple trigger on channel A, 1 V rising with 1 s autotrigger
        # handle = chandle
        # enable = 1
        source = channelA
        # threshold = 1000 mV
        direction = enums.PICO_THRESHOLD_DIRECTION["PICO_RISING"]
        # delay = 0 s
        # autoTriggerMicroSeconds = 1000000 us
        status["setSimpleTrigger"] = ps.ps6000aSetSimpleTrigger(self.chandle, 1, source, 1000, direction, 0, 1000000)
        assert_pico_ok(status["setSimpleTrigger"])

        # Get fastest available timebase
        # handle = chandle
        enabledChannelFlags = enums.PICO_CHANNEL_FLAGS["PICO_CHANNEL_A_FLAGS"]
        timebase = ctypes.c_uint32(0)
        timeInterval = ctypes.c_double(0)
        # resolution = resolution
        status["getMinimumTimebaseStateless"] = ps.ps6000aGetMinimumTimebaseStateless(self.chandle, enabledChannelFlags,
                                                                                      ctypes.byref(timebase),
                                                                                      ctypes.byref(timeInterval),
                                                                                      resolution)
        assert_pico_ok(status["getMinimumTimebaseStateless"])
        print("timebase = ", timebase.value)
        print("sample interval =", timeInterval.value, "s")

        # Set number of samples to be collected
        noOfPreTriggerSamples = 2000
        noOfPostTriggerSamples = 4000
        nSamples = noOfPostTriggerSamples + noOfPreTriggerSamples

        # Set number of memory segments
        noOfCaptures = 10
        maxSegments = ctypes.c_uint64(10)
        status["memorySegments"] = ps.ps6000aMemorySegments(self.chandle, noOfCaptures, ctypes.byref(maxSegments))
        assert_pico_ok(status["memorySegments"])

        # Set number of captures
        status["setNoOfCaptures"] = ps.ps6000aSetNoOfCaptures(self.chandle, noOfCaptures)
        assert_pico_ok(status["setNoOfCaptures"])

        # Create buffers
        bufferAMax = (ctypes.c_int16 * nSamples)()
        bufferAMin = (ctypes.c_int16 * nSamples)()  # used for downsampling which isn't in the scope of this example
        bufferAMax1 = (ctypes.c_int16 * nSamples)()
        bufferAMin1 = (ctypes.c_int16 * nSamples)()  # used for downsampling which isn't in the scope of this example
        bufferAMax2 = (ctypes.c_int16 * nSamples)()
        bufferAMin2 = (ctypes.c_int16 * nSamples)()  # used for downsampling which isn't in the scope of this example
        bufferAMax3 = (ctypes.c_int16 * nSamples)()
        bufferAMin3 = (ctypes.c_int16 * nSamples)()  # used for downsampling which isn't in the scope of this example
        bufferAMax4 = (ctypes.c_int16 * nSamples)()
        bufferAMin4 = (ctypes.c_int16 * nSamples)()  # used for downsampling which isn't in the scope of this example
        bufferAMax5 = (ctypes.c_int16 * nSamples)()
        bufferAMin5 = (ctypes.c_int16 * nSamples)()  # used for downsampling which isn't in the scope of this example
        bufferAMax6 = (ctypes.c_int16 * nSamples)()
        bufferAMin6 = (ctypes.c_int16 * nSamples)()  # used for downsampling which isn't in the scope of this example
        bufferAMax7 = (ctypes.c_int16 * nSamples)()
        bufferAMin7 = (ctypes.c_int16 * nSamples)()  # used for downsampling which isn't in the scope of this example
        bufferAMax8 = (ctypes.c_int16 * nSamples)()
        bufferAMin8 = (ctypes.c_int16 * nSamples)()  # used for downsampling which isn't in the scope of this example
        bufferAMax9 = (ctypes.c_int16 * nSamples)()
        bufferAMin9 = (ctypes.c_int16 * nSamples)()  # used for downsampling which isn't in the scope of this example

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
        status["setDataBuffers"] = ps.ps6000aSetDataBuffers(self.chandle, channelA, ctypes.byref(bufferAMax),
                                                            ctypes.byref(bufferAMin), nSamples, dataType, waveform,
                                                            downSampleMode, action)
        assert_pico_ok(status["setDataBuffers"])
        waveform1 = 1
        status["setDataBuffers1"] = ps.ps6000aSetDataBuffers(self.chandle, channelA, ctypes.byref(bufferAMax1),
                                                             ctypes.byref(bufferAMin1), nSamples, dataType, waveform1,
                                                             downSampleMode, add)
        assert_pico_ok(status["setDataBuffers1"])
        waveform2 = 2
        status["setDataBuffers2"] = ps.ps6000aSetDataBuffers(self.chandle, channelA, ctypes.byref(bufferAMax2),
                                                             ctypes.byref(bufferAMin2), nSamples, dataType, waveform2,
                                                             downSampleMode, add)
        assert_pico_ok(status["setDataBuffers2"])
        waveform3 = 3
        status["setDataBuffers3"] = ps.ps6000aSetDataBuffers(self.chandle, channelA, ctypes.byref(bufferAMax3),
                                                             ctypes.byref(bufferAMin3), nSamples, dataType, waveform3,
                                                             downSampleMode, add)
        assert_pico_ok(status["setDataBuffers3"])
        waveform4 = 4
        status["setDataBuffers4"] = ps.ps6000aSetDataBuffers(self.chandle, channelA, ctypes.byref(bufferAMax4),
                                                             ctypes.byref(bufferAMin4), nSamples, dataType, waveform4,
                                                             downSampleMode, add)
        assert_pico_ok(status["setDataBuffers4"])
        waveform5 = 5
        status["setDataBuffers5"] = ps.ps6000aSetDataBuffers(self.chandle, channelA, ctypes.byref(bufferAMax5),
                                                             ctypes.byref(bufferAMin5), nSamples, dataType, waveform5,
                                                             downSampleMode, add)
        assert_pico_ok(status["setDataBuffers5"])
        waveform6 = 6
        status["setDataBuffers6"] = ps.ps6000aSetDataBuffers(self.chandle, channelA, ctypes.byref(bufferAMax6),
                                                             ctypes.byref(bufferAMin6), nSamples, dataType, waveform6,
                                                             downSampleMode, add)
        assert_pico_ok(status["setDataBuffers6"])
        waveform7 = 7
        status["setDataBuffers7"] = ps.ps6000aSetDataBuffers(self.chandle, channelA, ctypes.byref(bufferAMax7),
                                                             ctypes.byref(bufferAMin7), nSamples, dataType, waveform7,
                                                             downSampleMode, add)
        assert_pico_ok(status["setDataBuffers7"])
        waveform8 = 8
        status["setDataBuffers8"] = ps.ps6000aSetDataBuffers(self.chandle, channelA, ctypes.byref(bufferAMax8),
                                                             ctypes.byref(bufferAMin8), nSamples, dataType, waveform8,
                                                             downSampleMode, add)
        assert_pico_ok(status["setDataBuffers8"])
        waveform9 = 9
        status["setDataBuffers9"] = ps.ps6000aSetDataBuffers(self.chandle, channelA, ctypes.byref(bufferAMax9),
                                                             ctypes.byref(bufferAMin9), nSamples, dataType, waveform9,
                                                             downSampleMode, add)
        assert_pico_ok(status["setDataBuffers9"])

        # Run block capture
        # handle = chandle
        # timebase = timebase
        timeIndisposedMs = ctypes.c_double(0)
        # segmentIndex = 0
        # lpReady = None   Using IsReady rather than a callback
        # pParameter = None
        status["runBlock"] = ps.ps6000aRunBlock(self.chandle, noOfPreTriggerSamples, noOfPostTriggerSamples, timebase,
                                                ctypes.byref(timeIndisposedMs), 0, None, None)
        assert_pico_ok(status["runBlock"])

        # Check for data collection to finish using ps6000aIsReady
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            status["isReady"] = ps.ps6000aIsReady(self.chandle, ctypes.byref(ready))

        # Get data from scope
        # handle = chandle
        # startIndex = 0
        noOfSamples = ctypes.c_uint64(nSamples)
        # downSampleRatio = 1
        # segmentIndex = 0
        # Creates a overflow location for each segment
        overflow = (ctypes.c_int16 * 10)()
        status["getValues"] = ps.ps6000aGetValuesBulk(self.chandle, 0, ctypes.byref(noOfSamples), 0, 9, 1,
                                                      downSampleMode,
                                                      ctypes.byref(overflow))
        assert_pico_ok(status["getValues"])

        # get max ADC value
        # handle = chandle
        minADC = ctypes.c_int16()
        maxADC = ctypes.c_int16()
        status["getAdcLimits"] = ps.ps6000aGetAdcLimits(self.chandle, resolution, ctypes.byref(minADC),
                                                        ctypes.byref(maxADC))
        assert_pico_ok(status["getAdcLimits"])

        # convert ADC counts data to mV
        adc2mVChAMax = adc2mV(bufferAMax, channelRange, maxADC)
        adc2mVChAMax1 = adc2mV(bufferAMax1, channelRange, maxADC)
        adc2mVChAMax2 = adc2mV(bufferAMax2, channelRange, maxADC)
        adc2mVChAMax3 = adc2mV(bufferAMax3, channelRange, maxADC)
        adc2mVChAMax4 = adc2mV(bufferAMax4, channelRange, maxADC)
        adc2mVChAMax5 = adc2mV(bufferAMax5, channelRange, maxADC)
        adc2mVChAMax6 = adc2mV(bufferAMax6, channelRange, maxADC)
        adc2mVChAMax7 = adc2mV(bufferAMax7, channelRange, maxADC)
        adc2mVChAMax8 = adc2mV(bufferAMax8, channelRange, maxADC)
        adc2mVChAMax9 = adc2mV(bufferAMax9, channelRange, maxADC)

        # Create time data
        time = np.linspace(0, (nSamples) * timeInterval.value * 1000000000, nSamples)

        # plot data from channel A and B
        plt.plot(time, adc2mVChAMax[:])
        plt.plot(time, adc2mVChAMax1[:])
        plt.plot(time, adc2mVChAMax2[:])
        plt.plot(time, adc2mVChAMax3[:])
        plt.plot(time, adc2mVChAMax4[:])
        plt.plot(time, adc2mVChAMax5[:])
        plt.plot(time, adc2mVChAMax6[:])
        plt.plot(time, adc2mVChAMax7[:])
        plt.plot(time, adc2mVChAMax8[:])
        plt.plot(time, adc2mVChAMax9[:])
        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')
        plt.show()

        print(status)
