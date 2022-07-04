#!/usr/bin/python3
import logging
import numpy as np


class SimSerial:
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(type(self).__name__)
        self.logger.debug(f'Initialised with - args: {args}; kwargs: {kwargs}')

    @staticmethod  # function does not need self
    def readline():
        return_bytes = 'test str /n'
        return return_bytes.encode()

    @staticmethod
    def read():
        return f'{np.random.randint(0, 10)}'.encode()  # return one item

    @staticmethod
    def inWaiting():
        return np.random.random() < .8  # the probability is smaller to be False as True

    def write(self, bytes_str):
        self.logger.debug(f'SerialWrite: {bytes_str.decode().strip()}')  # .strip() to remove tailing '/n'
