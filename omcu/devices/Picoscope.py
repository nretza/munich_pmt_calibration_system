#!/usr/bin/python3
import ctypes
import numpy as np

from picosdk.ps6000a import ps6000a as ps
from picosdk.PicoDeviceEnums import picoEnum as enums
from picosdk.functions import adc2mV, assert_pico_ok

from devices.device import device
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

    def __init__(self, trigger_ch = 0, signal_ch = 2, trigger_threshold = 2500, pre_trigger_samples = 100, post_trigger_samples = 250):

        if Picoscope._instance:
            raise Exception(f"ERROR: {str(type(self))} has already been initialized. please call with {str(type(self).__name__)}.Instance()")
        else:
            Picoscope._instance = self

        super().__init__()

        self.status = {}
        self.chandle = ctypes.c_int16()

        # maximum number of waveforms as to not overflow buffer (1 Gigasamples)
        self.max_nwf = int ( 1e9 / (2 * post_trigger_samples + pre_trigger_samples)) 
        
        # current wf number the picoscope is set up to
        self.current_nwf = None

        # resolution and timebase (set later)
        self.resolution = enums.PICO_DEVICE_RESOLUTION["PICO_DR_12BIT"]
        self.enabledChannelFlags = enums.PICO_CHANNEL_FLAGS["PICO_CHANNEL_A_FLAGS"] + enums.PICO_CHANNEL_FLAGS["PICO_CHANNEL_C_FLAGS"]
        self.timebase = ctypes.c_uint32(0)
        self.timeInterval = ctypes.c_double(0)

        # set channels
        self.channel_trg = trigger_ch
        self.channel_sgnl  = signal_ch

        # set range of channnel
        self.voltrange_trg = 9
        self.voltrange_sgnl = 3

        # set coupling
        self.coupling_trg = enums.PICO_COUPLING["PICO_DC"]
        self.coupling_sgnl = enums.PICO_COUPLING["PICO_DC_50OHM"]

        # set bandwidth
        self.bandwidth = enums.PICO_BANDWIDTH_LIMITER["PICO_BW_FULL"]
        
        # ADC limits / determined in channel setup
        self.minADC = ctypes.c_int16()
        self.maxADC = ctypes.c_int16()

        # set trigger
        self.trigger_threshold = trigger_threshold
        self.trigger_direction = enums.PICO_THRESHOLD_DIRECTION["PICO_RISING"]
        self.autotrigger = 1000000
        self.trigger_delay = 0

        # nr of samples
        self.noOfPreTriggerSamples = pre_trigger_samples
        self.noOfPostTriggerSamples = post_trigger_samples
        self.nSamples = self.noOfPreTriggerSamples + self.noOfPostTriggerSamples

        self.open_connection()
        self.channel_setup()
        self.set_timebase()
        self.set_trigger()

    def open_connection(self):
    
        # open connection to picoscope
        self.status["openunit"] = ps.ps6000aOpenUnit(ctypes.byref(self.chandle), None, self.resolution)  # opens connection
        assert_pico_ok(self.status["openunit"])


    def channel_setup(self):
        
        # turn signal and trigger channels on
        self.logger.info(f"Setting up channels. trig_ch: {self.channel_trg}, signal_ch: {self.channel_sgnl}")
        self.status["setTriggerCh"] = ps.ps6000aSetChannelOn(self.chandle, self.channel_trg, self.coupling_trg, self.voltrange_trg, 0, self.bandwidth)
        self.status["setSignalCh"]  = ps.ps6000aSetChannelOn(self.chandle, self.channel_sgnl, self.coupling_sgnl, self.voltrange_sgnl, 0, self.bandwidth)
        assert_pico_ok(self.status["setTriggerCh"])
        assert_pico_ok(self.status["setSignalCh"])

        # turn other channels off
        for channel in range(3):
            if channel in [self.channel_sgnl, self.channel_trg]: continue
            self.status["setChannel", channel] = ps.ps6000aSetChannelOff(self.chandle, channel)
            assert_pico_ok(self.status["setChannel", channel])
        
        # ADC limits
        self.status["getADCimits"] = ps.ps6000aGetAdcLimits(self.chandle, self.resolution, ctypes.byref(self.minADC), ctypes.byref(self.maxADC))
        assert_pico_ok(self.status["getADCimits"])


    def set_timebase(self):

        # Get fastest available timebase
        self.status["getMinimumTimebaseStateless"] = ps.ps6000aGetMinimumTimebaseStateless(self.chandle,
                                                                                           self.enabledChannelFlags,
                                                                                           ctypes.byref(self.timebase),
                                                                                           ctypes.byref(self.timeInterval),
                                                                                           self.resolution)
        assert_pico_ok(self.status["getMinimumTimebaseStateless"])
        self.logger.info("Setup to get the fastest available timebase.")


    def set_trigger(self):

        # Set simple trigger on the given channel, [thresh] mV rising with autotrigger
        self.logger.info(f"setting trigger threshold {self.trigger_threshold} mV on channel {self.channel_trg}")
        self.status["setSimpleTrigger"] = ps.ps6000aSetSimpleTrigger(self.chandle,
                                                                     1,
                                                                     self.channel_trg,
                                                                     self.trigger_threshold,
                                                                     self.trigger_direction,
                                                                     self.trigger_delay,
                                                                     self.autotrigger)
        assert_pico_ok(self.status["setSimpleTrigger"])
        self.logger.info(f"setup trigger direction {self.trigger_direction} at {self.trigger_threshold} threshold")


    def buffer_setup(self, number):

        assert number < self.max_nwf

        self.logger.info(f"will store data without downsampling. One trigger channel and one signal channel, several waveforms - indicated by number")

        # Create buffers
        self.buffer_trg  = ((ctypes.c_int16 * self.nSamples) * number)()
        self.buffer_sgnl = ((ctypes.c_int16 * self.nSamples) * number)()

        # Set data buffers
        dataType       = enums.PICO_DATA_TYPE["PICO_INT16_T"]
        downSampleMode = enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"]
        clear          = enums.PICO_ACTION["PICO_CLEAR_ALL"]
        add            = enums.PICO_ACTION["PICO_ADD"]

        action = clear | add
        for i in range(0, number):
            self.status["set_trg_buffer"] = ps.ps6000aSetDataBuffers(self.chandle,
                                                                    self.channel_trg,
                                                                    ctypes.byref(self.buffer_trg[i]),
                                                                    self.nSamples,
                                                                    dataType,
                                                                    i,
                                                                    downSampleMode,
                                                                    action)
            assert_pico_ok(self.status["set_trg_buffer"])
            self.status["set_sgnl_buffer"] = ps.ps6000aSetDataBuffers(self.chandle,
                                                                        self.channel_sgnl,
                                                                        ctypes.byref(self.buffer_sgnl[i]),
                                                                        self.nSamples,
                                                                        dataType,
                                                                        i,
                                                                        downSampleMode,
                                                                        action)
            assert_pico_ok(self.status["set_sgnl_buffer"])
            action = add

    def block_measurement(self, number = 10):

        assert number < self.max_nwf

        if number != self.current_nwf:

            # set memory segments in buffer (segment per waveform)
            maxSegments = ctypes.c_uint64(number)
            self.status["SetNrofSegments"] = ps.ps6000aMemorySegments(self.chandle, number, ctypes.byref(maxSegments))
            assert_pico_ok(self.status["SetNrofSegments"])

            # Set number of captures
            self.status["SetNrofCaptures"] = ps.ps6000aSetNoOfCaptures(self.chandle, number)
            assert_pico_ok(self.status["SetNrofCaptures"])

            # setup buffer
            self.buffer_setup(number)

            self.current_nwf = number

        # run block
        timeIndisposedMs = ctypes.c_double(0)
        self.status["runBlock"] = ps.ps6000aRunBlock(self.chandle,
                                                     self.noOfPreTriggerSamples,
                                                     self.noOfPostTriggerSamples,
                                                     self.timebase,
                                                     ctypes.byref(timeIndisposedMs),
                                                     0,
                                                     None,
                                                     None)
        assert_pico_ok(self.status["runBlock"])

        # Check for data collection to finish using ps6000aIsReady
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            ps.ps6000aIsReady(self.chandle, ctypes.byref(ready))

        # Get data from scope
        noOfSamples = ctypes.c_uint64(self.nSamples)
        end = number-1
        downSampleMode = enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"]

        # Creates an overflow location for each segment
        overflow = (ctypes.c_int16 * number)()

        self.status["getValues"] = ps.ps6000aGetValuesBulk(self.chandle,
                                                            0,
                                                            ctypes.byref(noOfSamples),
                                                            0,
                                                            end,
                                                            1,
                                                            downSampleMode,
                                                            ctypes.byref(overflow))
        assert_pico_ok(self.status["getValues"])

        # get max ADC value
        minADC = ctypes.c_int16()
        maxADC = ctypes.c_int16()

        self.status["getADCLimit"] = ps.ps6000aGetAdcLimits(self.chandle, self.resolution, ctypes.byref(minADC), ctypes.byref(maxADC))
        assert_pico_ok(self.status["getADCLimit"])
        self.stop_scope()

        # convert ADC counts data to mV
        adc2mVMax_trgch_list = np.zeros((number, self.nSamples))
        for i, buffers in enumerate(self.buffer_trg):
            adc2mVMax_trgch_list[i] = adc2mV(buffers, self.voltrange_trg, maxADC)

        adc2mVMax_sgnlch_list = np.zeros((number, self.nSamples))
        for i, buffers in enumerate(self.buffer_sgnl):
            adc2mVMax_sgnlch_list[i] = adc2mV(buffers, self.voltrange_sgnl, maxADC)

        # Create time data
        timevals = np.tile(np.linspace(0, self.nSamples * self.timeInterval * 1000000000, self.nSamples), (number, 1))

        self.logger.info(f"block measurement of {number} Waveforms performed. trigger_ch: {self.channel_trg}, signal_ch: {self.channel_sgnl}")

        # create dataset and return
        dataset = Measurement(time_data=timevals, signal_data=adc2mVMax_sgnlch_list, trigger_data=adc2mVMax_trgch_list)
        return dataset

        # TODO this produces weird data

    
    def get_datastream(channel = 2):
        
        # TODO: put in studd for continuous data stream here
        pass

    def stop_scope(self):

        self.status["stop"] = ps.ps6000aStop(self.chandle)
        assert_pico_ok(self.status["stop"])

        self.logger.info("picoscope stopped")

    def close_connection(self):
 
        self.status["stop"] = ps.ps6000aStop(self.chandle)
        assert_pico_ok(status["stop"])

        self.status["close"] = ps.ps6000aCloseUnit(self.chandle)
        assert_pico_ok(self.status["close"])

        self.logger.info("picoscope stopped and connection closed")


if __name__ == "__main__":
    ps = Picoscope()
    ps.block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=2000, number=100)
    ps.close_scope()
