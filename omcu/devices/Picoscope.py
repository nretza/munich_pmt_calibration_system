#!/usr/bin/python3
import ctypes

import numpy as np
from devices.device import device
from picosdk.functions import assert_pico_ok
from picosdk.PicoDeviceEnums import picoEnum as enums
from picosdk.ps6000a import ps6000a as ps
from utils.Measurement import Measurement


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

        # maximum number of waveforms as to not overflow buffer (5 Gigasamples)
        self.max_nwf = int ( 5e9 / (2 * post_trigger_samples + pre_trigger_samples)) 
        
        # current wf number the picoscope is set up to
        self.current_nwf_block  = None
        self.current_nwf_stream = None
        self.current_nr_samples_stream  = None

        # resolution and timebase (set later)
        self.resolution = enums.PICO_DEVICE_RESOLUTION["PICO_DR_12BIT"]
        self.enabledChannelFlags = enums.PICO_CHANNEL_FLAGS["PICO_CHANNEL_A_FLAGS"] + enums.PICO_CHANNEL_FLAGS["PICO_CHANNEL_C_FLAGS"]
        self.min_timebase_block  = 2 # 800 ps
        self.min_timebase_stream = 4 # 3.6 ns
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

        # nr of samples in block mode
        self.noOfPreTriggerSamples = pre_trigger_samples
        self.noOfPostTriggerSamples = post_trigger_samples
        self.nSamples = self.noOfPreTriggerSamples + self.noOfPostTriggerSamples

        self.open_connection()
        self.set_up_for = "none"


    def open_connection(self):
    
        # open connection to picoscope
        self.status["openunit"] = ps.ps6000aOpenUnit(ctypes.byref(self.chandle), None, self.resolution)
        assert_pico_ok(self.status["openunit"])


    def adc2mV(self, bufferADC, range, maxADC):
        channelInputRanges = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000]
        return (np.array(bufferADC, dtype=np.float32) * channelInputRanges[range]) / maxADC.value


    def stop_scope(self):

        self.status["stop"] = ps.ps6000aStop(self.chandle)
        assert_pico_ok(self.status["stop"])

        self.logger.debug("picoscope stopped")


    def close_connection(self):

        self.status["stop"] = ps.ps6000aStop(self.chandle)
        assert_pico_ok(self.status["stop"])

        self.status["close"] = ps.ps6000aCloseUnit(self.chandle)
        assert_pico_ok(self.status["close"])

        self.logger.info("picoscope stopped and connection closed")


    #---------------------------


    def channel_setup_for_block(self):
        
        # turn signal and trigger channels on
        self.logger.info(f"Setting up channels. trig_ch: {self.channel_trg}, signal_ch: {self.channel_sgnl}")
        self.status["setTriggerCh"] = ps.ps6000aSetChannelOn(self.chandle, self.channel_trg, self.coupling_trg, self.voltrange_trg, 0, self.bandwidth)
        self.status["setSignalCh"]  = ps.ps6000aSetChannelOn(self.chandle, self.channel_sgnl, self.coupling_sgnl, self.voltrange_sgnl, 0, self.bandwidth)
        assert_pico_ok(self.status["setTriggerCh"])
        assert_pico_ok(self.status["setSignalCh"])

        # turn other channels off
        for channel in range(4):
            if channel in [self.channel_sgnl, self.channel_trg]: continue
            self.status["setChannel", channel] = ps.ps6000aSetChannelOff(self.chandle, channel)
            assert_pico_ok(self.status["setChannel", channel])

        # get ADC limits
        self.status["getADCimits"] = ps.ps6000aGetAdcLimits(self.chandle, self.resolution, ctypes.byref(self.minADC), ctypes.byref(self.maxADC))
        assert_pico_ok(self.status["getADCimits"])


    def timebase_setup_for_block(self, samples):

        # Get fastest available timebase
        self.status["getMinimumTimebaseStateless"] = ps.ps6000aGetMinimumTimebaseStateless(self.chandle,
                                                                                           self.enabledChannelFlags,
                                                                                           ctypes.byref(self.timebase),
                                                                                           ctypes.byref(self.timeInterval),
                                                                                           self.resolution)
        assert_pico_ok(self.status["getMinimumTimebaseStateless"])

        if self.timebase.value < self.min_timebase_block:
            max_samples = ctypes.c_uint32(0)
            self.status["getTimebase"] = ps.ps6000aGetTimebase(self.chandle,
                                                               self.min_timebase_block,
                                                               samples,
                                                               ctypes.byref(self.timeInterval),
                                                               ctypes.byref(max_samples),
                                                               0)
            assert_pico_ok(self.status["getTimebase"])
            assert max_samples >= samples
            self.timebase = ctypes.c_uint32(self.min_timebase_block)
            
        self.logger.info(f"Setup to get the fastest available timebase: {self.timebase.value}.")


    def trigger_setup_for_block(self):

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


    def buffer_setup_for_block(self, number):

        assert number < self.max_nwf
        self.logger.debug(f"setting up buffer for {number} waveforms")
        self.logger.debug(f"will store data without downsampling. One trigger channel and one signal channel, several waveforms - indicated by number")

        # Create buffers
        self.buffer_trg  = ((ctypes.c_int16 * self.nSamples) * number)()
        self.buffer_sgnl = ((ctypes.c_int16 * self.nSamples) * number)()

        # Set data buffers
        dataType       = enums.PICO_DATA_TYPE["PICO_INT16_T"]
        downSampleMode = enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"]
        clear          = enums.PICO_ACTION["PICO_CLEAR_ALL"]
        add            = enums.PICO_ACTION["PICO_ADD"]

        # action for very fist buffer. then overwritten in code
        action = clear | add

        for i in range(0, number):
            self.status["set_trg_buffer"] = ps.ps6000aSetDataBuffer(self.chandle,
                                                                    self.channel_trg,
                                                                    ctypes.byref(self.buffer_trg[i]),
                                                                    self.nSamples,
                                                                    dataType,
                                                                    i,
                                                                    downSampleMode,
                                                                    action)
            assert_pico_ok(self.status["set_trg_buffer"])

            action = add
            self.status["set_sgnl_buffer"] = ps.ps6000aSetDataBuffer(self.chandle,
                                                                        self.channel_sgnl,
                                                                        ctypes.byref(self.buffer_sgnl[i]),
                                                                        self.nSamples,
                                                                        dataType,
                                                                        i,
                                                                        downSampleMode,
                                                                        action)
            assert_pico_ok(self.status["set_sgnl_buffer"])


    def block_measurement(self, nr_waveforms = 10):

        assert nr_waveforms < self.max_nwf

        if self.set_up_for != "block_measurement":
            
            self.close_connection()
            self.open_connection()
            self.logger.info(f"configuring for block measurements")
            self.channel_setup_for_block()
            self.timebase_setup_for_block(self.nSamples)
            self.trigger_setup_for_block()
            self.set_up_for = "block_measurement"

            self.current_nwf_stream        = None
            self.current_nr_samples_stream = None

        if nr_waveforms != self.current_nwf_block:

            # set memory segments in buffer (segment per waveform)
            maxSegments = ctypes.c_uint64(nr_waveforms)
            self.status["SetNrofSegments"] = ps.ps6000aMemorySegments(self.chandle, nr_waveforms, ctypes.byref(maxSegments))
            assert_pico_ok(self.status["SetNrofSegments"])

            # Set number of captures
            self.status["SetNrofCaptures"] = ps.ps6000aSetNoOfCaptures(self.chandle, nr_waveforms)
            assert_pico_ok(self.status["SetNrofCaptures"])

            # setup buffer
            self.buffer_setup_for_block(nr_waveforms)

            self.current_nwf_block = nr_waveforms

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
        end = nr_waveforms - 1
        downSampleMode = enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"]

        # Creates an overflow location for each segment
        overflow = (ctypes.c_int16 * nr_waveforms)()

        self.status["getValues"] = ps.ps6000aGetValuesBulk(self.chandle,
                                                            0,
                                                            ctypes.byref(noOfSamples),
                                                            0,
                                                            end,
                                                            1,
                                                            downSampleMode,
                                                            ctypes.byref(overflow))
        assert_pico_ok(self.status["getValues"])

        self.stop_scope()

        # convert ADC counts data to mV
        adc2mVMax_trgch_list  = self.adc2mV(self.buffer_trg, self.voltrange_trg, self.maxADC)
        adc2mVMax_sgnlch_list = self.adc2mV(self.buffer_sgnl, self.voltrange_sgnl, self.maxADC)

        # Create time data
        timevals = np.tile(np.linspace(0, self.nSamples * self.timeInterval.value * 1000000000, self.nSamples, dtype=np.float32), (nr_waveforms, 1))

        self.logger.info(f"block measurement of {nr_waveforms} Waveforms performed. trigger_ch: {self.channel_trg}, signal_ch: {self.channel_sgnl}")

        # create dataset and return
        dataset = Measurement(time_data=timevals, signal_data=adc2mVMax_sgnlch_list, trigger_data=adc2mVMax_trgch_list)
        return dataset


#---------------------------


    def chanel_setup_for_stream(self):

        # turn on signal channel
        self.logger.info(f"Setting up signal_ch: {self.channel_sgnl}")
        self.status["setSignalCh"]  = ps.ps6000aSetChannelOn(self.chandle, self.channel_sgnl, self.coupling_sgnl, self.voltrange_sgnl, 0, self.bandwidth)
        assert_pico_ok(self.status["setSignalCh"])

        # turn other channels off
        for channel in range(4):
            if channel == self.channel_sgnl: continue
            self.status["setChannel", channel] = ps.ps6000aSetChannelOff(self.chandle, channel)
            assert_pico_ok(self.status["setChannel", channel])

        # get ADC limits
        self.status["getADCimits"] = ps.ps6000aGetAdcLimits(self.chandle, self.resolution, ctypes.byref(self.minADC), ctypes.byref(self.maxADC))
        assert_pico_ok(self.status["getADCimits"])


    def timebase_setup_for_stream(self, samples):

        # Get fastest available timebase
        self.status["getMinimumTimebaseStateless"] = ps.ps6000aGetMinimumTimebaseStateless(self.chandle,
                                                                                           self.enabledChannelFlags,
                                                                                           ctypes.byref(self.timebase),
                                                                                           ctypes.byref(self.timeInterval),
                                                                                           self.resolution)
        assert_pico_ok(self.status["getMinimumTimebaseStateless"])

        if self.timebase.value < self.min_timebase_stream:
            max_samples = ctypes.c_uint32(0)
            self.status["getTimebase"] = ps.ps6000aGetTimebase(self.chandle,
                                                               self.min_timebase_stream,
                                                               samples,
                                                               ctypes.byref(self.timeInterval),
                                                               ctypes.byref(max_samples),
                                                               0)
            assert_pico_ok(self.status["getTimebase"])
            assert max_samples >= samples
            self.timebase = ctypes.c_uint32(self.min_timebase_stream)

        self.logger.info(f"Setup to get the fastest available timebase: {self.timebase.value}.")


    def buffer_setup_for_stream(self, nr_samples, nr_waveforms):

        self.logger.debug(f"setting up buffer for {nr_waveforms} waveforms of {nr_samples} samples")
        self.logger.debug(f"will store data without downsampling. One signal channel, several waveforms - indicated by number")

        # Set data buffer
        self.buffer_stream = ((ctypes.c_int16 * nr_samples) * nr_waveforms)()
        dataType       = enums.PICO_DATA_TYPE["PICO_INT16_T"]
        downSampleMode = enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"]
        clear          = enums.PICO_ACTION["PICO_CLEAR_ALL"]
        add            = enums.PICO_ACTION["PICO_ADD"]
        action = clear | add

        for i in range(0, nr_waveforms):
            self.status["set_stream_buffer"] = ps.ps6000aSetDataBuffer(self.chandle,
                                                                    self.channel_sgnl,
                                                                    ctypes.byref(self.buffer_stream[i]),
                                                                    nr_samples,
                                                                    dataType,
                                                                    i,
                                                                    downSampleMode,
                                                                    action)
            assert_pico_ok(self.status["set_stream_buffer"])
            action = add

    
    def get_datastream(self, nr_samples, nr_waveforms):
        
        if self.set_up_for != "streaming":

            self.close_connection()
            self.open_connection()
            self.logger.info(f"Configuring for streaming data")
            self.chanel_setup_for_stream()
            self.timebase_setup_for_stream(nr_samples)
            self.set_up_for = "streaming"

            self.current_nwf_block = None

        if nr_samples != self.current_nr_samples_stream or nr_waveforms != self.current_nwf_stream:

            # set memory segments in buffer (segment per waveform)
            maxSegments = ctypes.c_uint64(nr_waveforms)
            self.status["SetNrofSegments"] = ps.ps6000aMemorySegments(self.chandle, nr_waveforms, ctypes.byref(maxSegments))
            assert_pico_ok(self.status["SetNrofSegments"])

            # Set number of captures
            self.status["SetNrofCaptures"] = ps.ps6000aSetNoOfCaptures(self.chandle, nr_waveforms)
            assert_pico_ok(self.status["SetNrofCaptures"])

            # setup buffer
            self.buffer_setup_for_stream(nr_samples, nr_waveforms)

            self.current_nwf_stream        = nr_waveforms
            self.current_nr_samples_stream = nr_samples

        # run block
        timeIndisposedMs = ctypes.c_double(0)
        self.status["runBlock"] = ps.ps6000aRunBlock(self.chandle,
                                                     0,
                                                     nr_samples,
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
        noOfSamples = ctypes.c_uint64(nr_samples)
        end = nr_waveforms - 1
        downSampleMode = enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"]

        # Creates an overflow location for each segment
        overflow = (ctypes.c_int16 * nr_waveforms)()

        self.status["getValues"] = ps.ps6000aGetValuesBulk(self.chandle,
                                                            0,
                                                            ctypes.byref(noOfSamples),
                                                            0,
                                                            end,
                                                            1,
                                                            downSampleMode,
                                                            ctypes.byref(overflow))
        assert_pico_ok(self.status["getValues"])

        self.stop_scope()

        self.status["getADCimits"] = ps.ps6000aGetAdcLimits(self.chandle, self.resolution, ctypes.byref(self.minADC), ctypes.byref(self.maxADC))
        assert_pico_ok(self.status["getADCimits"])

        # convert ADC counts data to mV
        adc2mVMax_sgnlch_list = self.adc2mV(self.buffer_stream, self.voltrange_sgnl, self.maxADC)

        # Create time data
        timevals = np.linspace(0, nr_samples * self.timeInterval.value * 1000000000, nr_samples, dtype=np.float32)

        data_sgnl = np.zeros((nr_waveforms, nr_samples, 2))
        data_sgnl[:, :, 0] = timevals
        data_sgnl[:, :, 1] = adc2mVMax_sgnlch_list

        self.logger.info(f"block measurement of {nr_waveforms} Waveforms of {nr_samples} samples performed. signal_ch: {self.channel_sgnl}")

        return data_sgnl



#---------------------------------------------

if __name__ == "__main__":
    Picoscope.Instance().block_measurement(100)
    Picoscope.Instance().close_connection()
