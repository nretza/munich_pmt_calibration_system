#!/usr/bin/python3
import ctypes
import numpy as np
from numpy import trapz
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
        self.resolution = 1  # /enums.PICO_DEVICE_RESOLUTION["PICO_DR_12BIT"]
        # PICO_DR_8BIT = 0
        # PICO_DR_12BIT = 1
        ps.ps6000aOpenUnit(ctypes.byref(self.chandle), None, self.resolution)  # opens connection
        self.coupling = 50  # /enums.PICO_COUPLING["PICO_DC_50OHM"]
        # PICO_AC = 0, PICO_DC = 1, PICO_DC_50OHM = 50
        self.voltrange = 8
        # 0=PICO_10MV: ±10 mV, 1=PICO_20MV: ±20 mV, 2=PICO_50MV: ±50 mV, 3=PICO_100MV: ±100 mV, 4=PICO_200MV: ±200 mV,
        # 5=PICO_500MV: ±500 mV, 6=PICO_1V: ±1 V, 7=PICO_2V: ±2 V, 8=PICO_5V: ±5 V, 9=PICO_10V: ±10 V,
        # 10=PICO_20V: ±20 V (9 and 10 not for DC_50OHM)
        self.bandwidth = 0  # /enums.PICO_BANDWIDTH_LIMITER["PICO_BW_FULL"]
        # PICO_BW_FULL = 0, PICO_BW_100KHZ = 100000, PICO_BW_20KHZ = 20000, PICO_BW_1MHZ = 1000000,
        # PICO_BW_20MHZ = 20000000, PICO_BW_25MHZ = 25000000, PICO_BW_50MHZ = 50000000, PICO_BW_250MHZ = 250000000,
        # PICO_BW_500MHZ = 500000000

        self.noOfPreTriggerSamples = 200
        self.noOfPostTriggerSamples = 3000
        self.nSamples = self.noOfPreTriggerSamples + self.noOfPostTriggerSamples

    def channelA_setup(self):
        """
        This is a function to set channel A on and B,C,D off.
        :return: channel = 0
        """
        # Set channel A on
        # handle = chandle
        channel = 0  # channel A
        # coupling = self.coupling
        # channelRange = self.voltrange
        # analogueOffset = 0 V
        # bandwidth = self.bandwidth
        ps.ps6000aSetChannelOn(self.chandle, channel, self.coupling, self.voltrange, 0, self.bandwidth)

        # set channel B,C,D off
        for x in range(1, 3, 1):
            channel_off = x
            ps.ps6000aSetChannelOff(self.chandle, channel_off)

        return channel

    def channel_setup(self, channel=0):
        """
        This is a function to set a channel on and the others off.
        :param channel: int: 0=A, 1=B, 2=C, 3=D, default: 0
        :return: channel: int (0, 1, 2, 3)
        """
        # Set given channel on
        # handle = chandle
        # channel = channel
        # coupling = self.coupling
        # channelRange = self.voltrange
        # analogueOffset = 0 V
        # bandwidth = self.bandwidth
        ps.ps6000aSetChannelOn(self.chandle, channel, self.coupling, self.voltrange, 0, self.bandwidth)

        # set other channels off
        if channel == 0:
            for x in [1, 2, 3]:
                channel_off = x
                ps.ps6000aSetChannelOff(self.chandle, channel_off)
        if channel == 1:
            for x in [0, 2, 3]:
                channel_off = x
                ps.ps6000aSetChannelOff(self.chandle, channel_off)
        if channel == 2:
            for x in [0, 1, 3]:
                channel_off = x
                ps.ps6000aSetChannelOff(self.chandle, channel_off)
        if channel == 3:
            for x in [0, 1, 2]:
                channel_off = x
                ps.ps6000aSetChannelOff(self.chandle, channel_off)

        return channel

    def trigger_setup(self, channel=0, direction=2, threshold=1000):
        """
        This is a function to set the trigger on the given channel. The threshold can be given in [mV].
        :param channel: int: 0=A, 1=B, 2=C, 3=D, default: 0
        :param direction: int, default: 2 (rising edge)
        PICO_ABOVE = PICO_INSIDE = 0, PICO_BELOW = PICO_OUTSIDE = 1, PICO_RISING = PICO_ENTER = PICO_NONE = 2,
        PICO_FALLING = PICO_EXIT = 3, PICO_RISING_OR_FALLING = PICO_ENTER_OR_EXIT = 4
        :param threshold: int [mV] trigger value, default value: 1000 mV
        :return: channel (int), direction (int), threshold(int) [mV]
        """
        # Set simple trigger on the given channel, [thresh] mV rising with 1 ms autotrigger
        # handle = chandle
        # enable = 1
        # source = channel
        # threshold = threshold [mV], default value: 1000 mV
        # direction = 2 (rising)
        # delay = 0 s
        autoTriggerMicroSeconds = 1000  # [us]
        ps.ps6000aSetSimpleTrigger(self.chandle, 1, channel, threshold, direction, 0, autoTriggerMicroSeconds)
        return channel, direction, threshold

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

    def buffer_setup(self, channel=0):
        """
        This function tells the driver to store the data unprocessed: raw mode (no downsampling).
        :param channel: int: 0=A, 1=B, 2=C, 3=D, default: 0
        :return:
        """
        # Set number of samples to be collected
        nSamples = self.nSamples
        # Create buffers
        bufferMax = (ctypes.c_int16 * nSamples)()
        bufferMin = (ctypes.c_int16 * nSamples)()
        # Set data buffers
        # handle = chandle
        # channel = channel
        # bufferMax = bufferAMax
        # bufferMin = bufferAMin
        # nSamples = nSamples
        dataType = enums.PICO_DATA_TYPE["PICO_INT16_T"]  # 16-bit signed integer
        waveform = 0  # segment index
        downSampleMode = enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"]  # No downsampling. Returns raw data values.
        clear = enums.PICO_ACTION["PICO_CLEAR_ALL"]
        add = enums.PICO_ACTION["PICO_ADD"]
        action = clear | add  # PICO_ACTION["PICO_CLEAR_WAVEFORM_CLEAR_ALL"] | PICO_ACTION["PICO_ADD"]
        ps.ps6000aSetDataBuffers(self.chandle, channel, ctypes.byref(bufferMax),
                                 ctypes.byref(bufferMin), nSamples, dataType, waveform,
                                 downSampleMode, action)
        return bufferMax

    def buffer_multi_setup(self, channel=0, number=10):
        """
        This function tells the driver to store the data unprocessed: raw mode (no downsampling).
        :param channel: int: 0=A, 1=B, 2=C, 3=D, default: 0
        :param number: int (number of waveforms)
        :return:
        """
        # Set number of samples to be collected
        nSamples = self.nSamples

        # Set number of memory segments
        # noOfCaptures = number
        maxSegments = ctypes.c_uint64(number)
        ps.ps6000aMemorySegments(self.chandle, number, ctypes.byref(maxSegments))

        # Set number of captures
        ps.ps6000aSetNoOfCaptures(self.chandle, number)

        # Create buffers
        buffersMax = ((ctypes.c_int16 * nSamples) * number)()
        buffersMin = ((ctypes.c_int16 * nSamples) * number)()
        for i in range(number):
            bufferMax = (ctypes.c_int16 * nSamples)()
            bufferMin = (ctypes.c_int16 * nSamples)()
            buffersMax[i] = bufferMax
            buffersMin[i] = bufferMin

        # Set data buffers
        # handle = chandle
        # channel = channel
        # bufferMax = bufferMax
        # bufferMin = bufferMin
        # nSamples = nSamples
        dataType = enums.PICO_DATA_TYPE["PICO_INT16_T"]
        downSampleMode = enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"]
        clear = enums.PICO_ACTION["PICO_CLEAR_ALL"]
        add = enums.PICO_ACTION["PICO_ADD"]
        action = clear | add  # PICO_ACTION["PICO_CLEAR_WAVEFORM_CLEAR_ALL"] | PICO_ACTION["PICO_ADD"]

        for i, j, k in zip(range(0, number), buffersMax, buffersMin):
            waveform = i
            if i == 0:
                ps.ps6000aSetDataBuffers(self.chandle, channel, ctypes.byref(j), ctypes.byref(k), nSamples, dataType,
                                         waveform, downSampleMode, action)
            if i > 0:
                ps.ps6000aSetDataBuffers(self.chandle, channel, ctypes.byref(j), ctypes.byref(k), nSamples, dataType,
                                         waveform, downSampleMode, add)

        return buffersMax, buffersMin

    def single_measurement(self, channel=0, trgchannel=0, direction=2, threshold=1000, bufchannel=0):
        """
        This is a function to run a single waveform measurement.
        First, it runs channel_setup(channel) to set a channel on and the others off.
        Then, it runs trigger_setup(trgchannel, direction, threshold) which sets the trigger to a rising edge at the
        given value [mV].
        Then, it runs timebase_setup() to get the fastest available timebase.
        Then, it runs buffer_setup(bufchannel) to setup the buffer to
        store the data unprocessed.
        Then a single waveform measurement is taken und written into a file in the folder data.
        :param channel: int: 0=A, 1=B, 2=C, 3=D, default: 0
        :param trgchannel: int: 0=A, 1=B, 2=C, 3=D, default: 0
        :param direction: int, default: 2 (rising edge)
        PICO_ABOVE = PICO_INSIDE = 0, PICO_BELOW = PICO_OUTSIDE = 1, PICO_RISING = PICO_ENTER = PICO_NONE = 2,
        PICO_FALLING = PICO_EXIT = 3, PICO_RISING_OR_FALLING = PICO_ENTER_OR_EXIT = 4
        :param threshold: int [mV] trigger value, default value: 1000 mV
        :param bufchannel: int: 0=A, 1=B, 2=C, 3=D, default: 0
        :return: filename (str)
        """
        self.channel_setup(channel)
        self.trigger_setup(trgchannel, direction, threshold)
        timebase, timeInterval = self.timebase_setup()
        bufferMax = self.buffer_setup(bufchannel)
        nSamples = self.nSamples

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
        noOfSamples = ctypes.c_uint64(nSamples)
        # downSampleRatio = 1
        downSampleMode = enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"]  # # No downsampling. Returns raw data values.
        # segmentIndex = 0
        overflow = ctypes.c_int16(0)
        ps.ps6000aGetValues(self.chandle, 0, ctypes.byref(noOfSamples), 1, downSampleMode, 0,
                            ctypes.byref(overflow))

        # get max ADC value
        # handle = chandle
        minADC = ctypes.c_int16()
        maxADC = ctypes.c_int16()
        ps.ps6000aGetAdcLimits(self.chandle, self.resolution, ctypes.byref(minADC), ctypes.byref(maxADC))
        # convert ADC counts data to mV
        adc2mVChMax = adc2mV(bufferMax, self.voltrange, maxADC)

        # Create time data
        timevals = np.linspace(0, nSamples * timeInterval * 1000000000, nSamples)

        # create array of data and save as npy file
        data = np.zeros((nSamples, 2))
        for i, values in enumerate(adc2mVChMax):
            timeval = timevals[i]
            mV = values
            data[i] = [timeval, mV]
        filename = './data/'
        timestr = time.strftime("%Y%m%d-%H%M%S")
        filename += timestr + '-1.npy'
        np.save(filename, data)

        return filename

    def block_measurement(self, channel=0, trgchannel=0, direction=2, threshold=1000, bufchannel=0, number=10):
        """
        This is a function to run a block measurement. Several waveforms are stored. The number is indicated with the
        parameter number.
        First, it runs channel_setup(channel) to set a channel on and the others off.
        Then, it runs trigger_setup(trgchannel, direction, threshold) which sets the trigger to a rising edge at the
        given value [mV].
        Then, it runs timebase_setup() to get the fastest available timebase.
        Then, it runs buffer_multi_setup(bufchannel, number) to setup the buffer
        to store the data unprocessed.
        Then a multi waveform measurement is taken und written into a file (.npy) in the folder data.
        :param channel: int: 0=A, 1=B, 2=C, 3=D, default: 0
        :param trgchannel: int: 0=A, 1=B, 2=C, 3=D, default: 0
        :param direction: int, default: 2 (rising edge)
        PICO_ABOVE = PICO_INSIDE = 0, PICO_BELOW = PICO_OUTSIDE = 1, PICO_RISING = PICO_ENTER = PICO_NONE = 2,
        PICO_FALLING = PICO_EXIT = 3, PICO_RISING_OR_FALLING = PICO_ENTER_OR_EXIT = 4
        :param threshold: int [mV] trigger value, default value: 1000 mV
        :param bufchannel: int: 0=A, 1=B, 2=C, 3=D, default: 0
        :param number: int (number of waveforms)
        :return: filename
        """
        self.channel_setup(channel)
        self.trigger_setup(trgchannel, direction, threshold)
        timebase, timeInterval = self.timebase_setup()
        buffersMax, buffersMin = self.buffer_multi_setup(bufchannel, number)
        print('Picoscope set')
        nSamples = self.nSamples

        # Set number of memory segments
        # noOfCaptures = number
        maxSegments = ctypes.c_uint64(nSamples)
        ps.ps6000aMemorySegments(self.chandle, number, ctypes.byref(maxSegments))
        print('Memory segments set')

        # Set number of captures
        ps.ps6000aSetNoOfCaptures(self.chandle, number)
        print('Number of captures set')

        # Run block capture
        # handle = chandle
        # timebase = timebase
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
        print('Picoscope ready')

        # Get data from scope
        # handle = chandle
        # startIndex = 0
        noOfSamples = ctypes.c_uint64(nSamples)
        # downSampleRatio = 1
        # segmentIndex = 0
        end = number-1
        downSampleMode = enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"]
        # Creates an overflow location for each segment
        overflow = (ctypes.c_int16 * nSamples)()
        ps.ps6000aGetValuesBulk(self.chandle, 0, ctypes.byref(noOfSamples), 0, end, 1, downSampleMode,
                                                      ctypes.byref(overflow))
        print('got values')

        # get max ADC value
        # handle = chandle
        minADC = ctypes.c_int16()
        maxADC = ctypes.c_int16()
        ps.ps6000aGetAdcLimits(self.chandle, self.resolution, ctypes.byref(minADC), ctypes.byref(maxADC))
        print('adc limits')
        self.stop_scope()

        # convert ADC counts data to mV
        adc2mVChMax_list = np.zeros((number, nSamples))

        for i, buffers in enumerate(buffersMax):
            adc2mVChMax = adc2mV(buffers, self.voltrange, maxADC)
            adc2mVChMax_list[i] = adc2mVChMax

        # Create time data
        timevals = np.linspace(0, nSamples * timeInterval * 1000000000, nSamples)

        # create array of data and save as npy file
        data = np.zeros((number, nSamples, 2))
        print('data array with zeros')
        # for i, values in enumerate(adc2mVChMax_list):  # i = number of waveforms
        #     for j, samples in enumerate(values):  # j = nSamples
        #         timeval = timevals[j]
        #         mV = samples
        #         data[i][j] = [timeval, mV]
        data[:,:,0] = timevals
        data[:,:,1] = adc2mVChMax_list

        filename = './data/'
        timestr = time.strftime("%Y%m%d-%H%M%S")
        filename += timestr + '-' + str(number) + '.npy'
        print(filename)
        np.save(filename, data)
        print('file has been saved')

        return filename, data

    def plot_data(self, filename):
        """
        This is a plotting function.
        It opens a file from the data folder and plots the waveform (voltage [mV ]over time [ns])
        :param filename: str (e.g. './data/20210622-171439-10.npy') or can be given by filename = P.single_measurement()
               or filename = P.block_measurement()
        :return: plot
        """
        data = np.load(filename)  # './data/20210622-171439-10.npy'
        filename_split1 = filename.split('/')  # ['.', 'data', '20210622-171439-10.npy']
        filename_split1b = filename_split1[-1].split('.')  # ['20210622-171439-10', 'npy']
        figname = filename_split1b[0]
        filename_split2 = filename.split('-')  # ['./data/20210622', '171439', '10.npy']
        filename_split2b = filename_split2[-1].split('.')  # ['10', 'npy']
        number = int(filename_split2b[0])  # 10

        if number == 1:
            for k in data:
                plt.plot(k[0], k[1], '.', color='cornflowerblue')
            plt.xlabel('Time (ns)')
            plt.ylabel('Voltage (mV)')
            plt.show()

        elif number > 1:
            cmap = plt.cm.viridis
            colors = iter(cmap(np.linspace(0, 0.7, number)))
            for i, c in zip(data, colors):
                for k in i:
                    plt.plot(k[0], k[1], '.', color=c)
            plt.xlabel('Time (ns)')
            plt.ylabel('Voltage (mV)')
            plt.show()

        figureName = './data/plots/Figure_' + figname + '.pdf'
        plt.savefig(figureName)

    def plot_histogram(self, filename, nBins=20):
        """
        This is a function to plot a histogram of the area under the curve for multiple waveforms.
        :param filename: str (e.g. './data/20210622-171439-10.npy') or can be given by filename = P.single_measurement()
               or filename = P.block_measurement()
        :param nBins: int: number of bins, default: 20
        :return: plot
        """

        data = np.load(filename)  # './data/20210622-171439-10.npy'
        filename_split1 = filename.split('/')  # ['.', 'data', '20210622-171439-10.npy']
        filename_split1b = filename_split1[-1].split('.')  # ['20210622-171439-10', 'npy']
        figname = filename_split1b[0]
        filename_split2 = filename.split('-')  # ['./data/20210622', '171439', '10.npy']
        filename_split2b = filename_split2[-1].split('.')  # ['10', 'npy']
        number = int(filename_split2b[0])  # 10

        x = []
        y = []
        for i in data:
            for j in i:
                x.append(j[0])
                y.append(j[1])

        nSamples = self.nSamples
        x_array = np.reshape(x, (number, nSamples))
        y_array = np.reshape(y, (number, nSamples))

        area_array = trapz(y_array, x_array, axis=1)

        # nBins = self.nBins
        plt.hist(area_array, bins=nBins)
        plt.ylabel('counts')
        plt.xlabel('area [Vs]')
        plt.show()

        figureName = './data/plots/Histogram_' + figname + '.pdf'
        plt.savefig(figureName)

    def stop_scope(self):
        """
        This is a function to stop whatever the picoscope is doing.
        """
        ps.ps6000aStop(self.chandle)
        print('Picoscope stopped')

    def close_scope(self):
        """
        This is a function to stop whatever the picoscope is doing and close the connection to it.
        """
        ps.ps6000aStop(self.chandle)
        print('Picoscope stopped')
        ps.ps6000aCloseUnit(self.chandle)
        print('Picoscope closed')

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
        ps.ps6000aGetMinimumTimebaseStateless(self.chandle, enabledChannelFlags, ctypes.byref(timebase),
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
        timevals = np.linspace(0, nSamples * timeInterval.value * 1000000000, nSamples)

        # create array of data and save as txt file
        data = np.zeros((nSamples, 2))
        for i, values in enumerate(adc2mVChAMax):
            timeval = timevals[i]
            mV = values
            data[i] = [timeval, mV]
        np.savetxt('./data/waveform.txt', data, delimiter=' ', newline='\n', header='time data [mV]')

        # plot data from channel A and B
        plt.plot(timevals, adc2mVChAMax[:])
        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')
        plt.show()

    def block_measurement_with_setup(self):
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

        # --> Set number of memory segments
        noOfCaptures = 10
        maxSegments = ctypes.c_uint64(10)
        status["memorySegments"] = ps.ps6000aMemorySegments(self.chandle, noOfCaptures, ctypes.byref(maxSegments))
        assert_pico_ok(status["memorySegments"])

        # --> Set number of captures
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
        timevals = np.linspace(0, nSamples * timeInterval.value * 1000000000, nSamples)

        # plot data from channel A and B
        plt.plot(timevals, adc2mVChAMax[:])
        plt.plot(timevals, adc2mVChAMax1[:])
        plt.plot(timevals, adc2mVChAMax2[:])
        plt.plot(timevals, adc2mVChAMax3[:])
        plt.plot(timevals, adc2mVChAMax4[:])
        plt.plot(timevals, adc2mVChAMax5[:])
        plt.plot(timevals, adc2mVChAMax6[:])
        plt.plot(timevals, adc2mVChAMax7[:])
        plt.plot(timevals, adc2mVChAMax8[:])
        plt.plot(timevals, adc2mVChAMax9[:])
        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')
        plt.show()


if __name__ == "__main__":
    P = Picoscope()
    #data1 = P.single_measurement()
    #P.plot_data(data1)
    file, data2 = P.block_measurement(number=100)
    P.plot_histogram(data2)
    P.close_scope()
