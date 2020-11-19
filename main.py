import argparse
import logging

import serial

from TUI import TUI
from controller import Controller

BAUD_RATE = 921600
DATA_BITS = serial.EIGHTBITS
PARITY = serial.PARITY_NONE
STOP_BITS = serial.STOPBITS_ONE
RTSCTS = True


def log_level(x: str):
    return {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }.get(x.lower(), logging.error)


def main(args):
    print("Starting...")
    device = Controller(args.device, logging_level=log_level(args.logging_level), log_file=args.log_file)
    print(device)
    print("Started")

    TUI(device, config_file=args.commands)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Controller options')
    parser.add_argument('-d', '--device', help='Device serial port')
    parser.add_argument('-l', '--logging_level', help='Logging level')
    parser.add_argument('-f', '--log_file', help='Log file')
    parser.add_argument('-c', '--commands', help='Commands to be executed on the controller')
    arguments = parser.parse_args()
    main(arguments)
