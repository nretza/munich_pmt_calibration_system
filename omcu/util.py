import time
import logging
import numpy as np

from Waveform import Waveform
from devices.Laser import Laser
from devices.Picoscope import Picoscope
from devices.HV_supply import HV_supply
from devices.Rotation import Rotation
from devices.Powermeter import Powermeter
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

def filter_dataset_by_threshold(threshold, dataset):
    dataset_filtered = []
    for data in dataset:
        minval = np.min(data[:, 1])
        if minval < threshold:
            dataset_filtered.append(data)
    return dataset_filtered

def filter_data_and_triggerset_by_threshold(threshold, dataset, triggerset):
    dataset_filtered = []
    triggerset_filtered = []
    for data, trigger in zip(dataset, triggerset):
        minval = np.min(data[:, 1])
        if minval < threshold:
            dataset_filtered.append(data)
            triggerset_filtered.append(trigger)
    return dataset_filtered, triggerset_filtered

#-----------------------------------------------------   

def calc_meta_dict():
    meta_dict = {
                "theta [°]": Rotation.Instance().get_position()[1],
                "phi [°]": Rotation.Instance().get_position()[0],
                "occupancy [%]": measure_occ(),
                "gain": measure_gain(),
                "HV [V]": HV_supply.Instance().getHVMon(),
                "Powermeter": Powermeter.Instance().get_power(),
                "Laser temp [°C]": Laser.Instance().get_temp(),
                "Laser tune [%]": Laser.Instance().get_tune_value()/10,
                "Laser freq [Hz]": Laser.Instance().get_freq(),
                }
    return meta_dict

#-----------------------------------------------------

def calculate_occ(dataset, threshold_signal=-4) -> float:

        number = len(dataset)
        minval = np.zeros(number)
        for i in range(number):
            minval[i] = np.min(dataset[i].T[1])
        occ = np.sum(np.where(minval < threshold_signal, 1, 0))/number  # Occupancy for threshold
        return occ

def tune_occ(occ_min, occ_max, laser_tune_start=None, laser_tune_step=1, delay=2, threshold_pico=2000,
             threshold_signal=-4, iterations=10000):

    if not laser_tune_start:
        laser_tune_start = Laser.Instance().get_tune_value()

    Rotation.Instance().go_home()
    if not max(Rotation.Instance().get_position()) <= 1: #Rotation stage in home position
        logging.getLogger("OMCU").error("Error while tuning occupancy. Rotation stage is unable to go to home position")
        raise RuntimeError
    if not Laser.Instance().get_ld() == 1: #laser on
        try:
            Laser.Instance().on_pulsed()
        except:
            logging.getLogger("OMCU").error("Error while tuning occupancy. Laser cannot be turned on")
            raise RuntimeError
    if not HV_supply.Instance().is_on(): #HV on
        try:
            HV_supply.Instance().on()
        except:
            logging.getLogger("OMCU").error("Error while tuning occupancy. HV supply cannot be turned on")
            raise RuntimeError

    assert occ_min <= occ_max #numbers match

    logging.getLogger("OMCU").info(f"tuning occupancy to value between {occ_min} and {occ_max}")

    laser_tune = laser_tune_start

    while True:
        Laser.Instance().set_tune_value(laser_tune)
        time.sleep(delay)
        dataset, _ = Picoscope.Instance().block_measurement(trgchannel=0, sgnlchannel=2, direction=2,
                                                            threshold=threshold_pico, number=iterations)
        occ = calculate_occ(dataset=dataset, threshold_signal=threshold_signal)
        if occ < occ_min:
            laser_tune -= laser_tune_step
            logging.getLogger("OMCU").info(f"measured occupancy to be {occ}, decreasing tune to {laser_tune}")
        elif occ > occ_max:
            laser_tune += laser_tune_step
            logging.getLogger("OMCU").info(f"measured occupancy to be {occ}, increasing tune to {laser_tune}")
        else:
            logging.getLogger("OMCU").info(f"measured occupancy to be {occ}, leaving laser tuning")
            break
    return occ, laser_tune

def measure_occ(threshold_pico=2000, threshold_signal=-4, iterations=10000) -> float:

    if not Laser.Instance().get_ld() == 1: #laser on
        try:
            Laser.Instance().on_pulsed()
        except:
            logging.getLogger("OMCU").error("Error while tuning occupancy. Laser cannot be turned on")
            raise RuntimeError
    if not HV_supply.Instance().is_on(): #HV on
        try:
            HV_supply.Instance().on()
        except:
            logging.getLogger("OMCU").error("Error while tuning occupancy. HV supply cannot be turned on")
            raise RuntimeError

    dataset, _ = Picoscope.Instance().block_measurement(trgchannel=0, sgnlchannel=2, direction=2,
                                                        threshold=threshold_pico, number=iterations)
    occ = calculate_occ(dataset=dataset, threshold_signal=threshold_signal)
    logging.getLogger("OMCU").info(f"measured occupancy to be {occ}")
    return occ

#-----------------------------------------------------

def calculate_gain(dataset, threshold_signal=-4) -> float:
    gains = []
    for data in dataset:
        if np.min(data[:, 1]) < threshold_signal:
            wf = Waveform("_", "_", "_", data[:, 0], data[:, 1], np.min(data[:, 1]))
            gains.append(wf.calculate_gain())
    return sum(gains)/len(gains)

def tune_gain(g_min, g_max, V_start=None, V_step=10, threshold_pico=2000, delay=2, threshold_signal=-4,
              iterations=10000):

    if not V_start:
        V_start = HV_supply.Instance().getHVSet()

    Rotation.Instance().go_home()
    if not max(Rotation.Instance().get_position()) <= 1: #Rotation stage in home position
        logging.getLogger("OMCU").error("Error while tuning gain. Rotation stage is unable to go to home position")
        raise RuntimeError
    if not Laser.Instance().get_ld() == 1: #laser on
        try:
            Laser.Instance().on_pulsed()
        except:
            logging.getLogger("OMCU").error("Error while tuning occupancy. Laser cannot be turned on")
            raise RuntimeError
    if not HV_supply.Instance().is_on(): #HV on
        try:
            HV_supply.Instance().on()
        except:
            logging.getLogger("OMCU").error("Error while tuning occupancy. HV supply cannot be turned on")
            raise RuntimeError
    
    assert g_min <= g_max  # numbers match

    logging.getLogger("OMCU").info(f"tuning gain to value between {g_min} and {g_max}")

    V = V_start

    while True:

        # Sets voltage, unblocks when measured voltage in tolerance around set voltage
        HV_supply.Instance().SetVoltage(V, tolerance=2, max_iter=60, wait_time=1)

        time.sleep(delay)
        dataset, _ = Picoscope.Instance().block_measurement(trgchannel=0, sgnlchannel=2, direction=2,
                                                             threshold=threshold_pico, number=iterations)
        
        gain = calculate_gain(dataset, threshold_signal=threshold_signal)
        if gain < g_min:
            V += V_step
            logging.getLogger("OMCU").info(f"measured gain to be {gain}, moving HV up to {V} Volt")
        elif gain > g_max:
            V -= V_step
            logging.getLogger("OMCU").info(f"measured gain to be {gain}, moving HV down to {V} Volt")
        else:
            logging.getLogger("OMCU").info(f"measured gain to be {gain}, leaving gain tuning")
            break

    return gain, V

def measure_gain(threshold_pico=2000, threshold_signal=-4, iterations=10000) -> float:

    if not Laser.Instance().get_ld() == 1: #laser on
        try:
            Laser.Instance().on_pulsed()
        except:
            logging.getLogger("OMCU").error("Error while tuning occupancy. Laser cannot be turned on")
            raise RuntimeError
    if not HV_supply.Instance().is_on(): #HV on
        try:
            HV_supply.Instance().on()
        except:
            logging.getLogger("OMCU").error("Error while tuning occupancy. HV supply cannot be turned on")
            raise RuntimeError 

    dataset, _ = Picoscope.Instance().block_measurement(trgchannel=0, sgnlchannel=2, direction=2,
                                                        threshold=threshold_pico, number=iterations)
    
    gain = calculate_gain(dataset, threshold_signal=threshold_signal)
    logging.getLogger("OMCU").info(f"measured gain to be {gain}")
    return gain

#-------------------------------------------------------------------------------------
