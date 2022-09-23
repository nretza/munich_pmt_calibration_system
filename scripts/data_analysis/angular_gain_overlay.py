import sys
sys.path.append("../omcu")

import os
import config
from data_analysis.data_handler import data_handler
import numpy as np
import matplotlib.pyplot as plt

pmt_path = "/home/canada/munich_pmt_calibration_system/data/R14374/high_angle"
pmt_gelpad_path = "/home/canada/munich_pmt_calibration_system/data/R14374/gelpad_no_interface_layer"
pmt_gelpad_overshoot_path = "/home/canada/munich_pmt_calibration_system/data/R14374/gelpad_no_interface_high_angle"

pmt_handler = data_handler(config.PCS_DATAFILE, pmt_path)
pmt_gelpad_handler = data_handler(config.PCS_DATAFILE, pmt_gelpad_path)
pmt_gelpad_overshoot_handler = data_handler(config.PCS_DATAFILE, pmt_gelpad_overshoot_path)
pmt_handler.load_metadicts()
pmt_gelpad_handler.load_metadicts()
pmt_gelpad_overshoot_handler.load_metadicts()

pmt_occ_list = np.array([])
pmt_occ_std_list = np.array([])
pmt_theta_list = np.array([])

pmt_gelpad_occ_list = np.array([])
pmt_gelpad_occ_std_list = np.array([])
pmt_gelpad_theta_list = np.array([])

#get thetas
for metadict in pmt_handler.metadicts:
    if round(metadict["theta"]) not in pmt_theta_list:
        pmt_theta_list = np.append(pmt_theta_list, round(metadict["theta"]))
pmt_theta_list.sort()
for metadict in pmt_gelpad_handler.metadicts:
    if round(metadict["theta"]) not in pmt_gelpad_theta_list:
        pmt_gelpad_theta_list = np.append(pmt_gelpad_theta_list, round(metadict["theta"]))
for metadict in pmt_gelpad_overshoot_handler.metadicts:
    if round(metadict["theta"]) not in pmt_gelpad_theta_list:
        pmt_gelpad_theta_list = np.append(pmt_gelpad_theta_list, round(metadict["theta"]))
pmt_gelpad_theta_list.sort()

# get all values on specific angle and average
for theta in pmt_theta_list:
    temp_occ = []
    for metadict in pmt_handler.metadicts:
        if round(metadict["theta"]) == theta:
            temp_occ.append(metadict["gain"])
    pmt_occ_list = np.append(pmt_occ_list, np.mean(temp_occ))
    pmt_occ_std_list = np.append(pmt_occ_std_list, np.std(temp_occ))

for theta in pmt_gelpad_theta_list:
    temp_occ = []
    for metadict in pmt_gelpad_handler.metadicts:
        if round(metadict["theta"]) == theta:
            temp_occ.append(metadict["gain"])
    for metadict in pmt_gelpad_overshoot_handler.metadicts:
        if round(metadict["theta"]) == theta:
            temp_occ.append(metadict["gain"])
    pmt_gelpad_occ_list = np.append(pmt_gelpad_occ_list, np.mean(temp_occ))
    pmt_gelpad_occ_std_list = np.append(pmt_gelpad_occ_std_list, np.std(temp_occ))

#plotting
fig, ax = plt.subplots()
ax.errorbar(pmt_theta_list,
            pmt_occ_list,
            pmt_occ_std_list,
            linewidth=1,
            capsize=2,
            fmt=" ",
            marker='o',
            color="tab:blue",
            label="without gelpad")

ax.fill_between(pmt_theta_list,
                pmt_occ_list - pmt_occ_std_list,
                pmt_occ_list + pmt_occ_std_list,
                color="tab:blue",
                alpha=0.2)

ax.errorbar(pmt_gelpad_theta_list,
            pmt_gelpad_occ_list,
            pmt_gelpad_occ_std_list,
            linewidth=1,
            capsize=2,
            fmt=" ",
            marker='o',
            color="tab:orange",
            label="with gelpad (no interface layer)")

ax.fill_between(pmt_gelpad_theta_list,
                pmt_gelpad_occ_list - pmt_gelpad_occ_std_list,
                pmt_gelpad_occ_list + pmt_gelpad_occ_std_list,
                color="tab:orange",
                alpha=0.2)

ax.set_xlabel("inclination of incident photon in [°]")
ax.set_ylabel("measured gain")
ax.set_title("measured gain in single photon range\nfor Hamamatsu R14374")
plt.axvline(x = 87.5, color = 'black', ls=":")
plt.axhline(y = 5e6, color = 'black', ls="-", label="desired value in tuning")
ax.text(83, 2e6, 'combined data of two \n gelpad measurements', fontsize=7, rotation=90, verticalalignment='bottom')
ax.legend()
plt.show()
