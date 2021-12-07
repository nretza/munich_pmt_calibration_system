#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

import matplotlib.pyplot as plt
import numpy as np
from numpy import trapz
import scipy.constants as const
from scipy.integrate import quad

class Waveform:
    def __init__(self, theta, phi, HV, x, y, minval):
        self.theta = theta
        self.phi = phi
        self.HV = HV
        self.x = x
        self.y = y
        self.min = minval

    def __str__(self):
        print(self.theta,self.phi)

    def calculate_gain(self):
        self.mask = (self.x > 200) & (self.x < 220)  # maybe more dynamic
        self.area = trapz(abs(self.y[self.mask]*1e-3), abs(self.x[self.mask]*1e-9))
        self.charge = self.area/50
        self.gain = self.charge/const.e

    def mean(self):
        self.mean = np.mean(self.y)
