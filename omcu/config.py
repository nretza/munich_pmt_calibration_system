#!/usr/bin/python3

import numpy as np

#------------------------------------------------------
#--------------   GENERAL          --------------------
#------------------------------------------------------

#setup

OUT_PATH  = "/home/canada/munich_pmt_calibration_system/data"
PMT_NAME  = None             #asks for name at runtime if None

LOG_FILE  = "omcu.log"	     # name of the log file
LOG_LVL   = 20               # logging level (10: Debug, 20: Info, 30: Warning etc...)

COOLDOWN_TIME = 90           # Time in minutes before any measurements take place
COOLDOWN_HV   = 90

#------------------------------------------------------

# which test protocols to choose

PHOTOCATHODE_SCAN     = True
FRONTAL_HV_SCAN       = True
CHARGE_LINEARITY_SCAN = True
DARK_COUNT_SCAN       = True

#------------------------------------------------------

#Data-Analysis

ANALYSIS_PERFORM    = False     # perform data analysis after datataking
ANALYSIS_SHOW_PLOTS = False     # call plt.show()

#what to plot

ANALYSIS_PLOT_WFS                = True
ANALYSIS_PLOT_WF_AVG             = True
ANALYSIS_PLOT_WF_MSK             = True
ANALYSIS_PLOT_PEAKS              = True
ANALYSIS_PLOT_HIST_AMP           = True
ANALYSIS_PLOT_HIST_CHRG          = True
ANALYSIS_PLOT_HIST_GAIN          = True
ANALYSIS_PLOT_TTS                = True
ANALYSIS_PLOT_ANGULAR_ACCEPTANCE = True

ANALYSIS_PLOT_ANGLE_TO_GAIN      = True
ANALYSIS_PLOT_ANGLE_TO_TTS       = True
ANALYSIS_PLOT_ANGLE_TO_RISE_TIME = True

ANALYSIS_PLOT_HV_TO_GAIN         = True
ANALYSIS_PLOT_HV_TO_TTS          = True
ANALYSIS_PLOT_HV_TO_RISE_TIME    = True




#------------------------------------------------------
#--------------   PHOTOCATHODE SCAN   -----------------
#------------------------------------------------------

# an angular scan under constant gain / HV

PCS_DATAFILE      = "data_photocathode_scan.hdf5"

#-----------------------------------------------------

#tune

PCS_TUNE_MODE     = "iter"      # (none, iter, single, only_gain, only_occ)
PCS_TUNE_MAX_ITER = 15          # max iters for iter tune mode

#gain tune
PCS_TUNE_GAIN_MIN    = 4.95e6
PCS_TUNE_GAIN_MAX    = 5.05e6
PCS_TUNE_V_START     = 90          # will start at current voltage if None
PCS_TUNE_V_STEP      = 1

#occ tune
PCS_TUNE_OCC_MIN        = 0.09
PCS_TUNE_OCC_MAX        = 0.10
PCS_TUNE_LASER_START    = None       # will start at current laser tune if None
PCS_TUNE_LASER_STEP     = 1

PCS_TUNE_NR_OF_WAVEFORMS  =  100000
PCS_TUNE_SIGNAL_THRESHOLD = -4

#-----------------------------------------------------

PCS_PHI_LIST      = np.arange(0,  90, 5)          # phi angles to set while datataking (start,stop,step)
PCS_THETA_LIST    = np.arange(0, 105, 5)          # theta angles to set while datataking (start,stop,step)

PCS_NR_OF_WAVEFORMS     =  100000                 # Number of waveforms the picoscope should record per HV,phi,theta - configuration
PCS_SIGNAL_THRESHOLD    = -4                      # Determines when a waveform is considered a signal and will be written in the datafile
PCS_MEASUREMENT_SLEEP   =  1                      # Time in seconds that are waited before each recording of data




#------------------------------------------------------
#--------------   FRONTAL HV SCAN     -----------------
#------------------------------------------------------

# a scan of different HVs at frontal facing light source

FHVS_DATAFILE      = "data_frontal_HV.hdf5"

#------------------------------------------------------

#tune

FHVS_TUNE_MODE     = "only_occ"      # (none, iter, single, only_gain, only_occ)
FHVS_TUNE_MAX_ITER = 15              # max iters for iter tune mode

#gain tune
FHVS_TUNE_GAIN_MIN    = None
FHVS_TUNE_GAIN_MAX    = None
FHVS_TUNE_V_START     = None          # will start at current voltage if None
FHVS_TUNE_V_STEP      = None

#occ tune
FHVS_TUNE_OCC_MIN        = 0.09
FHVS_TUNE_OCC_MAX        = 0.10
FHVS_TUNE_LASER_START    = None       # will start at current laser tune if None
FHVS_TUNE_LASER_STEP     = 1

FHVS_TUNE_NR_OF_WAVEFORMS  =  100000
FHVS_TUNE_SIGNAL_THRESHOLD = -4

#------------------------------------------------------

FHVS_HV_LIST       = np.arange(75,105,1)          # HVs to set while datataking (start,stop,step)

FHVS_NR_OF_WAVEFORMS     =  100000                # Number of waveforms the picoscope should record per HV,phi,theta - configuration
FHVS_SIGNAL_THRESHOLD    = -4                     # Determines when a waveform is considered a signal and will be written in the datafile
FHVS_MEASUREMENT_SLEEP   =  1                     # Time in seconds that are waited before each recording of data




#------------------------------------------------------
#-----------   CHARGE LINEARITY SCAN     --------------
#------------------------------------------------------

# a scan of different laser tunes at frontal facing light source

CLS_DATAFILE      = "data_linearity.hdf5"

#------------------------------------------------------

#tune

CLS_TUNE_MODE     = "iter"      # (none, iter, single, only_gain, only_occ)
CLS_TUNE_MAX_ITER = 15          # max iters for iter tune mode

#gain tune
CLS_TUNE_GAIN_MIN    = 4.95e6
CLS_TUNE_GAIN_MAX    = 5.05e6
CLS_TUNE_V_START     = 90          # will start at current voltage if None
CLS_TUNE_V_STEP      = 1

#occ tune
CLS_TUNE_OCC_MIN        = 0.09
CLS_TUNE_OCC_MAX        = 0.10
CLS_TUNE_LASER_START    = None       # will start at current laser tune if None
CLS_TUNE_LASER_STEP     = 1

CLS_TUNE_NR_OF_WAVEFORMS  =  100000
CLS_TUNE_SIGNAL_THRESHOLD = -4

#------------------------------------------------------

CLS_LASER_TUNE_LIST     = np.arange(720,600,-2)  # Laser tunes to set while data taking (start,stop,step)

CLS_NR_OF_WAVEFORMS     =  100000                # Number of waveforms the picoscope should record per configuration
CLS_SIGNAL_THRESHOLD    = -4                     # Determines when a waveform is considered a signal and will be written in the datafile
CLS_MEASUREMENT_SLEEP   =  30                    # Time in seconds that are waited before each recording of data




#------------------------------------------------------
#-------------    DARK COUNT SCAN      ----------------
#------------------------------------------------------

# a long time scan with turned off laser under different HVs

DCS_DATAFILE      = "data_dark_count.hdf5"

#------------------------------------------------------

DCS_HV_LIST             = np.arange(75,105,1)    # HVs to set while data taking (start,stop,step)

DCS_NR_OF_SAMPLES       = 10000                  # Number of samples the picoscope should record per waveform
DCS_NR_OF_WAVEFORMS     = 10000                  # Number of waveforms per iteration
DCS_NR_OF_ITERATIONS    = 10                     # Number of iterations per HV-configuration
DCS_SIGNAL_THRESHOLD    = -4                     # Determines when a waveform is considered a signal
DCS_MEASUREMENT_SLEEP   =  1                     # Time in seconds that are waited before each recording of data
