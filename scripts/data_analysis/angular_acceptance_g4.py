import sys
sys.path.append("omcu")
print(sys.path)
import os
from utils.DataHandler import DataHandler
import config
import numpy as np
import matplotlib.pyplot as plt

pmt_path = "/home/nretza/ECP_libraries/munich_pmt_calibration_system/data/aa/no_gelpad.hdf5"
pmt_gelpad_path = "/home/nretza/ECP_libraries/munich_pmt_calibration_system/data/aa/gelpad.hdf5"

G4_pmt_path = "/home/nretza/ECP_libraries/munich_pmt_calibration_system/data/aa/acceptance_no_gelpad.txt"
G4_pmt_gelpad_path = "/home/nretza/ECP_libraries/munich_pmt_calibration_system/data/aa/acceptance_gelpad.txt"

pmt_handler = DataHandler(os.path.basename(pmt_path), os.path.dirname(pmt_path))
pmt_gelpad_handler = DataHandler(os.path.basename(pmt_gelpad_path), os.path.dirname(pmt_gelpad_path))
pmt_handler.load_metadicts()
pmt_gelpad_handler.load_metadicts()

G4_pmt = np.loadtxt(G4_pmt_path)
G4_pmt_gelpad = np.loadtxt(G4_pmt_gelpad_path)

G4_pmt_smoothed = np.convolve(G4_pmt[1], [1], mode='same')
G4_pmt_gelpad_smoothed = np.convolve(G4_pmt_gelpad[1], [1], mode='same')


#----------------------------------------------


pmt_aa_list = np.array([])
pmt_aa_std_list = np.array([])
pmt_theta_list = np.array([])

pmt_gelpad_aa_list = np.array([])
pmt_gelpad_aa_std_list = np.array([])
pmt_gelpad_theta_list = np.array([])

#get thetas
for m in pmt_handler.measurements:
    metadict = m.metadict
    if round(metadict["theta [°]"]) not in pmt_theta_list:
        pmt_theta_list = np.append(pmt_theta_list, round(metadict["theta [°]"]))
pmt_theta_list.sort()
for m in pmt_gelpad_handler.measurements:
    metadict = m.metadict
    if round(metadict["theta [°]"]) not in pmt_gelpad_theta_list:
        pmt_gelpad_theta_list = np.append(pmt_gelpad_theta_list, round(metadict["theta [°]"]))
pmt_gelpad_theta_list.sort()

# get all values on specific angle and average
for theta in pmt_theta_list:
    temp_aa = []
    for m in pmt_handler.measurements:
        metadict = m.metadict
        if round(metadict["theta [°]"]) == theta:
            temp_aa.append(metadict["occ [%]"])
    pmt_aa_list = np.append(pmt_aa_list, np.mean(temp_aa))
    pmt_aa_std_list = np.append(pmt_aa_std_list, np.std(temp_aa))

for theta in pmt_gelpad_theta_list:
    temp_aa = []
    for m in pmt_gelpad_handler.measurements:
        metadict = m.metadict
        if round(metadict["theta [°]"]) == theta:
            temp_aa.append(metadict["occ [%]"]  * 1.4)
    pmt_gelpad_aa_list = np.append(pmt_gelpad_aa_list, np.mean(temp_aa))
    pmt_gelpad_aa_std_list = np.append(pmt_gelpad_aa_std_list, np.std(temp_aa))

# Create two subplots
plt.rcParams.update({'font.size': 16})
fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)
fig.tight_layout()

# Create a twinx ax
ax1twin = ax1.twinx()

# Plot pmt on the left subplot
ax1.plot(G4_pmt[0], G4_pmt_smoothed, label="Monte Carlo", c="tab:red")
ax1twin.errorbar(pmt_theta_list,
            pmt_aa_list,
            yerr = pmt_aa_std_list,
            xerr = 3 + np.rad2deg(np.sin(np.deg2rad(pmt_theta_list)) * np.arctan(4/20)),
            linewidth=1,
            capsize=2,
            fmt=" ",
            marker='o',
            c="tab:blue",
            label="OMCU measurement")

ax1.set_xlabel("PMT inclination towards laser beam in [°]")
ax1.set_ylabel("angular acceptance [%] (MC)")
ax1twin.set_ylabel("normalized PMT occupancy [%] (OMCU)")
ax1.set_title("PMT angular acceptance without gelpad")
ax1.legend(handles=[ax1.lines[0], ax1twin.lines[0]], labels=["Monte Carlo", "OMCU measurement"])

# Create a twinx ax
ax2twin = ax2.twinx()

# Plot pmt_gelpad on the right subplot
ax2.plot(G4_pmt_gelpad[0], G4_pmt_gelpad_smoothed, label="Monte Carlo", c="tab:red")
ax2twin.errorbar(pmt_gelpad_theta_list,
            pmt_gelpad_aa_list,
            yerr = pmt_gelpad_aa_std_list,
            xerr = 3 + np.rad2deg(np.sin(np.deg2rad(pmt_gelpad_theta_list)) * np.arctan(4/20)),
            linewidth=1,
            capsize=2,
            fmt=" ",
            marker='o',
            c="tab:blue",
            label="OMCU measurement")

ax2.set_xlabel("PMT inclination towards laser beam in [°]")
ax2.set_ylabel("angular acceptance [%] (MC)")
ax2twin.set_ylabel("normalized PMT occupancy [%] (OMCU)")
ax2.set_title("PMT angular acceptance with gelpad")
ax2.legend(handles=[ax2.lines[0], ax2twin.lines[0]], labels=["Monte Carlo", "OMCU measurement"])

ax1.set_ylim(bottom=0)
ax1twin.set_ylim(0, 11.3)
ax2.set_ylim(bottom=0)
ax2twin.set_ylim(0, 21.5)


# Show the plot
plt.show()