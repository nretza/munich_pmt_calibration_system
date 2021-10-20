#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

import numpy as np

class Occupancy:
    def __init__(self):
        pass

    def occ(self, filename='data/20211020-140122/20211020-140122-5-15-10.npy', threshold=-0.8):

        data = np.load(filename)
        filename_split1 = filename.split('/')  # ['data', '20211020-140122', '20211020-140122-5-15-10.npy']
        filename_split2 = filename_split1[-1].split('-')  # ['20211020', '140122', '5', '15', '10.npy']
        filename_split3 = filename_split2[-1].split('.')  # ['10', 'npy']
        number = int(filename_split3[0])  # 10 = number of waveforms per measurement
        delta_theta = int(filename_split2[2])  # 5
        delta_phi = int(filename_split2[3])  # 15
        total_number = int((90/delta_theta) * (360/delta_phi))  # 432 = number of measurements
        total_number_waveforms = number * total_number
        minval = np.zeros(total_number_waveforms)
        #for i in range():



    def occ_old(self, file='./data/20210823-112905-10000-sgnl.npy', threshold=-4):

        data = np.load(file)
        number = len(data)
        minval=np.zeros(number)
        for i in range(number):
            minval[i]=np.min(data[i].T[1])

        occ=np.sum(np.where(minval<threshold, 1, 0))  # Occupancy for threshold -4mV

        return occ