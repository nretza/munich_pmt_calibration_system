#!/usr/bin/python3
# Author:  Laura Winter <evalaura.winter@tum.de>, Kilian Holzapfel <kilian.holzapfel@tum.de>

# # In case, add the home directory of this project to the python search path.
# import os
# import sys
# # E.g. if the software is installed in the home directory. Adapt in case
# sys.path.insert(0, os.path.join(os.environ['HOME'], 'munich_pmt_calibration_system'))
import sys
sys.path.append('/home/canada/munich_pmt_calibration_system/omcu')

# Import the sys-system python modules of this master-control software.
import argparse

from submodules.Picoscope import Picoscope
from submodules.PSU import PSU
from submodules.Picoamp import Picoamp
from submodules.Rotation import Rotation_stage
from submodules.Laser import Laser
from submodules.Powermeter import Powermeter
from logging_config import setup_logging
from config import Config

# set up the logging module with format, assign Handler, ...
setup_logging(to_console=True,
              # file_name=Config.omcu_log_file
              )

simulating = True


# TODO: this is just a basic implementation to show the syntax
def main(args):
    laser = Laser(simulating=args.simulating)
    print(f'Laser is at state: {laser.print_state()}')


# do things when this script is executed. Don't do it if imported.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='OMCU System.')
    parser.add_argument('--simulating', action='store_true')  # to run the software with simulated devices

    args = parser.parse_args()
    main(args)
