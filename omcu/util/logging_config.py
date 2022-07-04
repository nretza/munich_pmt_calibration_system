#!/usr/bin/python3
# Author:  Kilian Holzapfel <kilian.holzapfel@tum.de>

import json
import logging
import logging.handlers
import os


class MsgCounterFileHandler(logging.Handler):
    """
    A handler class which counts the logging records by level and periodically writes the counts to a json file.
    """

    def __init__(self, filename, continue_counts=True, *args, **kwargs):
        """
        Initialize the handler.

        PARAMETER
        ---------
        continue_counts: bool, optional
            defines if the counts should be loaded and restored if the json file exists already.
        """
        logging.Handler.__init__(self, *args, **kwargs)

        filename = os.fspath(filename)
        self.baseFilename = os.path.abspath(filename)

        self.continue_counts = continue_counts

        # if another instance of this class is created, get the actual counts
        self.level2count_dict = self.load_counts_from_file()

        # set level and update the json file, else do it when the level is set
        if self.level is not logging.NOTSET:
            self.setLevel(self.level)

    def emit(self, record):
        """
        Counts a record.
        In case, create add the level to the dict.
        If the time has come, update the json file.
        """
        level_name = record.levelname
        if level_name not in self.level2count_dict:
            self.level2count_dict[level_name] = 0
        self.level2count_dict[level_name] += 1

        self.flush()

    def flush(self):
        """
        Flushes the dictionary.
        """
        self.acquire()
        try:
            with open(self.baseFilename, 'w') as f:
                json.dump(self.level2count_dict, f)
        finally:
            self.release()

    def setLevel(self, level):
        """
        Set the logging level of this handler.  level must be an int or a str.
        """
        self.level = logging._checkLevel(level)

        # add levels to the counter dict. for the levels the Handler is listening to
        for level_int, level_name in logging._levelToName.items():  # get the dict, WARNING can be ignored
            if level_name not in self.level2count_dict and level_int >= self.level:
                self.level2count_dict[level_name] = 0

        self.flush()  # create the file

    def load_counts_from_file(self):
        """
        Load the dictionary from a json file or create an empty dictionary
        """
        level2count_dict = {}
        if os.path.exists(self.baseFilename) and self.continue_counts:
            try:
                with open(self.baseFilename) as f:
                    level2count_dict = dict(json.load(f))
            except Exception as a:
                logging.warning(f'Failed to load counts with: {a}')
                level2count_dict = {}

        return level2count_dict


def setup_logging(log_level=logging.DEBUG, to_console=False, file_name=None, msg_counter_file=None):
    """ Setup of the logging module. This piece of code has to be placed at the very beginning of the 'main' code,
    right after the imports or even before some imports i.e. `scheduler` or `Pyro` if those modules should have a
    different logging level than the rest.

    PARAMETERS
    ----------
    file_name
    log_level: logging level, optional
        The general logging level. Default is DEBUG
    to_console: bool, optional
        If True, logging prints to the console.
    file_name: Str or None, optional
        If set, logging to a file is enabled. The path and name is specified in thee config.py
    msg_counter_file: Str or None, optional
        If set, the logging msg are counted and saved in the file defined. In case the ending is replaced to '.json'.
        This can be used to monitor the system state, i.e. with InfluxDB-Telegraf-Grafana.
    """
    # set up logger
    # formatter is documented in 15.6.15. Formatter Objects
    # look above or: https://docs.python.org/3.1/library/logging.html#logging.Formatter
    # or: https://docs.python.org/3.1/library/logging.html#logging.handlers.HTTPHandler
    # for padding you can add a min size, e.g. '%(funcName)20s'

    logging.getLogger('schedule').setLevel(logging.WARNING)

    formatter_list = ['%(asctime)s',
                      '%(levelname)s',
                      # Text logging level for the message ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
                      # '%(processName)s', # Process name (if available).
                      '%(threadName)s',  # Thread name (if available).
                      # '%(thread)d',  # Thread ID (if available).
                      '%(name)s',  # Name of the logger (logging channel).
                      '%(funcName)s',  # Name of function containing the logging call.
                      '%(lineno)d',  # Source line number where the logging call was issued (if available).
                      '%(message)s'  # The logged message, computed as msg % args.
                      ]

    # get and set root logger. The base for everything in the logging world.
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # assign Handlers if set
    if file_name is not None:
        # create file handler which logs to a file. The files are rotated and kept for 10 rotations.
        # E.g.: 'W0' once per week on Monday (or Sunday?) a new file is started
        fh = logging.handlers.TimedRotatingFileHandler(file_name, when='W0', backupCount=10, utc=True)
        fh.setLevel(log_level)
        formatter = logging.Formatter(";".join(formatter_list))
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    if to_console:
        # Create console handler, with a different formatter
        ch = logging.StreamHandler()
        ch.setLevel(log_level)
        ch.setFormatter(logging.Formatter('%(asctime)s;%(levelname)7s; %(name)20s - %(message)s'))  # formatter)
        logger.addHandler(ch)

    if msg_counter_file is not None:
        # Create msg counter handler which counts the msg with a level equal or higher than WARNING.
        # The counts are stored in a json file. Which can be used to monitor the state with
        # e.g. InfluxDB/Telegraf/Grafana
        if msg_counter_file.endswith('.json'):
            pass
        elif len(msg_counter_file[-5:].rsplit('.', 1)) > 1:  # just check if there is a '.' in the last 5 elements
            msg_counter_file = msg_counter_file.rsplit('.', 1)[0] + '.json'  # replace the ending

        msg_counter_handler = MsgCounterFileHandler(msg_counter_file, level=logging.WARNING)
        logger.addHandler(msg_counter_handler)

    return logger
