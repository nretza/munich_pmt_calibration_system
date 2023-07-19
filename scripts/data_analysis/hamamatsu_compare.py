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

omcu_pmt_names          = []
omcu_supply_voltage     = []  # supply voltage at 5e6 gain
omcu_dark_count         = []  # dark count at 5e6 gain
omcu_dark_count_err     = []  # dark count std
omcu_peak_to_valley     = []  # peak to valley at 5e6 gain
omcu_peak_to_valley_err = []  # ptv std
omcu_tts                = []  # tts at 5e6 gain

pmt_directories = [x for x in os.listdir(omcu_data_path) if x.startswith("KM")]
pmt_directories = [x for x in pmt_directories if not "gelpad" in x and not "barnacle" in x and not "spring" in x]

for pmt_dir in pmt_directories:

    print(f"checking {pmt_dir}")
    pmt_dir_abs = os.path.join(omcu_data_path, pmt_dir)

    # obtain gain-calibration curve and find Dy10 for 5e6 gain
    gain = []
    HV   = []
    data_handler = DataHandler("data_frontal_HV.hdf5", pmt_dir_abs)
    data_handler.load_metadicts()
    for measurement in data_handler.meassurements:
        gain.append(measurement.metadict["gain"])
        HV.append(measurement.metadict["Dy10 [V]"])
    gain_fit = np.polyfit(gain, HV, deg=5)
    Dy10_5e6 = np.polyval(gain_fit, 5e6)
    if Dy10_5e6 < 80 or Dy10_5e6 > 90:
        print(f"WARNING: Dy10 of {Dy10_5e6} at 5e6 gain in pmt {pmt_dir}")
        continue
    omcu_supply_voltage.append(Dy10_5e6)

    # get TTS
    TTS = []
    for measurement in data_handler.meassurements:
        if abs(measurement.metadict["Dy10 [V]"] - Dy10_5e6) < HV_tolerance:
            if measurement.metadict["transit time spread [ns]"] != -1:
                TTS.append(measurement.metadict["transit time spread [ns]"])
            else:
                measurement.read_from_file()
                TTS.append(measurement.calculate_transit_time(measurement.metadict["sgnl threshold [mV]"])[1])
    omcu_tts.append(np.average(TTS))

    # get peak to valley
    ptv = []
    ptv_std = []
    for measurement in data_handler.meassurements:
        if abs(measurement.metadict["Dy10 [V]"] - Dy10_5e6) < 1:
            if measurement.metadict["peak to valley ratio"] != -1:
                ptv.append(measurement.metadict["peak to valley ratio"])
            else:
                measurement.read_from_file()
                p_1, p_2 = measurement.calculate_ptv(measurement.metadict["sgnl threshold [mV]"])
                ptv.append(p_1)
                ptv.append(p_2)
    omcu_peak_to_valley.append(np.average(ptv))
    omcu_peak_to_valley_err.append(np.average(ptv))

    # get dark count for Dy10 at 5e6 gain
    data_handler = DataHandler("data_dark_count.hdf5", pmt_dir_abs)
    DataHandler.load_metadicts()
    dark_counts = []
    for measurement in data_handler.meassurements:
        if abs(measurement.metadict["Dy10 [V]"] - Dy10_5e6) < HV_tolerance:
            dark_counts.append(measurement.metadict["dark rate [Hz]"])
    omcu_dark_count.append(np.average(dark_counts))
    omcu_dark_count_err.append(np.std(dark_counts))

    # append pmt name
    omcu_pmt_names.append(pmt_dir.split("_")[0])

omcu_pmt_names          = np.array(omcu_pmt_names)
omcu_supply_voltage     = np.array(omcu_supply_voltage)
omcu_dark_count         = np.array(omcu_dark_count)
omcu_dark_count_err     = np.array(omcu_dark_count_err)
omcu_peak_to_valley     = np.array(omcu_peak_to_valley)
omcu_peak_to_valley_err = np.array(omcu_peak_to_valley_err)
omcu_tts                = np.array(omcu_tts)

# account for Dy10*12 = total HV
omcu_supply_voltage = omcu_supply_voltage * 12

omcu_supply_voltage_relative = np.zeros(len(omcu_pmt_names))
omcu_dark_count_relative     = np.zeros(len(omcu_pmt_names))
omcu_peak_to_valley_relative = np.zeros(len(omcu_pmt_names))
omcu_tts_relative            = np.zeros(len(omcu_pmt_names))

# Iterate over the hamamatsu data
for index, row in hamamatsu_data.iterrows():
    serial_no = row['Serial No.']
    pmt_index = np.where(omcu_pmt_names == serial_no)[0]

    omcu_supply_voltage_relative[pmt_index] = omcu_supply_voltage[pmt_index] - row["Supply Voltage"]
    omcu_dark_count_relative[pmt_index]     = omcu_dark_count[pmt_index]     - row["Dark Count"]
    omcu_peak_to_valley_relative[pmt_index] = omcu_peak_to_valley[pmt_index] - row["Peak to Valley Ratio"]
    omcu_tts_relative[pmt_index]            = omcu_tts[pmt_index]            - row["TTS"]










# Create a figure
fig, axs = plt.subplots(2, 2)

axs[0, 0].errorbar(omcu_pmt_names, omcu_supply_voltage_relative, yerr=6, fmt='o')
axs[0, 0].set_title('Supply Voltage vs PMT Names')
axs[0, 0].set_xlabel('PMT Names')
axs[0, 0].set_ylabel('Supply Voltage')

axs[0, 1].errorbar(omcu_pmt_names, omcu_dark_count, yerr=omcu_dark_count_err, fmt='o')
axs[0, 1].set_title('Dark Count vs PMT Names')
axs[0, 1].set_xlabel('PMT Names')
axs[0, 1].set_ylabel('Dark Count')

axs[1, 0].errorbar(omcu_pmt_names, omcu_peak_to_valley_relative, yerr=omcu_peak_to_valley_err, fmt='o')
axs[1, 0].set_title('Peak to Valley vs PMT Names')
axs[1, 0].set_xlabel('PMT Names')
axs[1, 0].set_ylabel('Peak to Valley')

axs[1, 1].errorbar(omcu_pmt_names, omcu_tts_relative, yerr=1, fmt='o')
axs[1, 1].set_title('TTS vs PMT Names')
axs[1, 1].set_xlabel('PMT Names')
axs[1, 1].set_ylabel('TTS')

axs[0, 0].axhline(y=0, color="gray", linestyle="--", label="Hamamatsu Baseline")
axs[1, 0].axhline(y=0, color="gray", linestyle="--", label="Hamamatsu Baseline")
axs[0, 1].axhline(y=0, color="gray", linestyle="--", label="Hamamatsu Baseline")
axs[1, 1].axhline(y=0, color="gray", linestyle="--", label="Hamamatsu Baseline")

axs[0, 0].set_xticklabels(omcu_pmt_names, rotation=90)
axs[0, 1].set_xticklabels(omcu_pmt_names, rotation=90)
axs[1, 0].set_xticklabels(omcu_pmt_names, rotation=90)
axs[1, 1].set_xticklabels(omcu_pmt_names, rotation=90)