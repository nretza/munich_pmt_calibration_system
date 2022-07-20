import time
import logging
import numpy as np

from omcu.Waveform import Waveform
from omcu.devices.Laser import Laser
from omcu.devices.Picoscope import Picoscope
from omcu.devices.HV_supply import HV_supply
from omcu.devices.Rotation import Rotation

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
        logging_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    log_handler = logging.FileHandler(filename=logging_file)
    log_handler.setLevel(logging_level)
    log_handler.setFormatter(logging_formatter)

    #settings for root logger. all loggers inherit from root
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().addHandler(log_handler)

    return log_handler

#-----------------------------------------------------

def calculate_occ(dataset, threshold_signal=-4) -> float:

        number = len(dataset)
        minval = np.zeros(number)
        for i in range(number):
            minval[i] = np.min(dataset[i].T[1])
        occ = np.sum(np.where(minval < threshold_signal, 1, 0))/number  # Occupancy for threshold
        return occ

def tune_occ(occ_min, occ_max, laser_tune_start=None, laser_tune_step=1, delay=0.1, threshold_pico=2000,
             threshold_signal=-4, iterations=10000) -> List[float, float]:

    if not laser_tune_start:
        laser_tune_start = Laser.Instance().get_tune_value()

    Rotation.Instance().go_home()

    assert max(Rotation.Instance().get_position()) <= 1 #Rotation stage in home position
    assert Laser.Instance().get_ld() == 1 #laser on
    assert HV_supply.Instance().is_on() #HV on
    assert occ_min <= occ_max #numbers match

    laser_tune = laser_tune_start

    while True:
        Laser.Instance().set_tune_value(laser_tune)
        time.sleep(delay)
        dataset, _ = Picoscope.Instance().block_measurement(trgchannel=0, sgnlchannel=2, direction=2,
                                                            threshold=threshold_pico, number=iterations)
        occ = calculate_occ(dataset=dataset, threshold_signal=threshold_signal)
        if occ < occ_min:
            laser_tune -= laser_tune_step
        elif occ > occ_max:
            laser_tune += laser_tune_step
        else:
            break
    return occ, laser_tune

def measure_occ(threshold_pico=2000, threshold_signal=-4, iterations=10000) -> float:

    assert Laser.Instance().get_ld() == 1 # laser on
    assert HV_supply.Instance().is_on() #HV on

    dataset, _ = Picoscope.Instance().block_measurement(trgchannel=0, sgnlchannel=2, direction=2,
                                                        threshold=threshold_pico, number=iterations)
    return calculate_occ(dataset=dataset, threshold_signal=threshold_signal)

#-----------------------------------------------------

def calculate_gain(dataset, threshold_signal=-4) -> float:
    gains = []
    for data in dataset:
        if np.min(data[:, 1]) < threshold_signal:
            wf = Waveform("_", "_", "_", data[:, 0], data[:, 1], np.min(data[:, 1]))
            gains.append(wf.calculate_gain())
    return sum(gains)/len(gains)

def tune_gain(g_min, g_max, V_start=None, V_step=10, threshold_pico=2000, threshold_signal=-4,
              iterations=10000) -> List[float, float]:

    if not V_start:
        V_start = HV_supply.Instance().getHVSet()

    Rotation.Instance().go_home()

    assert tune_occ(0, 0.1) < 0.1 # occupancy tuned
    assert max(Rotation.Instance().get_position()) <= 1  # Rotation stage in home position
    assert Laser.Instance().get_ld() == 1  # laser on
    assert HV_supply.Instance().is_on() #HV on
    assert g_min <= g_max  # numbers match

    V = V_start

    while True:

        # Sets voltage, unblocks when measured voltage in tolerance around set voltage
        HV_supply.Instance().SetVoltage(V, tolerance=2, max_iter=60, wait_time=1)

        dataset, _ = Picoscope.Instance().block_measurement(trgchannel=0, sgnlchannel=2, direction=2,
                                                             threshold=threshold_pico, number=iterations)
        
        gain = calculate_gain(dataset, threshold=threshold_signal)
        if gain < g_min:
            V += V_step
        elif gain > g_max:
            V -= V_step
        else:
            break

    return gain, V

def measure_gain(threshold_pico=2000, threshold_signal=-4, iterations=10000) -> float:

    assert tune_occ(0, 0.1) < 0.1 # occ tuned
    assert Laser.Instance().get_ld() == 1  # laser on
    assert HV_supply.Instance().is_on() #HV on

    dataset, _ = Picoscope.Instance().block_measurement(trgchannel=0, sgnlchannel=2, direction=2,
                                                        threshold=threshold_pico, number=iterations)
    
    return calculate_gain(dataset, threshold_signal=threshold_signal)
