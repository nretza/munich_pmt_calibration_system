#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

import matplotlib.pyplot as plt
import numpy as np
from numpy import trapz
import scipy.constants as const

class Waveform:
    def __init__(self, theta, phi, y, x):
        self.theta = theta
        self.phi = phi
        self.y = y
        self.x = x

    def __str__(self):
        print(self.theta,self.phi)

    def calculate_gain(self):
        self.area = trapz(abs(self.y*1e-3), abs(self.x*1e-9))
        self.gain = self.area/const.e

    def plot_wf(self):
            pass
