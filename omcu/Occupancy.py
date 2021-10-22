#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>

import numpy as np

class Occupancy:
    def __init__(self):
        pass

    def occ(self, filename='data/20211022-140412-1.1/20211022-140412-6-4-10.npy', threshold=-0.8):

        data = np.load(filename)
        filename_split1 = filename.split('/')  # ['data', '20211022-140412-1.1', '20211022-140412-6-4-10.npy']
        filename_split2 = filename_split1[-1].split('-')  # ['20211020', '140412', '6', '4', '10.npy']
        filename_split3 = filename_split2[-1].split('.')  # ['10', 'npy']
        number = int(filename_split3[0])  # 10 = number of waveforms per measurement
        number_theta = int(filename_split2[2])  # 6
        number_phi = int(filename_split2[3])  # 4
        total_number = int(number_theta * number_phi)  # 24 = number of measurements
        total_number_waveforms = number * total_number  # 240
        minval = np.zeros(total_number_waveforms)
        m=0
        for i in range(0, number_theta, 1):
            for j in range(0, number_phi, 1):
                for n in range(0, number, 1):
                    minval[m] = np.min(data[i][j][0][n].T[1])
                    m+=1

        occ = np.sum(np.where(minval<threshold, 1, 0))
        return occ

    def occ_old(self, file='./data/20210823-112905-10000-sgnl.npy', threshold=-4):

        data = np.load(file)
        number = len(data)
        minval=np.zeros(number)
        for i in range(number):
            minval[i]=np.min(data[i].T[1])

        occ = np.sum(np.where(minval<threshold, 1, 0))  # Occupancy for threshold
        return occ