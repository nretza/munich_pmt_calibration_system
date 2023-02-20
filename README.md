# munich_pmt_calibration_system
Control Software for the Optical Module Calibration Unit.

## usage

### before running

Please make sure that the following conditions are met before the OMCU is turned on:
.
1. The PMT is connected to the Picoscope via the coaxial cable labeled "Data" inside the OMCU.
2. The OMCU is properly closed and the red handles are shut.
3. The uBase is plugged in. (See plug to the right of the OMCU)
4. The following devices to the left of the OMCU are turned on:
   * the Power Meter
   * the Laser Control System
   * both PSU_0 and PSU_1
   * the Picoscope
   * the Picoamp
		 
### comand line arguments

usage: main.py [-h] [-o OUTPATH] [-n PMTNAME] [-c COOLDOWN] [-p PHI] [-t THETA] [-v HV]

optional arguments:


| short       | long                | description                                                                     |
|-------------|---------------------|---------------------------------------------------------------------------------|
| -h          | --help              | show this help message and exit                                                 |
| -o OUTPATH  | --outpath OUTPATH   | path to the program output                                                      |
| -n PMTNAME  | --pmtname PMTNAME   | name of the PMT inside the omcu                                                 |
| -c COOLDOWN | --cooldown COOLDOWN | the cooldown time in minutes to reduce noise before any measurement takes place |
| -p PHI      | --phi PHI           | list of phi angles to cycle through while datataking                            |
| -t THETA    | --theta THETA       | list of theta angles to cycle through while datataking                          |
| -v HV       | --HV HV             | list of high voltages to cycle through while datataking                         |

If no argument is given, the omcu defaults to the value in omcu/config.py

### config file
The omcu offers a config file at omcu/config.py to adjust varoius settings in detail. Please note that these configurations will be overwritten by comand line argments you pass to the omcu.