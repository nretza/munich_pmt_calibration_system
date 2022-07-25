import numpy
#------------------------------------------------------

#file setup
import numpy as np

OUT_PATH = "/home/canada/omcu_data"
PMT_NAME = None
LOG_FILE = "omcu.log"
DATA_FILE = "Data.hdf5"

#------------------------------------------------------

# data taking

COOLDOWN_TIME = 30

HV_LIST       = np.arange(1000, 1400, 20)   #HVs to set while datataking (start,stop,step)
PHI_LIST      = np.arange(0,90,5)           #phi angles to set while datataking (start,stop,step)
THETA_LIST    = np.arange(0,90,5)           #theta angles to set while datataking (start,stop,step)

NR_OF_WAVEFORMS     = 100000                #Number of waveforms the picoscope should record per HV,phi,theta - configuration
SIGNAL_THRESHOLD    = -4                    #Determines when a waveform is considered a signal and will be written in the datafile
MEASUREMENT_SLEEP   = 1                     #Time in seconds that are waited before each recording of data

#------------------------------------------------------

#tune

TUNE_MODE   = "iter" #none, iter, single, only_gain, only_occ
TUNE_MAX_ITER = 10   #max iters for iter tune mode

#gain tune
GAIN_MIN    = 0.97e6
GAIN_MAX    = 1.03e6
V_START     = None # will start at current voltage when None
V_STEP      = 10

#occ tune
OCC_MIN             = 0
OCC_MAX             = 0.1
LASER_TUNE_START    = None # will start at current laser tune when None
LASER__TUNE_STEP    = 10

TUNE_NR_OF_WAVEFORMS  = 10000
TUNE_SIGNAL_THRESHOLD = -4

#-----------------------------------------------------