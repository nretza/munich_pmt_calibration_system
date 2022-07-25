#!/usr/bin/python3
import logging
import numpy as np


class sim_serial:
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(type(self).__name__)
        self.logger.debug(f'Initialized with - args: {args}; kwargs: {kwargs}')

    @staticmethod  # function does not need self
    def readline():
        return_bytes = 'test str /n'
        return return_bytes.encode()

    @staticmethod  # function does not need self
    def readlines():
        return_bytes = 'test str /n'
        return return_bytes.encode()

    @staticmethod
    def read():
        return f'{np.random.randint(0, 10)}'.encode()  # return one item

    @staticmethod
    def inWaiting():
        return np.random.random() < .8  # the probability is smaller to be False as True

    @staticmethod
    def reset_input_buffer():
        pass

    @staticmethod
    def reset_output_buffer():
        pass

    def write(self, bytes_str):
        self.logger.debug(f'SerialWrite: {bytes_str.decode().strip()}')  # .strip() to remove tailing '/n'
