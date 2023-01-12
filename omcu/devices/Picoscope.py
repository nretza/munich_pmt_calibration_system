#!/usr/bin/python3
import ctypes
import numpy as np
from numpy import trapz
from devices.device import device
from picosdk.ps6000a import ps6000a as ps
from picosdk.PicoDeviceEnums import picoEnum as enums
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV
import time

from utils.data_structs import Measurement


class Picoscope(device):

    """
    This is a class for the PicoTech Picoscope 6424E
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
        ps.ps6000aOpenUnit(ctypes.byref(self.chandle), None, self.resolution)  # opens connection

        # CHANNEL SETUP
        self.coupling_sgnl = enums.PICO_COUPLING["PICO_DC_50OHM"]
        self.coupling_trg = enums.PICO_COUPLING["PICO_DC"]
        self.voltrange_sgnl = 3
        self.voltrange_trg = 9

        # voltage range for signal channel needs to be sufficiently low to avoid large noise band

        self.timebase = 2  # 0 and 1 didn't work
        if self.timebase < 5:
            self.timeInterval = (2 ** self.timebase) / 5000000000  # [s]
        else:
            self.timeInterval = (self.timebase - 4) / 156250000

        self.bandwidth = enums.PICO_BANDWIDTH_LIMITER["PICO_BW_FULL"]

        self.noOfPreTriggerSamples = 100
        self.noOfPostTriggerSamples = 250
        self.nSamples = self.noOfPreTriggerSamples + self.noOfPostTriggerSamples

    def get_nSamples(self):
        return self.nSamples

    def channel_setup(self, trgchannel=0, sgnlchannel=2):
        """
        This is a function to set a trigger channel and a signal channel on and the others off.
        :param trgchannel: int: 0=A, 1=B, 2=C, 3=D, default: 0
        :param sgnlchannel: int: 0=A, 1=B, 2=C, 3=D, default: 2
        :return: trgchannel, sgnlchannel: int (0, 1, 2, 3)
        """

        # channel setup
        ps.ps6000aSetChannelOn(self.chandle, trgchannel, self.coupling_trg, self.voltrange_trg, 0, self.bandwidth)
        ps.ps6000aSetChannelOn(self.chandle, sgnlchannel, self.coupling_sgnl, self.voltrange_sgnl, 0, self.bandwidth)

        for ch in [0, 1, 2, 3]:
            if trgchannel == ch or sgnlchannel == ch:
                pass
            else:
                ps.ps6000aSetChannelOff(self.chandle, ch)

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
        enabledChannelFlags = enums.PICO_CHANNEL_FLAGS["PICO_CHANNEL_A_FLAGS"]
        timebase = ctypes.c_uint32(0)
        timeInterval = ctypes.c_double(0)
        ps.ps6000aGetMinimumTimebaseStateless(self.chandle, enabledChannelFlags, ctypes.byref(timebase),
                                              ctypes.byref(timeInterval), self.resolution)

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

        # channel setup
        self.channel_setup(trgchannel, sgnlchannel)

        # Set number of memory segments
        maxSegments = ctypes.c_uint64(number)
        ps.ps6000aMemorySegments(self.chandle, number, ctypes.byref(maxSegments))

        # Set number of captures
        ps.ps6000aSetNoOfCaptures(self.chandle, number)

        timebase, timeInterval = self.timebase_setup()

        self.trigger_setup(trgchannel, direction, threshold)

        buffersMax_trgch, buffersMin_trgch, buffersMax_sgnlch, buffersMin_sgnlch =\
            self.buffer_setup_block_multi(trgchannel=trgchannel, sgnlchannel=sgnlchannel, number=number)

        nSamples = self.nSamples
        timeIndisposedMs = ctypes.c_double(0)

        ps.ps6000aRunBlock(self.chandle, self.noOfPreTriggerSamples, self.noOfPostTriggerSamples, timebase,
                           ctypes.byref(timeIndisposedMs), 0, None, None)

        # Check for data collection to finish using ps6000aIsReady
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            ps.ps6000aIsReady(self.chandle, ctypes.byref(ready))

        # Get data from scope
        noOfSamples = ctypes.c_uint64(nSamples)
        end = number-1
        downSampleMode = enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"]

        # Creates an overflow location for each segment
        overflow = (ctypes.c_int16 * number)()

        ps.ps6000aGetValuesBulk(self.chandle, 0, ctypes.byref(noOfSamples), 0, end, 1, downSampleMode,
                                                  ctypes.byref(overflow))

        # get max ADC value
        minADC = ctypes.c_int16()
        maxADC = ctypes.c_int16()

        ps.ps6000aGetAdcLimits(self.chandle, self.resolution, ctypes.byref(minADC), ctypes.byref(maxADC))

        self.stop_scope()

        # convert ADC counts data to mV
        adc2mVMax_trgch_list = np.zeros((number, nSamples))
        for i, buffers in enumerate(buffersMax_trgch):
            adc2mVMax_trgch_list[i] = adc2mV(buffers, self.voltrange_trg, maxADC)

        adc2mVMax_sgnlch_list = np.zeros((number, nSamples))
        for i, buffers in enumerate(buffersMax_sgnlch):
            adc2mVMax_sgnlch_list[i] = adc2mV(buffers, self.voltrange_sgnl, maxADC)

        # Create time data
        timevals = np.tile(np.linspace(0, nSamples * timeInterval * 1000000000, nSamples), (number,1))

        self.logger.debug(f"block measurement of {number} Waveforms performed. trigger_ch: {trgchannel}, signal_ch: {sgnlchannel}")
        dataset = Measurement(time_data=timevals, signal_data=adc2mVMax_sgnlch_list, trigger_data=adc2mVMax_trgch_list)

        return dataset

        # TODO this produces weird data

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
        self.logger.debug("picoscope stopped")

    def close_scope(self):
        """
        This is a function to stop whatever the picoscope is doing and close the connection to it.
        """
        ps.ps6000aStop(self.chandle)
        ps.ps6000aCloseUnit(self.chandle)

        self.logger.debug("picoscope stopped and connection closed")


if __name__ == "__main__":
    ps = Picoscope()
    ps.block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=2000, number=100)
    ps.close_scope()
