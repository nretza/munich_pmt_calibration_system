#!/usr/bin/python3
import time
import logging
import numpy as np

from devices.Laser import Laser
from devices.Picoscope import Picoscope
from devices.uBase import uBase
from devices.Rotation import Rotation

#-----------------------------------------------------

def setup_file_logging(logging_file: str, logging_level = logging.INFO, logging_formatter=None):
    """
    Sets up logging to a file given logging level and format.

    How it works: Each module has its own logger. Here, a logging handler is created, which outputs to
    the desired file. This handler is then passed to the root logger, from which all other loggers inherit.

    PARAMETERS
    ---------
    logging_file: the desired output file
    logging_level: the level to which should be outputted. Default: logging.INFO
    logging_format: the desired output format of the handler Default: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    """

    if not logging_formatter:
        logging_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    log_handler = logging.FileHandler(filename=logging_file)
    log_handler.setLevel(logging_level)
    log_handler.setFormatter(logging_formatter)

    #settings for root logger. all loggers inherit from root
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().addHandler(log_handler)

    return log_handler

#-----------------------------------------------------

def gaussian(x, a, mu, sigma):
     return a * np.exp(- (x - mu) ** 2 / (sigma ** 2))

#-----------------------------------------------------

def meassure_occ(threshold_signal=-4, threshold_pico=2000, iterations=10000):
    
    # laser on
    if not Laser.Instance().get_ld() == 1:
        try:
            Laser.Instance().on_pulsed()
        except:
            logging.getLogger("OMCU").error("Error while tuning occupancy. Laser cannot be turned on")
            raise RuntimeError

    # uBase reachable
    if not len(uBase.Instance().getUID()): 
        logging.getLogger("OMCU").error("Error while tuning occupancy. uBase can not be reached")
        raise RuntimeError

    # take data and calc occupancy
    dataset = Picoscope.Instance().block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=threshold_pico, number=iterations)
    occ = dataset.calculate_occ(threshold_signal=threshold_signal)

    logging.getLogger("OMCU").info(f"measured occupancy to be {occ}")

    return occ

def meassure_gain(threshold_signal=-4, threshold_pico=2000, iterations=10000):

    # laser on
    if not Laser.Instance().get_ld() == 1: 
        try:
            Laser.Instance().on_pulsed()
        except:
            logging.getLogger("OMCU").error("Error while tuning occupancy. Laser cannot be turned on")
            raise RuntimeError

    # uBase reachable
    if not len(uBase.Instance().getUID()):
        logging.getLogger("OMCU").error("Error while tuning occupancy. uBase can not be reached")
        raise RuntimeError

    # take data and calc gain
    dataset = Picoscope.Instance().block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=threshold_pico, number=iterations)
    gain = dataset.calculate_gain(threshold_signal=threshold_signal)

    logging.getLogger("OMCU").info(f"measured occupancy to be {gain}")

    return gain

#-----------------------------------------------------

def tune_occ(occ_min, occ_max, laser_tune_start=None, laser_tune_step=1, delay=2, threshold_pico=2000, threshold_signal=-4, waveforms=10000,  iterations=10):

    # Rotation stage in home position
    Rotation.Instance().go_home()
    if not max(Rotation.Instance().get_position()) <= 1: 
        logging.getLogger("OMCU").error("Error while tuning occupancy. Rotation stage is unable to go to home position")
        raise RuntimeError

    # laser on
    if not Laser.Instance().get_ld() == 1: 
        try:
            Laser.Instance().on_pulsed()
        except:
            logging.getLogger("OMCU").error("Error while tuning occupancy. Laser cannot be turned on")
            raise RuntimeError

    # uBase reachable
    if not len(uBase.Instance().getUID()):
        logging.getLogger("OMCU").error("Error while tuning occupancy. uBase can not be reached")
        raise RuntimeError

    # set start value of laser tune
    if not laser_tune_start:
        laser_tune_start = Laser.Instance().get_tune_value()

    # numbers match
    assert occ_min <= occ_max

    logging.getLogger("OMCU").info(f"tuning occupancy at Dy10={round(uBase.Instance().getDy10())} to value between {occ_min} and {occ_max}")

    laser_tune = laser_tune_start
    i = 0

    while True:

        Laser.Instance().set_tune_value(laser_tune)
        time.sleep(delay)
        dataset = Picoscope.Instance().block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=threshold_pico, number=waveforms)
        occ = dataset.calculate_occ(signal_threshold=threshold_signal)

        if i > iterations:
            logging.getLogger("OMCU").warning(f"could not tune ocupancy in {iterations} iterations. Leaving with occupancy of {round(occ,2)}")
            break

        if occ < occ_min:
            laser_tune -= laser_tune_step
            logging.getLogger("OMCU").info(f"measured occupancy to be {occ}, decreasing tune to {laser_tune}")
        elif occ > occ_max:
            laser_tune += laser_tune_step
            logging.getLogger("OMCU").info(f"measured occupancy to be {occ}, increasing tune to {laser_tune}")
        else:
            logging.getLogger("OMCU").info(f"measured occupancy to be {occ}, leaving laser tuning")
            break

        i+=1

    return occ, laser_tune

def tune_gain(g_min, g_max, V_start=None, V_step=1, threshold_pico=2000, delay=2, threshold_signal=-4, waveforms=10000, iterations=10):

    # Rotation stage in home position
    Rotation.Instance().go_home()
    if not max(Rotation.Instance().get_position()) <= 1: 
        logging.getLogger("OMCU").error("Error while tuning gain. Rotation stage is unable to go to home position")
        raise RuntimeError
    
    # laser on
    if not Laser.Instance().get_ld() == 1: 
        try:
            Laser.Instance().on_pulsed()
        except:
            logging.getLogger("OMCU").error("Error while tuning occupancy. Laser cannot be turned on")
            raise RuntimeError

    # uBase reachable
    if not len(uBase.Instance().getUID()): 
        logging.getLogger("OMCU").error("Error while tuning occupancy. uBase can not be reached")
        raise RuntimeError

    # set start value of voltage
    if not V_start:
        V_start = uBase.Instance().getDy10()
    
    # numbers match
    assert g_min <= g_max  

    logging.getLogger("OMCU").info(f"tuning gain to value between {g_min} and {g_max}")

    V = V_start
    i = 0

    while True:

        uBase.Instance().SetVoltage(V)
        time.sleep(delay)
        dataset = Picoscope.Instance().block_measurement(trgchannel=0, sgnlchannel=2, direction=2, threshold=threshold_pico, number=waveforms)
        gain = dataset.calculate_gain(signal_threshold=threshold_signal)

        if i > iterations:
            logging.getLogger("OMCU").warning(f"could not tune gain in {iterations} iterations. Leaving with gain of {round(gain,2)}")
            break

        if gain < g_min:
            V += V_step
            logging.getLogger("OMCU").info(f"measured gain to be {round(gain,2)}, moving HV up to {V} Volt")
        elif gain > g_max:
            V -= V_step
            logging.getLogger("OMCU").info(f"measured gain to be {round(gain,2)}, moving HV down to {V} Volt")
        else:
            logging.getLogger("OMCU").info(f"measured gain to be {round(gain,2)}, leaving gain tuning")
            break

        i+=1

    return gain, V

#------------------------------------

def tune_parameters(tune_mode,
                    nr_waveforms = None,
                    gain_min = None,
                    gain_max = None,
                    V_start = None,
                    V_step = None,
                    occ_min = None,
                    occ_max = None,
                    laser_start = None,
                    laser_step = None,
                    signal_threshold = None,
                    iterations = None):

    start_time = time.time()

    if tune_mode == "single" or tune_mode == "only_occ":

        assert occ_min and occ_max and laser_step and signal_threshold and nr_waveforms and iterations

        print(f"\ntuning occupancy between {occ_min} and {occ_max}")
        occ, laser_tune = tune_occ(occ_min=occ_min,
                                   occ_max=occ_max,
                                   laser_tune_start=laser_start,
                                   laser_tune_step=laser_step,
                                   threshold_signal=signal_threshold,
                                   waveforms=nr_waveforms,
                                   iterations=iterations)
        print(f"reached occupancy of {occ} at {laser_tune} laser tune value")

    if tune_mode == "single" or tune_mode == "only_gain":

        assert gain_min and gain_max and V_step and signal_threshold and nr_waveforms and iterations

        print(f"\ntuning gain between {gain_min} and {gain_max}")
        gain, HV = tune_gain(g_min=gain_min,
                             g_max=gain_max,
                             V_start=V_start,
                             V_step=V_step,
                             threshold_signal=signal_threshold,
                             waveforms=nr_waveforms,
                             iterations=iterations)
        print(f"reached gain {gain} at Voltage of {HV} Volt")

    if tune_mode == "iter":

        assert occ_min and occ_max and laser_step and signal_threshold and nr_waveforms and iterations
        assert gain_min and gain_max and V_step and signal_threshold and nr_waveforms and iterations
        
        iters = 0

        print(f"\ntuning occupancy between {occ_min} and {occ_max} and gain between {gain_min} and {gain_max} iteratively")

        while True:

            iters += 1

            _, laser_val = tune_occ(occ_min=occ_min,
                                    occ_max=occ_max,
                                    laser_tune_start=laser_start,
                                    laser_tune_step=laser_step,
                                    threshold_signal=signal_threshold,
                                    waveforms=nr_waveforms)

            _, HV_val = tune_gain(g_min=gain_min,
                                  g_max=gain_max,
                                  V_start=V_start,
                                  V_step=V_step,
                                  threshold_signal=signal_threshold,
                                  waveforms=nr_waveforms)


            # measure after tuning to avoid cross-influence
            dataset = Picoscope.Instance().block_measurement(number=nr_waveforms)
            gain = dataset.calculate_gain(signal_threshold=signal_threshold)
            occ  = dataset.calculate_occ(signal_threshold=signal_threshold)

            if occ > occ_min and occ < occ_max and gain > gain_min and gain:
                print(f"reached occupancy of {occ} at {laser_val} laser tune value and gain of {round(gain,2)} at {HV_val} V.")
                break
            if iters >= iterations:
                print(f"WARNING: could not reach desired tuning values within {iterations} iterations. Aborting tuning!")
                print(f"reached occupancy of {occ} at {laser_val} laser tune value and gain of {round(gain,2)} at {HV_val} V.")

    if tune_mode == "none":

        dataset = Picoscope.Instance().block_measurement(number=nr_waveforms)
        gain = dataset.calculate_gain(signal_threshold=signal_threshold)
        occ  = dataset.calculate_occ(signal_threshold=signal_threshold)
        print(f"\nwill not tune gain and occupancy. measured:\nocc:\t{occ}\ngain:\t{round(gain,2)}")

    if tune_mode not in ["none", "iter", "single", "only_gain", "only_occ"]:

        dataset = Picoscope.Instance().block_measurement(number=nr_waveforms)
        gain = dataset.calculate_gain(signal_threshold=signal_threshold)
        occ  = dataset.calculate_occ(signal_threshold=signal_threshold)
        print(f"WARNING: Can not make sense of tuning mode. Will proceed without tuning. measured:\nocc:\t{occ}\ngain:\t{round(gain,2)}")

    end_time = time.time()
    print(f"Total time for tuning: {round((end_time - start_time) / 60, 0)} minutes")