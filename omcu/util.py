import time
import logging
import numpy as np
from numpy import trapz
import scipy.constants as const

from devices.Laser import Laser
from devices.Picoscope import Picoscope
from devices.PSU import PSU0 #TODO: REPLACE WITH HV
from devices.Rotation import Rotation

class Waveform:

    def __init__(self, theta, phi, HV, x, y, minval):
        self.theta = theta
        self.phi = phi
        self.HV = HV
        self.x = x
        self.y = y
        self.min = minval

    def __str__(self):
        print(self.theta, self.phi)

    def calculate_gain(self):
        indMin = np.argmin(self.y)
        if (self.x[indMin] < 190) or (self.x[indMin] > 220):
            self.mask = (self.x > 195) & (self.x < 220)
        else:
            xlim1 = self.x[indMin-10]
            xlim2 = self.x[indMin+15]
            self.mask = (self.x > xlim1) & (self.x < xlim2)
        self.area = trapz(self.y[self.mask]*1e-3, self.x[self.mask]*1e-9)
        self.charge = self.area/50
        self.gain = abs(self.charge)/const.e
        return self.gain

    def mean(self):
        self.mean = np.mean(self.y)
        return self.mean

    def subtractBaseline(self, value):
        self.y -= value
        return self.y

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

    logging.getLogger().addHandler(log_handler)

    return log_handler

#-----------------------------------------------------

def calculate_occ(dataset, threshold=-4) -> float:

        number = len(dataset)
        minval = np.zeros(number)
        for i in range(number):
            minval[i] = np.min(dataset[i].T[1])
        occ = np.sum(np.where(minval < threshold, 1, 0))/number  # Occupancy for threshold
        return occ

def tune_occ(occ_min, occ_max, laser_tune_start=710, laser_tune_step=1, delay=0.1, threshold_pico=2000,
             threshold_occ=-4, iterations=10000) -> Tuple(float, float):

    Rotation.Instance().go_home()

    assert max(Rotation.Instance().get_position()) <= 1 #Rotation stage in home position
    assert Laser.Instance().get_ld() == 1 #laser on
    assert PSU0.Instance().is_on() #PSU0 on  #TODO: REPLACE WITH HV
    assert occ_min <= occ_max #numbers match

    laser_tune = laser_tune_start

    while True:
        Laser.Instance().set_tune_value(laser_tune)
        time.sleep(delay)
        dataset, _ = Picoscope.Instance().block_measurement(trgchannel=0, sgnlchannel=2, direction=2,
                                                            threshold=threshold_pico, number=iterations)
        occ = calculate_occ(dataset=dataset, threshold=threshold_occ)
        if occ < occ_min:
            laser_tune -= laser_tune_step
        elif occ > occ_max:
            laser_tune += laser_tune_step
        else:
            break
    return occ, laser_tune

def measure_occ(threshold_pico=2000, threshold_occ=-4, iterations=10000) -> float:

    assert Laser.Instance().get_ld() == 1 # laser on
    assert PSU0.Instance().is_on() # PSU0 on  #TODO: REPLACE WITH HV

    dataset, _ = Picoscope.Instance().block_measurement(trgchannel=0, sgnlchannel=2, direction=2,
                                                        threshold=threshold_pico, number=iterations)
    return calculate_occ(dataset=dataset, threshold=threshold_occ)

#-----------------------------------------------------

def calculate_gain(dataset, threshold=-4) -> float:
    gains = []
    for data in dataset:
        if np.min(data[:, 1]) < threshold:
            wf = Waveform("_", "_", "_", data[:, 0], data[:, 1], np.min(data[:, 1]))
            gains.append(wf.calculate_gain())
    return sum(gains)/len(gains)

def tune_gain(g_min, g_max, Vctl_start=4, Vctl_step=0.2, delay=0.1, threshold_pico=2000, threshold_gain=-4,
              iterations=10000) -> Tuple(float, float):

    Rotation.Instance().go_home()

    assert tune_occ(0, 0.1) < 0.1 # occupancy tuned
    assert max(Rotation.Instance().get_position()) <= 1  # Rotation stage in home position
    assert Laser.Instance().get_ld() == 1  # laser on
    assert PSU0.Instance().is_on() #PSU0 on  #TODO: REPLACE WITH HV
    assert g_min <= g_max  # numbers match

    Vctl = Vctl_start

    while True:
        PSU0.Instance().settings(2,Vctl, current=0.1)  #TODO: REPLACE WITH HV
        time.sleep(delay)
        dataset, _ = Picoscope.Instance().block_measurement(trgchannel=0, sgnlchannel=2, direction=2,
                                                             threshold=threshold_pico, number=iterations)
        
        gain = calculate_gain(dataset, threshold=threshold_gain)
        if gain < g_min:
            Vctl += Vctl_step
        elif gain > g_max:
            Vctl -= Vctl_step
        else:
            break

    return gain, Vctl

def measure_gain(threshold_pico=2000, threshold_gain=-4, iterations=10000) -> float:

    assert tune_occ(0, 0.1) < 0.1 # occ tuned
    assert Laser.Instance().get_ld() == 1  # laser on
    assert PSU0.Instance().is_on() #PSU0 on TODO: REPLACE WITH HV  #TODO: REPLACE WITH HV

    dataset, _ = Picoscope.Instance().block_measurement(trgchannel=0, sgnlchannel=2, direction=2,
                                                        threshold=threshold_pico, number=iterations)
    
    return calculate_gain(dataset, threshold=threshold_gain)
