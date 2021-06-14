#!/usr/bin/python3
import ctypes
import numpy as np
from picosdk.ps6000a import ps6000a as ps
from picosdk.PicoDeviceEnums import picoEnum as enums
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok
import time


class Picoscope:
    """
    This is a class for the PicoTech Picoscope 6424E
    """

    def __init__(self):
        self.chandle = ctypes.c_int16()
        self.resolution = 1 # /enums.PICO_DEVICE_RESOLUTION["PICO_DR_12BIT"]
        # PICO_DR_8BIT = 0
        # PICO_DR_12BIT = 1
        ps.ps6000aOpenUnit(ctypes.byref(self.chandle), None, self.resolution)  # opens connection
        self.coupling = 50 # /enums.PICO_COUPLING["PICO_DC_50OHM"]
        # PICO_AC = 0, PICO_DC = 1, PICO_DC_50OHM = 50
        self.voltrange = 8
        # 0=PICO_10MV: ±10 mV, 1=PICO_20MV: ±20 mV, 2=PICO_50MV: ±50 mV, 3=PICO_100MV: ±100 mV, 4=PICO_200MV: ±200 mV,
        # 5=PICO_500MV: ±500 mV, 6=PICO_1V: ±1 V, 7=PICO_2V: ±2 V, 8=PICO_5V: ±5 V, 9=PICO_10V: ±10 V,
        # 10=PICO_20V: ±20 V (9 and 10 not for DC_50OHM)
        self.bandwidth = 0  # /enums.PICO_BANDWIDTH_LIMITER["PICO_BW_FULL"]
        # PICO_BW_FULL = 0, PICO_BW_100KHZ = 100000, PICO_BW_20KHZ = 20000, PICO_BW_1MHZ = 1000000,
        # PICO_BW_20MHZ = 20000000, PICO_BW_25MHZ = 25000000, PICO_BW_50MHZ = 50000000, PICO_BW_250MHZ = 250000000,
        # PICO_BW_500MHZ = 500000000

        self.channelA = 0  # enums.PICO_CHANNEL["PICO_CHANNEL_A"]
        self.channelB = 1  # enums.PICO_CHANNEL["PICO_CHANNEL_B"]
        self.channelC = 2  # enums.PICO_CHANNEL["PICO_CHANNEL_C"]
        self.channelD = 3  # enums.PICO_CHANNEL["PICO_CHANNEL_D"]

        self.trigger_direction = 2  # /enums.PICO_THRESHOLD_DIRECTION["PICO_RISING"]
        # PICO_ABOVE = PICO_INSIDE = 0, PICO_BELOW = PICO_OUTSIDE = 1, PICO_RISING = PICO_ENTER = PICO_NONE = 2,
        # PICO_FALLING = PICO_EXIT = 3, PICO_RISING_OR_FALLING = PICO_ENTER_OR_EXIT = 4
        self.autotrigger = 1000  # [us]

        # Set number of samples to be collected
        self.noOfPreTriggerSamples = 2000
        self.noOfPostTriggerSamples = 5000
        self.nSamples = self.noOfPostTriggerSamples + self.noOfPreTriggerSamples

        # Create buffers
        self.bufferAMax = (ctypes.c_int16 * self.nSamples)()
        self.bufferAMin = (ctypes.c_int16 * self.nSamples)()

        # Adc limits
        self.minADC = ctypes.c_int16()
        self.maxADC = ctypes.c_int16()

    def channel_setup(self):
        """
        This is a function to set channel A on and B,C,D off.
        :return:
        """
        # Set channel A on
        # handle = chandle
        # channel = self.channelA
        # coupling = self.coupling
        # channelRange = self.voltrange
        # analogueOffset = 0 V
        # bandwidth = self.bandwidth
        ps.ps6000aSetChannelOn(self.chandle, self.channelA, self.coupling, self.voltrange, 0, self.bandwidth)

        # set channel B,C,D off
        for x in range(1, 3, 1):
            channel = x
            ps.ps6000aSetChannelOff(self.chandle, channel)

    def trigger_setup(self, thresh=1000):
        """
        This is a function to set the trigger on channel A. The threshold can be given in [mV].
        :param thresh: int [mV] trigger value, default value: 1000 mV
        :return:
        """
        # Set simple trigger on channel A, [thresh] mV rising with 1 s autotrigger
        # handle = chandle
        # enable = 1
        source = self.channelA
        # threshold = thresh [mV], default value: 1000 mV
        direction = self.trigger_direction
        # delay = 0 s
        # autoTriggerMicroSeconds = self.autotrigger
        ps.ps6000aSetSimpleTrigger(self.chandle, 1, source, thresh, direction, 0, self.autotrigger)

    def timebase_setup(self):
        """
        This is a function to get the fastest available timebase.
        The timebases allow slow enough sampling in block mode to overlap the streaming sample intervals.
        :return: timebase: int
        """
        # Get fastest available timebase
        # handle = chandle
        enabledChannelFlags = 1  # enums.PICO_CHANNEL_FLAGS["PICO_CHANNEL_A_FLAGS"]
        # PICO_CHANNEL_A_FLAGS = 1, PICO_CHANNEL_B_FLAGS = 2, PICO_CHANNEL_C_FLAGS = 4, PICO_CHANNEL_D_FLAGS = 8
        timebase = ctypes.c_uint32(0)
        timeInterval = ctypes.c_double(0)
        # resolution = resolution
        ps.ps6000aGetMinimumTimebaseStateless(self.chandle, enabledChannelFlags, ctypes.byref(timebase),
                                              ctypes.byref(timeInterval), self.resolution)
        print("timebase = ", timebase.value)
        print("sample interval =", timeInterval.value, "s")
        return timebase.value, timeInterval.value

    def buffer_setup(self):
        """
        This function tells the driver to store the data unprocessed: raw mode (no downsampling).
        :return:
        """
        # Set data buffers
        # handle = chandle
        # channel = channelA
        # bufferMax = bufferAMax
        # bufferMin = bufferAMin
        # nSamples = nSamples
        dataType = enums.PICO_DATA_TYPE["PICO_INT16_T"]  # 16-bit signed integer
        waveform = 0  # segment index
        downSampleMode = enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"]  # No downsampling. Returns raw data values.
        clear = enums.PICO_ACTION["PICO_CLEAR_ALL"]
        add = enums.PICO_ACTION["PICO_ADD"]
        action = clear | add  # PICO_ACTION["PICO_CLEAR_WAVEFORM_CLEAR_ALL"] | PICO_ACTION["PICO_ADD"]
        ps.ps6000aSetDataBuffers(self.chandle, self.channelA, ctypes.byref(self.bufferAMax),
                                 ctypes.byref(self.bufferAMin), self.nSamples, dataType, waveform,
                                 downSampleMode, action)

    def single_measurement(self, thresh=1000):
        """
        This is a function to run a single waveform measurement.
        First, it runs channel_setup() to set channel A on and B,C,D off.
        Then, it runs trigger_setup(thresh) which sets the trigger to a rising edge at the given value [mV].
        Then, it runs timebase_setup() to get the fastest available timebase.
        Then, it runs buffer_setup() to setup the buffer to store the data unprocessed.
        Then a single waveform measurement is taken und written into a file in the folder data.
        :param thresh: int [mV] trigger value, default value: 1000 mV
        :return:
        """
        self.channel_setup()
        self.trigger_setup(thresh)
        timebase, timeInterval = self.timebase_setup()
        self.buffer_setup()

        # Run block capture
        # handle = chandle
        # timebase, timeInterval = self.timebase_setup()
        timeIndisposedMs = ctypes.c_double(0)
        # segmentIndex = 0
        # lpReady = None   Using IsReady rather than a callback
        # pParameter = None
        ps.ps6000aRunBlock(self.chandle, self.noOfPreTriggerSamples, self.noOfPostTriggerSamples, timebase,
                           ctypes.byref(timeIndisposedMs), 0, None, None)

        # Check for data collection to finish using ps6000aIsReady
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            ps.ps6000aIsReady(self.chandle, ctypes.byref(ready))

        # Get data from scope
        # handle = chandle
        # startIndex = 0
        noOfSamples = ctypes.c_uint64(self.nSamples)
        # downSampleRatio = 1
        downSampleMode = enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"]  # # No downsampling. Returns raw data values.
        # segmentIndex = 0
        overflow = ctypes.c_int16(0)
        ps.ps6000aGetValues(self.chandle, 0, ctypes.byref(noOfSamples), 1, downSampleMode, 0,
                            ctypes.byref(overflow))

        # get max ADC value
        # handle = chandle
        ps.ps6000aGetAdcLimits(self.chandle, self.resolution, ctypes.byref(self.minADC), ctypes.byref(self.maxADC))
        # convert ADC counts data to mV
        adc2mVChAMax = adc2mV(self.bufferAMax, self.voltrange, self.maxADC)

        # Create time data
        timevals = np.linspace(0, self.nSamples * timeInterval * 1000000000, self.nSamples)

        # create array of data and save as txt file
        data = np.zeros((self.nSamples, 2))
        for i, values in enumerate(adc2mVChAMax):
            timeval = timevals[i]
            mV = values
            data[i] = [timeval, mV]
        filename = './data/'
        timestr = time.strftime("%Y%m%d-%H%M%S")
        filename += timestr
        filename += '.txt'
        np.savetxt(filename, data, delimiter=' ', newline='\n', header='time data [mV]')

    def close_scope(self):
        """
        This is a function to stop whatever the picoscope is doing and close the connection to it.
        :return:
        """
        ps.ps6000aStop(self.chandle)
        ps.ps6000aCloseUnit(self.chandle)

    def single_measurement_with_setup(self, thresh=1000):
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
        ps.ps6000aSetChannelOn(self.chandle, channelA, coupling, channelRange, 0, bandwidth)

        # set channel B,C,D off
        for x in range(1, 3, 1):
            channel = x
            ps.ps6000aSetChannelOff(self.chandle, channel)

        # Set simple trigger on channel A, [thresh] mV rising with 1 s autotrigger
        # handle = chandle
        # enable = 1
        source = channelA
        threshold = thresh  # [mV], default value: 1000 mV
        direction = enums.PICO_THRESHOLD_DIRECTION["PICO_RISING"]
        # delay = 0 s
        # autoTriggerMicroSeconds = 1000000 us
        ps.ps6000aSetSimpleTrigger(self.chandle, 1, source, threshold, direction, 0, 1000000)

        # Get fastest available timebase
        # handle = chandle
        enabledChannelFlags = enums.PICO_CHANNEL_FLAGS["PICO_CHANNEL_A_FLAGS"]
        timebase = ctypes.c_uint32(0)
        timeInterval = ctypes.c_double(0)
        # resolution = resolution
        ps.ps6000aGetMinimumTimebaseStateless(self.chandle, enabledChannelFlags,ctypes.byref(timebase),
                                              ctypes.byref(timeInterval), self.resolution)
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
        dataType = enums.PICO_DATA_TYPE["PICO_INT16_T"]  # 16-bit signed integer
        waveform = 0
        downSampleMode = enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"]  # No downsampling. Returns raw data values.
        clear = enums.PICO_ACTION["PICO_CLEAR_ALL"]
        add = enums.PICO_ACTION["PICO_ADD"]
        action = clear | add  # PICO_ACTION["PICO_CLEAR_WAVEFORM_CLEAR_ALL"] | PICO_ACTION["PICO_ADD"]
        ps.ps6000aSetDataBuffers(self.chandle, channelA, ctypes.byref(bufferAMax),
                                                            ctypes.byref(bufferAMin), nSamples, dataType, waveform,
                                                            downSampleMode, action)

        # Run block capture
        # handle = chandle
        # timebase = timebase
        timeIndisposedMs = ctypes.c_double(0)
        # segmentIndex = 0
        # lpReady = None   Using IsReady rather than a callback
        # pParameter = None
        ps.ps6000aRunBlock(self.chandle, noOfPreTriggerSamples, noOfPostTriggerSamples, timebase,
                                                ctypes.byref(timeIndisposedMs), 0, None, None)

        # Check for data collection to finish using ps6000aIsReady
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            ps.ps6000aIsReady(self.chandle, ctypes.byref(ready))

        # Get data from scope
        # handle = chandle
        # startIndex = 0
        noOfSamples = ctypes.c_uint64(nSamples)
        # downSampleRatio = 1
        # segmentIndex = 0
        overflow = ctypes.c_int16(0)
        ps.ps6000aGetValues(self.chandle, 0, ctypes.byref(noOfSamples), 1, downSampleMode, 0,
                                                  ctypes.byref(overflow))

        # get max ADC value
        # handle = chandle
        minADC = ctypes.c_int16()
        maxADC = ctypes.c_int16()
        ps.ps6000aGetAdcLimits(self.chandle, self.resolution, ctypes.byref(minADC),
                                                        ctypes.byref(maxADC))

        # convert ADC counts data to mV
        adc2mVChAMax = adc2mV(bufferAMax, channelRange, maxADC)

        # Create time data
        time = np.linspace(0, (nSamples) * timeInterval.value * 1000000000, nSamples)

        # create array of data and save as txt file
        data = np.zeros((nSamples, 2))
        for i, values in enumerate(adc2mVChAMax):
            timeval = time[i]
            mV = values
            data[i] = [timeval, mV]
        np.savetxt('./data/waveform.txt', data, delimiter=' ', newline='\n', header='time data [mV]')

        # plot data from channel A and B
        plt.plot(time, adc2mVChAMax[:])
        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')
        plt.show()

    def block_measurement(self):
        status = {}
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
                                                                                      self.resolution)
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
        status["getAdcLimits"] = ps.ps6000aGetAdcLimits(self.chandle, self.resolution, ctypes.byref(minADC),
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
