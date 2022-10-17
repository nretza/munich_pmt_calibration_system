from devices.HV_base import HV_base
from utils.util import setup_file_logging
setup_file_logging("logger.log", 10)
UID = HV_base.Instance().getUID()
print(UID)
print(HV_base.Instance().getAvgReport())
