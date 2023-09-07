# Disclaimer

This is a copy of the [P-ONE OMCU repository](https://github.com/pone-software/munich_pmt_calibration_system/) up to commit 32bfad6e2567b9f87f8abfd742b11f64f68118b0. This repository exists purely for personal archival purposes.

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

usage: omcu [-h] [-l LOGLVL] [-o OUTPATH] [-n PMTNAME] [-c COOLDOWN] [--config CONFIG] [--script SCRIPT] [--printconfig]

optional arguments:


| short       | long                | description                                                                         |
|-------------|---------------------|-------------------------------------------------------------------------------------|
| -h          | --help              | show this help message and exit                                                     |
| -o OUTPATH  | --outpath OUTPATH   | path to the program output                                                          |
| -n PMTNAME  | --pmtname PMTNAME   | name of the PMT inside the omcu                                                     |
| -c COOLDOWN | --cooldown COOLDOWN | the cooldown time in minutes to reduce noise before any measurement takes place     |
|             | --config CONFIG     | path to an alternative config file, which should be used instead of the default one | 
|             | --script SCRIPT     | executes the given script instead of the main program                               |
|             | --printconfig       | prints the content of the given config file. Exits the program afterwards           |

If no argument is given, the omcu defaults to the value in omcu/config.py

### config file
The omcu offers a config file at omcu/config.py to adjust varoius settings in detail. Please note that these configurations will be overwritten by comand line argments you pass to the omcu.
