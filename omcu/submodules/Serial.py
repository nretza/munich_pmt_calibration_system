#!/usr/bin/python3
import logging
import serial
import time


class Serial(serial):
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(type(self).__name__)
        self.logger.debug(f'Initialised with - args: {args}; kwargs: {kwargs}')

    def write_serial(self, cmd, delay=None, line_ending=b'\r\n'):
        """

        PARAMETERS
        ----------
        cmd: Str, bytes, optional
        delay: float or None, optional
        line_ending: bytes, optional
        """
        if delay is None:
            delay = self.delay

        if type(cmd) is str:
            cmd = cmd.encode()

        if not cmd.endswith(line_ending):
            cmd += line_ending

        self.serial.write(cmd)
        time.sleep(delay)

        return_str = self.serial.readline().decode()

        self.logger.debug(f'Serial write cmd: {cmd}; return {return_str}')
        return return_str