#!/usr/bin/python3
import serial
import time


def io_serial(cmd, delay=0.1, serial=serial):
        """
        1. Checks if something is to read. 2. write command to serial 3. checks if response is available and if yes: prints it
        PARAMETERS
        ----------
        cmd: bytes
        delay: float or None
        """
        sep = ': '
        if serial.in_waiting:
            string = str(serial.read_until(size=serial.in_waiting)[:-2], 'utf-8')
            #split_str = string.split(sep)
            #if split_str[0] == '0':
            print(string, 'Leftover from the serial buffer!')
            #print(str(serial.read_until(size=serial.in_waiting)[:-2], 'utf-8'))
        
        serial.write(cmd)
        
        while True:
            if serial.in_waiting > 0:
                string = str(serial.read(size=serial.in_waiting)[:-2], 'utf-8')
                split_str = string.split(sep)
                if split_str[0] == '0':
                    ret = float(split_str[1])
                else:
                    print(split_str[1])
                #print(string)
                
                break
            time.sleep(delay)
        return ret
