#!/usr/bin/python3
import logging
import time
import config

import numpy as np
from devices.Laser import Laser
from devices.Picoscope import Picoscope
from devices.Rotation import Rotation
from devices.uBase import uBase

#-----------------------------------------------------

def signal_handle(signum, frame):
     logging.getLogger("OMCU").log(60, f'{signum}: received, frame: {frame}')
     exit(1)

def check_config():

    print()
    time.sleep(1)
    logging.getLogger("OMCU").info("Checking if config file is valid")
    print("Checking if config file is valid...")
    time.sleep(1)
    warning = False

    if config.OUT_PATH == "":
        logging.getLogger("OMCU").warning("OUT_PATH is empty")
        print("WARNING: OUT_PATH is empty, data might not be stored correctly!")
        time.sleep(1)
        warning = True
    if config.LOG_FILE == "":
        logging.getLogger("OMCU").warning("LOG_FILE is empty")
        print("WARNING: LOG_FILE is empty, log might not be stored correctly!")
        time.sleep(1)
        warning = True
    if config.COOLDOWN_TIME not in range(0,24*60,1):
        logging.getLogger("OMCU").warning(f"Cooldown time {config.COOLDOWN_TIME} minutes might not be reasonable")
        print(f"WARNING: Cooldown time {config.COOLDOWN_TIME} minutes might not be reasonable!")
        time.sleep(1)
        warning = True
    if config.COOLDOWN_HV not in range(0,120):
        logging.getLogger("OMCU").warning(f"Cooldown HV {config.COOLDOWN_HV} V exceeds max uBase HV!")
        print(f"WARNING: Cooldown HV {config.COOLDOWN_HV} V exceeds max uBase HV!")
        time.sleep(1)
        warning = True
    if config.LASER_SETUP_TIME not in range(0,6*60,1):
        logging.getLogger("OMCU").warning(f"Laser startup time time {config.LASER_SETUP_TIME} minutes might not be reasonable")
        print(f"WARNING: Laser startup time time {config.LASER_SETUP_TIME} minutes might not be reasonable!")
        time.sleep(1)
        warning = True

    if not (config.PHOTOCATHODE_SCAN or config.FRONTAL_HV_SCAN or config.CHARGE_LINEARITY_SCAN or config.DARK_COUNT_SCAN):
        logging.getLogger("OMCU").warning(f"No testing procedures set in config")
        print("WARNING: NO testing procedures set in config. No tests will be performed!")
        time.sleep(1)
        warning = True

    if config.PCS_DATAFILE == "" and config.PHOTOCATHODE_SCAN:
        logging.getLogger("OMCU").warning("PCS_DATAFILE is empty")
        print("WARNING: PCS_DATAFILE is empty, data might not be stored correctly!")
        time.sleep(1)
        warning = True
    if (np.max(config.PCS_PHI_LIST) > 355 or np.min(config.PCS_THETA_LIST) < 0) and config.PHOTOCATHODE_SCAN:
        logging.getLogger("OMCU").warning("PCS_PHI_LIST exceeds limits of (0,355)")
        print("WARNING: PCS_PHI_LIST exceeds limits of (0,355). Procedure might not finish correctly!")
        time.sleep(1)
        warning = True
    if (np.max(config.PCS_THETA_LIST) > 100 or np.min(config.PCS_THETA_LIST) < 0) and config.PHOTOCATHODE_SCAN:
        logging.getLogger("OMCU").warning("PCS_THETA_LIST exceeds limits of (0,100)")
        print("WARNING: PCS_THETA_LIST exceeds limits of (0,100). Procedure might not finish correctly!")
        time.sleep(1)
        warning = True

    if config.FHVS_DATAFILE == "" and config.FRONTAL_HV_SCAN:
        logging.getLogger("OMCU").warning("FHVS_DATAFILE is empty")
        print("WARNING: FHVS_DATAFILE is empty, data might not be stored correctly!")
        time.sleep(1)
        warning = True
    if (np.max(config.FHVS_HV_LIST) > 120 or np.min(config.FHVS_HV_LIST) < 0) and config.FRONTAL_HV_SCAN:
        logging.getLogger("OMCU").warning("FHVS_HV_LIST exceeds limits of (0,120)")
        print("WARNING: FHVS_HV_LIST exceeds limits of (0,120). Procedure might not finish correctly!")
        time.sleep(1)
        warning = True

    if config.CLS_DATAFILE == "" and config.CHARGE_LINEARITY_SCAN:
        logging.getLogger("OMCU").warning("CLS_DATAFILE is empty")
        print("WARNING: CLS_DATAFILE is empty, data might not be stored correctly!")
        time.sleep(1)
        warning = True
    if (np.max(config.CLS_LASER_TUNE_LIST) > 800 or np.min(config.CLS_LASER_TUNE_LIST) < 600) and config.CHARGE_LINEARITY_SCAN:
        logging.getLogger("OMCU").warning("CLS_LASER_TUNE_LIST exceeds limits of (600,800)")
        print("WARNING: CLS_LASER_TUNE_LIST exceeds limits of (600,800). Procedure might not finish correctly!")
        time.sleep(1)
        warning = True

    if config.DCS_DATAFILE == "" and config.DARK_COUNT_SCAN:
        logging.getLogger("OMCU").warning("DCS_DATAFILE is empty")
        print("WARNING: DCS_DATAFILE is empty, data might not be stored correctly!")
        time.sleep(1)
        warning = True
    if (np.max(config.DCS_HV_LIST) > 120 or np.min(config.DCS_HV_LIST) < 0) and config.DARK_COUNT_SCAN:
        logging.getLogger("OMCU").warning("DCS_HV_LIST exceeds limits of (0,120)")
        print("WARNING: DCS_HV_LIST exceeds limits of (0,120). Procedure might not finish correctly!")
        time.sleep(1)
        warning = True

    while warning:
        answer = input("please acknowledge these warnings [y/n]:\n>>> ")
        if answer.lower() in ["y", "yes"]: break
        if answer.lower() in ["n", "no"]:
            print("ERROR: OMCU determined as not set up by user input. Exiting program. Good bye!")
            exit()

    logging.getLogger("OMCU").info("Config check complete")
    time.sleep(1)
    print("Config check complete!")
    time.sleep(1)

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

    logging.addLevelName(60, "SIGNAL")

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

def measure_occ(threshold_signal=-4, iterations=10000):
    
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
    dataset = Picoscope.Instance().block_measurement(iterations)
    occ = dataset.calculate_occ(threshold_signal=threshold_signal)

    logging.getLogger("OMCU").info(f"measured occupancy to be {occ}")

    return occ

def measure_gain(threshold_signal=-4, iterations=10000):

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
    dataset = Picoscope.Instance().block_measurement(iterations)
    gain, _ = dataset.calculate_gain(threshold_signal=threshold_signal)

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
        dataset = Picoscope.Instance().block_measurement(waveforms)
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

def tune_gain(g_min, g_max, V_start=None, V_step=1, delay=2, threshold_signal=-4, waveforms=10000, iterations=10):

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
        dataset = Picoscope.Instance().block_measurement(waveforms)
        gain, _ = dataset.calculate_gain(signal_threshold=threshold_signal)

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

            # set current tune vals as new starting positions
            laser_start = laser_val
            V_start     = HV_val

            # measure after tuning to avoid cross-influence
            dataset = Picoscope.Instance().block_measurement(nr_waveforms)
            gain, _ = dataset.calculate_gain(signal_threshold=signal_threshold)
            occ     = dataset.calculate_occ(signal_threshold=signal_threshold)

            if occ > occ_min and occ < occ_max and gain > gain_min and gain:
                print(f"reached occupancy of {occ} at {laser_val} laser tune value and gain of {round(gain,2)} at {HV_val} V.")
                break
            if iters >= iterations:
                print(f"WARNING: could not reach desired tuning values within {iterations} iterations. Aborting tuning!")
                print(f"reached occupancy of {occ} at {laser_val} laser tune value and gain of {round(gain,2)} at {HV_val} V.")

    if tune_mode == "none":

        dataset = Picoscope.Instance().block_measurement(nr_waveforms)
        gain, _ = dataset.calculate_gain(signal_threshold=signal_threshold)
        occ     = dataset.calculate_occ(signal_threshold=signal_threshold)
        print(f"\nwill not tune gain and occupancy. measured:\nocc:\t{occ}\ngain:\t{round(gain,2)}")

    if tune_mode not in ["none", "iter", "single", "only_gain", "only_occ"]:

        dataset = Picoscope.Instance().block_measurement(nr_waveforms)
        gain, _ = dataset.calculate_gain(signal_threshold=signal_threshold)
        occ     = dataset.calculate_occ(signal_threshold=signal_threshold)
        print(f"WARNING: Can not make sense of tuning mode. Will proceed without tuning. measured:\nocc:\t{occ}\ngain:\t{round(gain,2)}")

    end_time = time.time()
    print(f"Total time for tuning: {round((end_time - start_time) / 60, 0)} minutes")
