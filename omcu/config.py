# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>

import os


class Config:
    # ------------ basic setup ---------------------------------
    home_dir = os.environ['HOME']

    # ------------ Logging ----------------------------------------------
    omcu_log_file: str = os.path.join(home_dir, 'logs/omcu.log')
    omcu_msg_counter_file: str = omcu_log_file.replace('.log', '_count.json')  # counting each level
