import sys
import os
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
omcu_supply_voltage_err = []  # gain err
omcu_dark_count         = []  # dark count at 5e6 gain
omcu_dark_count_err     = []  # dark count std
omcu_peak_to_valley     = []  # peak to valley at 5e6 gain
omcu_peak_to_valley_err = []  # ptv std
omcu_tts                = []  # tts at 5e6 gain
omcu_tts_err            = []  # tts err

pmt_directories = [x for x in os.listdir(omcu_data_path) if x.startswith("KM")]
pmt_directories = [x for x in pmt_directories if not "gelpad" in x and not "barnacle" in x and not "spring" in x]

# loop through pmts
for pmt_dir in pmt_directories:

    print(f"checking {pmt_dir}")
    pmt_dir_abs = os.path.join(omcu_data_path, pmt_dir)

    # create datahandler for fHV
    data_handler = DataHandler("data_frontal_HV.hdf5", pmt_dir_abs)
    data_handler.load_metadicts()
    for measurement in data_handler.measurements:
        if "Dy10" in measurement.metadict and measurement.metadict["Dy10 [V]"] == -1: measurement.metadict["Dy10 [V]"] = measurement.metadict["Dy10"]
        if "sgnl threshold" in measurement.metadict and measurement.metadict["sgnl threshold [mV]"] == -1: measurement.metadict["sgnl threshold [mV]"] = measurement.metadict["sgnl threshold"]
    print("creating data handler done...")
    # obtain gain-calibration curve and find Dy10 for 5e6 gain
    gain = []
    HV   = []
    for measurement in data_handler.measurements:
        measurement.read_from_file()
        if "Dy10" in measurement.metadict and measurement.metadict["Dy10 [V]"] == -1: measurement.metadict["Dy10 [V]"] = measurement.metadict["Dy10"]
        if "sgnl threshold" in measurement.metadict and measurement.metadict["sgnl threshold [mV]"] == -1: measurement.metadict["sgnl threshold [mV]"] = measurement.metadict["sgnl threshold"]
        if measurement.metadict["Dy10 [V]"] < 75: continue
        gain.append(measurement.calculate_gain(measurement.metadict["sgnl threshold [mV]"])[0])
        HV.append(measurement.metadict["Dy10 [V]"])
        measurement.clear()
    gain_fit = np.polyfit(gain, HV, deg=5)
    Dy10_5e6 = np.polyval(gain_fit, 5e6)
    if Dy10_5e6 < 75 or Dy10_5e6 > 95:
        print(f"WARNING: Dy10 of {Dy10_5e6} at 5e6 gain in pmt {pmt_dir}")
        continue
    omcu_supply_voltage.append(Dy10_5e6)
    omcu_supply_voltage_err.append(6) # systematic err
    print(f"HV done... {Dy10_5e6} V")

    # get TTS
    TTS = []
    for measurement in data_handler.measurements:
        if abs(measurement.metadict["Dy10 [V]"] - Dy10_5e6) < HV_tolerance:
            measurement.read_from_file()
            if "Dy10" in measurement.metadict and measurement.metadict["Dy10 [V]"] == -1: measurement.metadict["Dy10 [V]"] = measurement.metadict["Dy10"]
            if "sgnl threshold" in measurement.metadict and measurement.metadict["sgnl threshold [mV]"] == -1: measurement.metadict["sgnl threshold [mV]"] = measurement.metadict["sgnl threshold"]
            TTS.append(measurement.calculate_transit_time(measurement.metadict["sgnl threshold [mV]"])[1])
            measurement.clear()
    omcu_tts.append(np.average(TTS))
    omcu_tts_err.append(1) # systematic
    print(f"TTS done... {np.average(TTS)} ns")

    # get peak to valley
    ptv = []
    ptv_std = []
    for measurement in data_handler.measurements:
        if abs(measurement.metadict["Dy10 [V]"] - Dy10_5e6) < 1:
            measurement.read_from_file()
            if "Dy10" in measurement.metadict and measurement.metadict["Dy10 [V]"] == -1: measurement.metadict["Dy10 [V]"] = measurement.metadict["Dy10"]
            if "sgnl threshold" in measurement.metadict and measurement.metadict["sgnl threshold [mV]"] == -1: measurement.metadict["sgnl threshold [mV]"] = measurement.metadict["sgnl threshold"]
            p_1, p_2 = measurement.calculate_ptv(measurement.metadict["sgnl threshold [mV]"])
            measurement.clear()
            ptv.append(p_1)
            ptv_std.append(p_2)
    omcu_peak_to_valley.append(np.average(ptv))
    omcu_peak_to_valley_err.append(np.average(ptv_std))
    print(f"PTV done... {np.average(ptv)}")

    # get DCS data_handler
    data_handler = DataHandler("data_dark_count.hdf5", pmt_dir_abs)
    data_handler.load_metadicts()
    print("creating data handler for  done")

    # get dark count for Dy10 at 5e6 gain
    dark_counts = []
    for measurement in data_handler.measurements:
        if "Dy10" in measurement.metadict and measurement.metadict["Dy10 [V]"] == -1: measurement.metadict["Dy10 [V]"] = measurement.metadict["Dy10"]
        if "sgnl threshold" in measurement.metadict and measurement.metadict["sgnl threshold [mV]"] == -1: measurement.metadict["sgnl threshold [mV]"] = measurement.metadict["sgnl threshold"]
        if abs(measurement.metadict["Dy10 [V]"] - Dy10_5e6) < HV_tolerance:
            dark_counts.append(measurement.metadict["dark rate [Hz]"])
    omcu_dark_count.append(np.average(dark_counts))
    omcu_dark_count_err.append(np.std(dark_counts))
    print(f"DC done... {np.average(dark_counts)} Hz")
    
    # append pmt name
    omcu_pmt_names.append(pmt_dir.split("_")[0])
    print()

# convert to numpy
omcu_pmt_names          = np.array(omcu_pmt_names)
omcu_supply_voltage     = np.array(omcu_supply_voltage)
omcu_supply_voltage_err = np.array(omcu_supply_voltage_err)
omcu_peak_to_valley     = np.array(omcu_peak_to_valley)
omcu_peak_to_valley_err = np.array(omcu_peak_to_valley_err)
omcu_tts                = np.array(omcu_tts)
omcu_tts_err            = np.array(omcu_tts_err)
omcu_dark_count         = np.zeros(len(omcu_pmt_names)) # np.array(omcu_dark_count)
omcu_dark_count_err     = np.zeros(len(omcu_pmt_names)) # np.array(omcu_dark_count_err)

# account for Dy10*12 = total HV
omcu_supply_voltage = omcu_supply_voltage * 12

# init relative arrays
omcu_supply_voltage_relative = np.zeros(len(omcu_pmt_names))
omcu_dark_count_relative     = np.zeros(len(omcu_pmt_names))
omcu_peak_to_valley_relative = np.zeros(len(omcu_pmt_names))
omcu_tts_relative            = np.zeros(len(omcu_pmt_names))

# Iterate over the hamamatsu data
for index, row in hamamatsu_data.iterrows():
    serial_no = row['Serial No.']
    pmt_index = np.where(omcu_pmt_names == serial_no)[0]

    # fill relative arrays
    omcu_supply_voltage_relative[pmt_index] = omcu_supply_voltage[pmt_index] - row["Supply Voltage"]
    omcu_dark_count_relative[pmt_index]     = omcu_dark_count[pmt_index]     - row["Dark Count"]
    omcu_peak_to_valley_relative[pmt_index] = omcu_peak_to_valley[pmt_index] - row["Peak to Valley Ratio"]
    omcu_tts_relative[pmt_index]            = omcu_tts[pmt_index]            - row["TTS"]

fig, axs = plt.subplots(2, 2, figsize=(14, 9))

axs[0, 0].errorbar(omcu_pmt_names, omcu_supply_voltage_relative, yerr=omcu_supply_voltage_err, fmt='o', capsize=5, label="OMCU data")
axs[0, 0].set_xlabel('PMT Serial No.')
axs[0, 0].set_ylabel('measured Supply Voltage\nrelative to Hamamatsu Data')

axs[0, 1].errorbar(omcu_pmt_names, omcu_dark_count_relative, yerr=omcu_dark_count_err, fmt='o', capsize=5, label="OMCU data")
axs[0, 1].set_xlabel('PMT Serial No.')
axs[0, 1].set_ylabel('measured Dark Count\nrelative to Hamamatsu Data')

axs[1, 0].errorbar(omcu_pmt_names, omcu_peak_to_valley_relative, yerr=omcu_peak_to_valley_err, fmt='o', capsize=5, label="OMCU data")
axs[1, 0].set_xlabel('PMT Serial No.')
axs[1, 0].set_ylabel('measured Peak to Valley Ratio\nrelative to Hamamatsu Data')

axs[1, 1].errorbar(omcu_pmt_names, omcu_tts_relative, yerr=omcu_tts_err, fmt='o', capsize=5, label="OMCU data")
axs[1, 1].set_xlabel('PMT Serial No.')
axs[1, 1].set_ylabel('measured TTS\nrelative to Hamamatsu Data')

axs[0, 0].axhline(y=0, linestyle="solid", label="Hamamatsu Baseline", c="tab:red")
axs[1, 0].axhline(y=0, linestyle="solid", label="Hamamatsu Baseline", c="tab:red")
axs[0, 1].axhline(y=0, linestyle="solid", label="Hamamatsu Baseline", c="tab:red")
axs[1, 1].axhline(y=0, linestyle="solid", label="Hamamatsu Baseline", c="tab:red")

# Calculate the average of the data points for each dataset
avg_supply_voltage = np.nanmean(omcu_supply_voltage_relative)
avg_dark_count     = np.nanmean(omcu_dark_count_relative)
avg_peak_to_valley = np.nanmean(omcu_peak_to_valley_relative)
avg_tts            = np.nanmean(omcu_tts_relative)

# Draw horizontal lines at the averages and label them
axs[0, 0].axhline(y=avg_supply_voltage, color="purple", linestyle="dashed", label="average offset")
axs[0, 1].axhline(y=avg_dark_count, color="purple", linestyle="dashed", label="average offset")
axs[1, 0].axhline(y=avg_peak_to_valley, color="purple", linestyle="dashed", label="average offset")
axs[1, 1].axhline(y=avg_tts, color="purple", linestyle="dashed", label="average offset")

axs[0, 0].set_xticklabels(omcu_pmt_names, rotation=60)
axs[0, 1].set_xticklabels(omcu_pmt_names, rotation=60)
axs[1, 0].set_xticklabels(omcu_pmt_names, rotation=60)
axs[1, 1].set_xticklabels(omcu_pmt_names, rotation=60)

# Calculate the maximum absolute values of the arrays
max_abs_supply_voltage = np.nanmax(np.abs(omcu_supply_voltage_relative) + np.abs(omcu_supply_voltage_err))
max_abs_dark_count = np.nanmax(np.abs(omcu_dark_count_relative) + np.abs(omcu_dark_count_err))
max_abs_peak_to_valley = np.nanmax(np.abs(omcu_peak_to_valley_relative) + np.abs(omcu_peak_to_valley_err))
max_abs_tts = np.nanmax(np.abs(omcu_tts_relative) + np.abs(omcu_tts_err))

# Set the y-axis limits using the maximum absolute values with some padding (e.g., 20%)
axs[0, 0].set_ylim(-max_abs_supply_voltage * 1.2, max_abs_supply_voltage * 1.2)
axs[0, 1].set_ylim(-max_abs_dark_count * 1.2, max_abs_dark_count * 1.2)
axs[1, 0].set_ylim(-max_abs_peak_to_valley * 1.2, max_abs_peak_to_valley * 1.2)
axs[1, 1].set_ylim(-max_abs_tts * 1.2, max_abs_tts * 1.2)

# Draw lines from the data points 0.5cm to the left and straight down to y=0 line
for ax in axs.flatten():
    for idx, (x, y) in enumerate(zip(omcu_pmt_names, ax.get_children()[0].get_ydata())):
        x_pos = idx  # Use the index directly as the x-position
        ax.plot([x_pos - 0.4, x_pos - 0.4], [y, 0], color='gray', linestyle='--', linewidth=0.7)
        ax.plot([x_pos, x_pos - 0.4], [y, y], color='gray', linestyle='--', linewidth=0.7)

axs[0, 0].legend()
axs[1, 0].legend()
axs[0, 1].legend()
axs[1, 1].legend()

plt.subplots_adjust(hspace=0.5)

plt.savefig("/home/canada/munich_pmt_calibration_system/data/R14374/hamamatsu_data_comparison.png", dpi=300)
