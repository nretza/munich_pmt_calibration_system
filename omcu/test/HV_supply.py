from omcu.devices.HV_supply import HV_supply
from omcu.util import setup_file_logging


setup_file_logging("/home/canada/logfile.log", logging_level=10)
HV_supply.Instance()