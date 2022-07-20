#!/usr/bin/python3
import ctypes
import numpy as np
from numpy import trapz
from omcu.devices.device import device
from picosdk.ps6000a import ps6000a as ps
from picosdk.PicoDeviceEnums import picoEnum as enums
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV
import time


class Picoscope(device):
    """
    This is a class for the PicoTech Picoscope 6424E
    
    This is a Singleton - google it!
    """

    _instance = None

    @classmethod
    def Instance(cls):
        if not cls._instance:
            cls._instance = Picoscope()
        return cls._instance

    def __init__(self):

        if Picoscope._instance:
            raise Exception(f"ERROR: {str(type(self))} has already been initialized. please call with {str(type(self).__name__)}.Instance()")
        else:
            Picoscope._instance = self

        super().__init__()

        self.chandle = ctypes.c_int16()
        self.resolution = enums.PICO_DEVICE_RESOLUTION["PICO_DR_12BIT"]
        # PICO_DR_8BIT = 0, PICO_DR_10BIT = 10, PICO_DR_12BIT = 1
        ps.ps6000aOpenUnit(ctypes.byref(self.chandle), None, self.resolution)  # opens connection

        # CHANNEL SETUP
        self.coupling_sgnl = enums.PICO_COUPLING["PICO_DC_50OHM"]
        self.coupling_trg = enums.PICO_COUPLING["PICO_DC"]
        # PICO_AC = 0, PICO_DC = 1, PICO_DC_50OHM = 50
        self.voltrange_sgnl = 3
        self.voltrange_trg = 9
        # voltage range for signal channel needs to be sufficiently low to avoid large noise band
        # 0=PICO_10MV: ±10 mV, 1=PICO_20MV: ±20 mV, 2=PICO_50MV: ±50 mV, 3=PICO_100MV: ±100 mV, 4=PICO_200MV: ±200 mV,
        # 5=PICO_500MV: ±500 mV, 6=PICO_1V: ±1 V, 7=PICO_2V: ±2 V, 8=PICO_5V: ±5 V, 9=PICO_10V: ±10 V,
        # 10=PICO_20V: ±20 V (9 and 10 not for DC_50OHM)

        self.timebase = 2  # 0 and 1 didn't work
        if self.timebase < 5:
            self.timeInterval = (2 ** self.timebase) / 5000000000  # [s]
        else:
            self.timeInterval = (self.timebase - 4) / 156250000

        self.bandwidth = enums.PICO_BANDWIDTH_LIMITER["PICO_BW_FULL"]
        # PICO_BW_FULL = 0, PICO_BW_100KHZ = 100000, PICO_BW_20KHZ = 20000, PICO_BW_1MHZ = 1000000,
        # PICO_BW_20MHZ = 20000000, PICO_BW_25MHZ = 25000000, PICO_BW_50MHZ = 50000000, PICO_BW_250MHZ = 250000000,
        # PICO_BW_500MHZ = 500000000

        self.noOfPreTriggerSamples = 100
        self.noOfPostTriggerSamples = 250
        self.nSamples = self.noOfPreTriggerSamples + self.noOfPostTriggerSamples

    def get_nSamples(self):
        nSamples = self.nSamples
        return nSamples

    def channel_setup(self, trgchannel=0, sgnlchannel=2):
        """
        This is a function to set a trigger channel and a signal channel on and the others off.
        :param trgchannel: int: 0=A, 1=B, 2=C, 3=D, default: 0
        :param sgnlchannel: int: 0=A, 1=B, 2=C, 3=D, default: 2
        :return: trgchannel, sgnlchannel: int (0, 1, 2, 3)
        """
        # channel setup

        # handle = chandle
        # channel = channel
        # coupling = self.coupling_trg/sgnl
        # channelRange = self.voltrange_trg/sgnl
        # analogueOffset = 0 V
        # bandwidth = self.bandwidth

        ps.ps6000aSetChannelOn(self.chandle, trgchannel, self.coupling_trg, self.voltrange_trg, 0, self.bandwidth)
        #print("Trigger channel on:", trgchannel)
        ps.ps6000aSetChannelOn(self.chandle, sgnlchannel, self.coupling_sgnl, self.voltrange_sgnl, 0, self.bandwidth)
        #print("Signal channel on:", sgnlchannel)

        for ch in [0, 1, 2, 3]:
            if trgchannel == ch or sgnlchannel == ch:
                pass
            else:
                ps.ps6000aSetChannelOff(self.chandle, ch)
                #print("Channel off:", ch)

        self.logger.debug(f"Setting up channels. trig_ch: {trgchannel}, signal_ch: {sgnlchannel}") 
        return trgchannel, sgnlchannel

    def channel_setup_all(self):
        """
        This function turns all channels on.
        :return:
        """
        for ch in [0, 1, 2, 3]:
            ps.ps6000aSetChannelOn(self.chandle, ch, self.coupling_sgnl, self.voltrange_sgnl, 0, self.bandwidth)

        self.logger.debug(f"turning all channels on")

    def trigger_setup(self, trgchannel=0, direction=2, threshold=1000):
        """
        This is a function to set the trigger on the given channel. The threshold can be given in [mV].
        :param trgchannel: int: 0=A, 1=B, 2=C, 3=D, default: 0
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
        autoTriggerMicroSeconds = 1000000  # [us]
        ps.ps6000aSetSimpleTrigger(self.chandle, 1, trgchannel, threshold, direction, 0, autoTriggerMicroSeconds)

        self.logger.debug(f"setting trigger threshold {threshold} mV on channel {trgchannel}") 

        return trgchannel, direction, threshold

    def timebase_setup(self):
        """
        This is a function to get the fastest available timebase.
        The timebases allow slow enough sampling in block mode to overlap the streaming sample intervals.
        :return: timebase: int
        """
        # Get fastest available timebase
        # handle = chandle
        enabledChannelFlags = enums.PICO_CHANNEL_FLAGS["PICO_CHANNEL_A_FLAGS"]
        # PICO_CHANNEL_A_FLAGS = 1, PICO_CHANNEL_B_FLAGS = 2, PICO_CHANNEL_C_FLAGS = 4, PICO_CHANNEL_D_FLAGS = 8
        timebase = ctypes.c_uint32(0)
        timeInterval = ctypes.c_double(0)
        # resolution = resolution
        ps.ps6000aGetMinimumTimebaseStateless(self.chandle, enabledChannelFlags, ctypes.byref(timebase),
                                              ctypes.byref(timeInterval), self.resolution)
        #print("timebase = ", timebase.value)
        #print("sample interval =", timeInterval.value, "s")

        self.logger.debug("Setup to get the fastest available timebase.")

        return timebase.value, timeInterval.value

    def buffer_setup(self, channel=0):
        """
        This function tells the driver to store the data unprocessed: raw mode (no downsampling).
        One channel, one waveform.
        :param channel: int: 0=A, 1=B, 2=C, 3=D, default: 0
        :return: bufferMax, format: bufferMax = (ctypes.c_int16 * nSamples)()
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

        self.logger.debug(f"Will store data without downsampling. One channel, one waveform.")
        return bufferMax

    def buffer_setup_block(self, channel=0, number=10):
        """
        This function tells the driver to store the data unprocessed: raw mode (no downsampling).
        One channel, several waveforms - indicated by number.
        :param channel: int: 0=A, 1=B, 2=C, 3=D, default: 0
        :param number: int (number of waveforms)
        :return: buffersMax, buffersMin
                format: ((ctypes.c_int16 * nSamples) * number)()
        """
        # Set number of samples to be collected
        nSamples = self.nSamples

        # Create buffers
        buffersMax = ((ctypes.c_int16 * nSamples) * number)()
        buffersMin = ((ctypes.c_int16 * nSamples) * number)()

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
        action = clear|add  # PICO_ACTION["PICO_CLEAR_WAVEFORM_CLEAR_ALL"] | PICO_ACTION["PICO_ADD"]

        for i in range(0, number):
            waveform = i
            if i == 0:
                ps.ps6000aSetDataBuffers(self.chandle, channel, ctypes.byref(buffersMax[i]), ctypes.byref(buffersMin[i]),
                                         nSamples, dataType, waveform, downSampleMode, action)
            if i > 0:
                ps.ps6000aSetDataBuffers(self.chandle, channel, ctypes.byref(buffersMax[i]), ctypes.byref(buffersMin[i]),
                                         nSamples, dataType, waveform, downSampleMode, add)

        self.logger.debug(f"will store data without downsampling. One channel, several waveforms.")

        return buffersMax, buffersMin

    def buffer_setup_block_multi(self, trgchannel=0, sgnlchannel=2, number=10):
        """
        This function tells the driver to store the data unprocessed: raw mode (no downsampling).
        One trigger channel and one signal channel, several waveforms - indicated by number
        :param trgchannel: int: 0=A, 1=B, 2=C, 3=D, default: 0
        :param sgnlchannel: int: 0=A, 1=B, 2=C, 3=D, default: 2
        :param number: int (number of waveforms)
        :return: buffersMax_trgch, buffersMin_trgch, buffersMax_sgnlch, buffersMin_sgnlch
                format: ((ctypes.c_int16 * nSamples) * number)()
        """

        # Set number of samples to be collected
        nSamples = self.nSamples

        # Create buffers
        buffersMax_trgch = ((ctypes.c_int16 * nSamples) * number)()
        buffersMin_trgch = ((ctypes.c_int16 * nSamples) * number)()
        buffersMax_sgnlch = ((ctypes.c_int16 * nSamples) * number)()
        buffersMin_sgnlch = ((ctypes.c_int16 * nSamples) * number)()

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
        action = clear|add  # PICO_ACTION["PICO_CLEAR_WAVEFORM_CLEAR_ALL"] | PICO_ACTION["PICO_ADD"]

        for i in range(0, number):
            waveform = i
            if i == 0:
                ps.ps6000aSetDataBuffers(self.chandle, trgchannel, ctypes.byref(buffersMax_trgch[i]),
                                         ctypes.byref(buffersMin_trgch[i]), nSamples, dataType, waveform,
                                         downSampleMode, action)
                ps.ps6000aSetDataBuffers(self.chandle, sgnlchannel, ctypes.byref(buffersMax_sgnlch[i]),
                                         ctypes.byref(buffersMin_sgnlch[i]), nSamples, dataType, waveform,
                                         downSampleMode, add)
            if i > 0:
                ps.ps6000aSetDataBuffers(self.chandle, trgchannel, ctypes.byref(buffersMax_trgch[i]),
                                         ctypes.byref(buffersMin_trgch[i]), nSamples, dataType, waveform,
                                         downSampleMode, add)
                ps.ps6000aSetDataBuffers(self.chandle, sgnlchannel, ctypes.byref(buffersMax_sgnlch[i]),
                                         ctypes.byref(buffersMin_sgnlch[i]), nSamples, dataType, waveform,
                                         downSampleMode, add)

        self.logger.debug(f"will store data without downsampling. One trigger channel and one signal channel, several waveforms - indicated by number")

        return buffersMax_trgch, buffersMin_trgch, buffersMax_sgnlch, buffersMin_sgnlch

    def block_measurement(self, trgchannel=0, sgnlchannel=2, direction=2, threshold=1000, number=10):
        """
        This is a function to run a block measurement. Several waveforms are stored. The number is indicated with the
        parameter number.
        First, it runs channel_setup(channel) to set a channel on and the others off.
        Then, it runs trigger_setup(trgchannel, direction, threshold) which sets the trigger to a rising edge at the
        given value [mV].
        Then, it runs timebase_setup() to get the fastest available timebase.
        Then, it runs buffer_multi_setup(bufchannel, number) to setup the buffer
        to store the data unprocessed.
        :param trgchannel: int: 0=A, 1=B, 2=C, 3=D, default: 0
        :param sgnlchannel: int: 0=A, 1=B, 2=C, 3=D, default: 2
        :param direction: int, default: 2 (rising)
        PICO_ABOVE = PICO_INSIDE = 0, PICO_BELOW = PICO_OUTSIDE = 1, PICO_RISING = PICO_ENTER = PICO_NONE = 2,
        PICO_FALLING = PICO_EXIT = 3, PICO_RISING_OR_FALLING = PICO_ENTER_OR_EXIT = 4
        :param threshold: int [mV] trigger value, default value: 1000 mV
        :param number: int (number of waveforms)
        :return: data_sgnl, data_trg
        """

        self.channel_setup(trgchannel, sgnlchannel)
        # self.channel_setup_all()

        # Set number of memory segments
        maxSegments = ctypes.c_uint64(number)
        ps.ps6000aMemorySegments(self.chandle, number, ctypes.byref(maxSegments))

        # Set number of captures
        ps.ps6000aSetNoOfCaptures(self.chandle, number)

        timebase, timeInterval = self.timebase_setup()
        # timebase = self.timebase
        # timeInterval = self.timeInterval
        #print(timebase, timeInterval)

        self.trigger_setup(trgchannel, direction, threshold)
        #print('Picoscope set')

        buffersMax_trgch, buffersMin_trgch, buffersMax_sgnlch, buffersMin_sgnlch =\
            self.buffer_setup_block_multi(trgchannel=trgchannel, sgnlchannel=sgnlchannel, number=number)

        nSamples = self.nSamples

        # Run block capture
        # handle = chandle
        # timebase = timebase
        timeIndisposedMs = ctypes.c_double(0)
        # segmentIndex = 0
        # lpReady = None   Using IsReady rather than a callback
        # pParameter = None

        t1 = time.time()
        ps.ps6000aRunBlock(self.chandle, self.noOfPreTriggerSamples, self.noOfPostTriggerSamples, timebase,
                           ctypes.byref(timeIndisposedMs), 0, None, None)
        t2 = time.time()
        deltaT = t2-t1
        #print(deltaT)

        # Check for data collection to finish using ps6000aIsReady
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            ps.ps6000aIsReady(self.chandle, ctypes.byref(ready))
        #print('Picoscope ready')

        # Get data from scope
        # handle = chandle
        # startIndex = 0
        noOfSamples = ctypes.c_uint64(nSamples)
        # segmentIndex = 0
        end = number-1
        # downSampleRatio = 1
        downSampleMode = enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"]
        # Creates an overflow location for each segment
        overflow = (ctypes.c_int16 * number)()

        ps.ps6000aGetValuesBulk(self.chandle, 0, ctypes.byref(noOfSamples), 0, end, 1, downSampleMode,
                                                  ctypes.byref(overflow))
        #print('got values')

        # get max ADC value
        # handle = chandle
        minADC = ctypes.c_int16()
        maxADC = ctypes.c_int16()
        ps.ps6000aGetAdcLimits(self.chandle, self.resolution, ctypes.byref(minADC), ctypes.byref(maxADC))
        #print('adc limits')

        self.stop_scope()

        # convert ADC counts data to mV
        adc2mVMax_trgch_list = np.zeros((number, nSamples))
        for i, buffers in enumerate(buffersMax_trgch):
            adc2mVMax_trgch_list[i] = adc2mV(buffers, self.voltrange_trg, maxADC)

        adc2mVMax_sgnlch_list = np.zeros((number, nSamples))
        for i, buffers in enumerate(buffersMax_sgnlch):
            adc2mVMax_sgnlch_list[i] = adc2mV(buffers, self.voltrange_sgnl, maxADC)

        # Create time data
        timevals = np.linspace(0, nSamples * timeInterval * 1000000000, nSamples)

        # create array of data and save as npy file
        data_sgnl = np.zeros((number, nSamples, 2))
        data_sgnl[:, :, 0] = timevals
        data_sgnl[:, :, 1] = adc2mVMax_sgnlch_list

        data_trg = np.zeros((number, nSamples, 2))
        data_trg[:, :, 0] = timevals
        data_trg[:, :, 1] = adc2mVMax_trgch_list

        # timestr = time.strftime("%Y%m%d-%H%M%S")
        # directory = 'data/' + timestr
        # os.mkdir(directory)
        # filename_sgnl = './data/' + timestr + '/' + timestr + '-' + str(number) + '-sgnl.npy'
        # np.save(filename_sgnl, data_sgnl)
        # filename_trg = './data/' + timestr + '/' + timestr + '-' + str(number) + '-trg.npy'
        # np.save(filename_trg, data_trg)
        # print('files have been saved under', filename_sgnl, 'and', filename_trg)

        self.logger.info(f"block measurement of {number} Waveforms performed. trigger_ch: {trgchannel}, signal_ch: {sgnlchannel}")
        return data_sgnl, data_trg  # filename_sgnl, filename_trg

    def block_measurement_one_ch(self, channel=2, number=10):
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
        :param channel: int: 0=A, 1=B, 2=C, 3=D, default: 2
        :param direction: int, default: 2 (rising)
        PICO_ABOVE = PICO_INSIDE = 0, PICO_BELOW = PICO_OUTSIDE = 1, PICO_RISING = PICO_ENTER = PICO_NONE = 2,
        PICO_FALLING = PICO_EXIT = 3, PICO_RISING_OR_FALLING = PICO_ENTER_OR_EXIT = 4
        :param threshold: int [mV] trigger value, default value: 0 mV
        :param number: int (number of waveforms)
        :return: filename
        """

        self.channel_setup(channel)
        # self.channel_setup_all()

        # Set number of memory segments
        maxSegments = ctypes.c_uint64(number)
        ps.ps6000aMemorySegments(self.chandle, number, ctypes.byref(maxSegments))

        # Set number of captures
        ps.ps6000aSetNoOfCaptures(self.chandle, number)

        timebase, timeInterval = self.timebase_setup()
        # timebase = self.timebase
        # timeInterval = self.timeInterval
        #print(timebase, timeInterval)


        buffersMax, buffersMin = self.buffer_setup_block(channel=channel, number=number)

        nSamples = self.nSamples

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
        #print('Picoscope ready')

        # Get data from scope
        # handle = chandle
        # startIndex = 0
        noOfSamples = ctypes.c_uint64(nSamples)
        # segmentIndex = 0
        end = number-1
        # downSampleRatio = 1
        downSampleMode = enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"]
        # Creates an overflow location for each segment
        overflow = (ctypes.c_int16 * number)()

        ps.ps6000aGetValuesBulk(self.chandle, 0, ctypes.byref(noOfSamples), 0, end, 1, downSampleMode,
                                                  ctypes.byref(overflow))
        #print('got values')

        # get max ADC value
        # handle = chandle
        minADC = ctypes.c_int16()
        maxADC = ctypes.c_int16()
        ps.ps6000aGetAdcLimits(self.chandle, self.resolution, ctypes.byref(minADC), ctypes.byref(maxADC))
        #print('adc limits')

        self.stop_scope()

        # convert ADC counts data to mV
        adc2mVMax_list = np.zeros((number, nSamples))
        for i, buffers in enumerate(buffersMax):
            adc2mVMax_list[i] = adc2mV(buffers, self.voltrange_sgnl, maxADC)

        # Create time data
        timevals = np.linspace(0, nSamples * timeInterval * 1000000000, nSamples)

        # create array of data and save as npy file
        data = np.zeros((number, nSamples, 2))
        data[:, :, 0] = timevals
        data[:, :, 1] = adc2mVMax_list

        # timestr = time.strftime("%Y%m%d-%H%M%S")
        # directory = 'data/' + timestr
        # os.mkdir(directory)
        # filename_sgnl = './data/' + timestr + '/' + timestr + '-' + str(number) + '-sgnl.npy'
        # np.save(filename_sgnl, data_sgnl)
        # filename_trg = './data/' + timestr + '/' + timestr + '-' + str(number) + '-trg.npy'
        # np.save(filename_trg, data_trg)
        # print('files have been saved under', filename_sgnl, 'and', filename_trg)

        self.logger.info(f"Single channel block measurement of {number} Waveforms performed. ch: {channel}")

        return data

    def adc2v(self, data, vrange=7):
        """
        This function converts adc data to values in V
        :param data:
        :param vrange:
        :return:
        """
        maxADC = ctypes.c_int32(32512)
        vranges = {2:0.05,3:0.1,4:0.2,5:0.5,6:1,7:2,8:5}
        data = np.array(data)
        data = data*(vranges[vrange] / maxADC.value)
        return data

    def plot_data(self, filename):
        """
        This is a plotting function.
        It opens a file from the data folder and plots the waveform (voltage [mV ]over time [ns])
        :param filename: str (e.g. './data/20210622-171439-10.npy') or can be given by filename = P.single_measurement()
               or filename = P.block_measurement()
        :return: plot
        """
        data = np.load(filename)  # './data/20210823-103625-10-sgnl.npy'
        filename_split1 = filename.split('/')  # ['.', 'data', '20210823-103625-10-sgnl.npy']
        filename_split1b = filename_split1[-1].split('.')  # ['20210823-103625-10-sgnl', 'npy']
        figname = filename_split1b[0]  # '20210823-103625-10-sgnl'
        filename_split2 = figname.split('-')  # ['20210823', '103625', '10', 'sgnl']
        filename_split2b = filename_split2[:3]  # ['20210823', '103625', '10']
        number = int(filename_split2b[-1])  # 10

        plt.figure()
        cmap = plt.cm.viridis
        colors = iter(cmap(np.linspace(0, 0.7, number)))
        for i, c in zip(data, colors):
            plt.plot(i[:, 0], i[:, 1], color=c)
        plt.xlabel('Time (ns)')
        plt.ylabel('Voltage (mV)')

        figureName = './data/plots/Figure_' + figname + '.pdf'
        plt.savefig(figureName)
        plt.show()

    def plot_histogram(self, filename, nBins=20):
        """
        This is a function to plot a histogram of the area under the curve for multiple waveforms.
        :param filename: str (e.g. './data/20210622-171439-10.npy') or can be given by filename = P.single_measurement()
               or filename = P.block_measurement()
        :param nBins: int: number of bins, default: 20
        :return: plot
        """

        data = np.load(filename)  # './data/20210823-103625-10-sgnl.npy'
        filename_split1 = filename.split('/')  # ['.', 'data', '20210823-103625-10-sgnl.npy']
        filename_split1b = filename_split1[-1].split('.')  # ['20210823-103625-10-sgnl', 'npy']
        figname = filename_split1b[0]  # '20210823-103625-10-sgnl'
        filename_split2 = figname.split('-')  # ['20210823', '103625', '10', 'sgnl']
        filename_split2b = filename_split2[:3]  # ['20210823', '103625', '10']
        number = int(filename_split2b[-1])  # 10

        x = data[:, :, 0]
        y = data[:, :, 1]

        nSamples = self.nSamples
        x_array = np.reshape(x, (number, nSamples))
        y_array = np.reshape(y, (number, nSamples))

        area_array = trapz(y_array, x_array, axis=1)

        plt.figure()
        # nBins = self.nBins
        plt.hist(area_array, bins=nBins)
        plt.ylabel('counts')
        plt.xlabel('area [Vs]')

        figureName = './data/plots/Histogram_' + figname + '.pdf'
        plt.savefig(figureName)
        plt.show()

    def stop_scope(self):
        """
        This is a function to stop whatever the picoscope is doing.
        """
        ps.ps6000aStop(self.chandle)
        #print('Picoscope stopped')

        self.logger.warning("picoscope stopped")

    def close_scope(self):
        """
        This is a function to stop whatever the picoscope is doing and close the connection to it.
        """
        ps.ps6000aStop(self.chandle)
        #print('Picoscope stopped')
        ps.ps6000aCloseUnit(self.chandle)
        #print('Picoscope closed')

        self.logger.warning("picoscope stopped and connection closed")

if __name__ == "__main__":
    ps = Picoscope()
    ps.block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=2000, number=100)
    ps.close_scope()
