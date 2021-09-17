#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

import numpy as np

class Occupancy:
    def __init__(self):
        pass

    def occ(self, file='./data/20210823-112905-10000-sgnl.npy', threshold=-4):

        data = np.load(file)
        number = len(data)
        minval=np.zeros(number)
        for i in range(number):
            minval[i]=np.min(data[i].T[1])

        occ=np.sum(np.where(minval<threshold, 1, 0))  # Occupancy for threshold -4mV

        return occ