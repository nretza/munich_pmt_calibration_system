import sys
import os
import h5py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

sys.path.append("../../omcu")

from utils.DataHandler import DataHandler


########################################################
#                                                      #
#        Hello, i am a preliminary script              #
#                                                      #
########################################################

hamamatsu_data_file = "hamamatsu_pmt_values.csv"
omcu_data_path      = "/home/canada/munich_pmt_calibration_system/data/R14374"

hamamatsu_data = pd.read_csv(hamamatsu_data_file)

HV_tolerance = 1

omcu_pmt_names      = []
omcu_supply_voltage = []  # supply voltage at 5e6 gain
omcu_dark_count     = []  # dark count at 5e6 gain
omcu_peak_to_valley = []  # peak to valley at 5e6 gain
omcu_tts            = []  # tts at 5e6 gain

pmt_directories = [x for x in os.listdir(omcu_data_path) if x.startswith("KM")]
pmt_directories = [x for x in pmt_directories if not "gelpad" in x and not "barnacle" in x and not "spring" in x]

for pmt_dir in pmt_directories:

    print(f"checking {pmt_dir}")
    pmt_dir_abs = os.path.join(omcu_data_path, pmt_dir)

    # obtain gain-callibration curve and find Dy10 for 5e6 gain
    gain = []
    HV   = []
    data_handler = DataHandler("data_frontal_HV.hdf5", pmt_dir_abs)
    data_handler.load_metadicts()
    for measurement in data_handler.meassurements:
        gain.append(measurement.metadict["gain"])
        HV.append(measurement.metadict["Dy10 [V]"])
    gain_fit = np.polyfit(gain, HV, deg=5)
    HV_5e6 = round(np.polyval(gain_fit, 5e6))
    if HV_5e6 < 80 or HV_5e6 > 90:
        print(f"WARNING: Dy10 of {HV_5e6} at 5e6 gain in pmt {pmt_dir}")
        continue
    omcu_supply_voltage.append(HV_5e6)

    # get TTS
    TTS = []
    for measurement in data_handler.meassurements:
        if round(measurement.metadict["Dy10 [V]"]) == HV_5e6:
            if measurement.metadict["transit time spread [ns]"] != -1:
                TTS.append(measurement.metadict["transit time spread [ns]"])
            else:
                measurement.read_from_file()
                TTS.append(measurement.calculate_transit_time(measurement.metadict["sgnl threshold [mV]"])[1])
    omcu_tts.append(np.average(TTS))

    # get peak to valley
    ptv = []
    for measurement in data_handler.meassurements:
        if round(measurement.metadict["Dy10 [V]"]) == HV_5e6:
            if measurement.metadict["peak to valley ratio"] != -1:
                ptv.append(measurement.metadict["peak to valley ratio"])
            else:
                measurement.read_from_file()
                ptv.append(measurement.calculate_ptv(measurement.metadict["sgnl threshold [mV]"])[0])
    omcu_peak_to_valley.append(np.average(ptv))

    # get dark count for Dy10 at 5e6 gain
#    data_handler = DataHandler("data_dark_count.hdf5", pmt_dir_abs)
#    DataHandler.load_metadicts()
#    dark_counts = []
#    for measurement in data_handler.meassurements:
#        if round(measurement.metadict["Dy10 [V]"]) == HV_5e6:
#            dark_counts.append(measurement.metadict["dark rate [Hz]"])
#    omcu_dark_count.append(np.average(dark_counts))

    omcu_pmt_names.append(pmt_dir.split("_")[0])


# Plot 1: Supply Voltage
plt.scatter(omcu_pmt_names, omcu_supply_voltage)
plt.title('Supply Voltage vs PMT Names')
plt.xlabel('PMT Names')
plt.ylabel('Supply Voltage')
plt.show()

# Plot 2: Dark Count
#plt.scatter(omcu_pmt_names, omcu_dark_count)
#plt.title('Dark Count vs PMT Names')
#plt.xlabel('PMT Names')
#plt.ylabel('Dark Count')
#plt.show()

# Plot 3: Peak to Valley
plt.scatter(omcu_pmt_names, omcu_peak_to_valley)
plt.title('Peak to Valley vs PMT Names')
plt.xlabel('PMT Names')
plt.ylabel('Peak to Valley')
plt.show()

# Plot 4: TTS
plt.scatter(omcu_pmt_names, omcu_tts)
plt.title('TTS vs PMT Names')
plt.xlabel('PMT Names')
plt.ylabel('TTS')
plt.show()