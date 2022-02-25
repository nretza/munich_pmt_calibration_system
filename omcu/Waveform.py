#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

import numpy as np
from numpy import trapz
import scipy.constants as const

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

    def mean(self):
        self.mean = np.mean(self.y)

    def subtractBaseline(self, value):
        self.y -= value
