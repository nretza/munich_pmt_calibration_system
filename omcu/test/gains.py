from devices.Picoscope import Picoscope
from utils.Waveform import Waveform

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

data_sgnl, data_trg = Picoscope.Instance().block_measurement(trgchannel=0,
                                                             sgnlchannel=2,
                                                             direction=2,
                                                             threshold=2000,
                                                            number=50000)
gains = []
min_val = []
for wf in data_sgnl:
    wf_obj = Waveform("_", "_", "_", wf[:, 0], wf[:, 1], np.min(wf[:, 1]))
    min_val.append(np.min(wf[:, 1]))
    gains.append(wf_obj.calculate_gain())

plt.hist2d(gains, min_val, bins=500, norm=mpl.colors.LogNorm(), cmap=mpl.cm.gray)

#plt.hist(gains, bins=500)
#plt.axvline(x = 1.6e6, color = 'b', label = 'axvline - full height')
plt.show()
