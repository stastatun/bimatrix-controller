import time

import serial
import argparse
import logging

import controller

BAUD_RATE = 921600
DATA_BITS = serial.EIGHTBITS
PARITY = serial.PARITY_NONE
STOP_BITS = serial.STOPBITS_ONE
RTSCTS = True


def log_level(x: str):
    levels = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    return levels[x.lower()]


def commadline_mode(arg):
    with serial.Serial(arg.device, BAUD_RATE, timeout=None, parity=PARITY, rtscts=RTSCTS, stopbits=STOP_BITS,
                       bytesize=DATA_BITS) as ser:
        while True:
            c = input("Command: ")
            if c.lower() == "quit":
                break
            s = '>%s<' % c
            print("Sending command {}".format(c))
            ser.write(bytes(s, 'utf-8'))
            res = ""
            while True:
                r = ser.read()
                if r:
                    res += r.decode('ascii')
                    if "<" in res:
                        print(res)
                        break
                else:
                    print("Pass")

def predefined_mode(arg):
    # Example commands
    commands = ['ON', 'SV;0x78', 'MUX;ON', 'SF;0x0032', 'SR;H',
                'CA;0x200000 0x400000 0x000001 0x000002 0x004000 0x008000 0x000000 0x000000 0x000000 0x000000',
                'CA;0x200000 0x400000 0x000001 0x000002 0x004000 0x008000 0x000000 0x000000 0x000000 0x000000',
                'PW;0x00FA 0x00FA 0x00FA 0x00FA 0x00FA 0x00FA', 'T', 'T', 'OFF', 'SOC']
    with serial.Serial(arg.device, BAUD_RATE, timeout=None, parity=PARITY, rtscts=RTSCTS, stopbits=STOP_BITS, bytesize=DATA_BITS) as ser:
        """for c in commands:
            s = '>%s<' % c
            print("Sending command {}".format(c))
            ser.write(bytes(s, 'utf-8'))
            res = ""
            while True:
                r = ser.read()
                if r:
                    res += r.decode('ascii')
                    if "<" in res:
                        print(res)
                        break
                else:
                    print("Pass")"""
def main(args):
    print("Starting...")

    device = controller.Controller(args.device, logging_level=log_level(args.logging_level))
    commands = ['ON', 'SV;0x78', 'MUX;OFF', 'SYNC;A', 'SR;H', 'MP;0x000015 0x32',
                'SC;0x0064 0x0000 0x00C8 0x0000 0x01F4 0x0000 0x0000',
                'PW;0x00FA 0x00FA 0x00FA 0x00FA 0x00FA 0x00FA', 'T', 'OFF', 'SOC']
    print("Started.")

    #for c in commands:
        #print(bytes(c, 'utf-8'))
    #commadline_mode(arg)
    #predefined_mode(arg)

    res = device.set_pulse_generator(True)
    print(res)
    battery_level = device.read_battery()
    print("Battery level is: {}%".format(battery_level))
    res = device.set_pulse_generator(False)
    print(res)

    print("Test current range")
    res = device.set_current_range('H')
    print(res)
    res = device.set_current_range('L')
    print(res)

    print("Test voltage")
    res = device.set_voltage(150)
    print(res)
    res = device.set_voltage(70)
    print(res)
    res = device.set_voltage(85)
    print(res)

    print("Test num of n-plets")
    res = device.set_num_nplets(0)
    print(res)
    res = device.set_num_nplets(16777215)
    print(res)
    res = device.set_num_nplets(14500)
    print(res)

    print("Test time between pulses")
    res = device.set_time_between(255)
    print(res)
    res = device.set_time_between(1)
    print(res)
    res = device.set_time_between(126)
    print(res)

    print("Test delay")
    res = device.set_delay(0)
    print(res)
    res = device.set_delay(16777215)
    print(res)
    res = device.set_delay(5000)
    print(res)

    print("Test trigger")

    res = device.trigger_pulse_generator()
    print(res)

    print("Sleep for 5 seconds")
    #time.sleep(5)

    res = device.trigger_pulse_generator()
    print(res)

    print("Test n-plet repetition rate")
    res = device.set_repetition_rate(1)
    print(res)
    res = device.set_repetition_rate(400)
    print(res)

    print("Test pulse widths")
    res = device.set_pulse_width([50, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    print(res)

    print("Test amplitude")
    res = device.set_amplitude([50, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    print(res)

    print("Test mode")
    res = device.set_mode('unipolar')
    print(res)
    #res = device.set_mode('bipolar')
    #print(res)

    print("Test common electrode")
    res = device.set_common_electrode('A')
    print(res)
    res = device.set_common_electrode('C')
    print(res)

    print("Test unipolar channels")
    res = device.set_pulses_unipolar(
        ['800000', '400000', '200000', '100000', '080000', '040000', '020000', '010000',
         '008000', '004000', '002000', '001000', '000800', '000400', '000200', '000100',
         '000000', '000000', '000000', '000000', '000000', '000000', '000000', '000000'], value_type='hex')
    print(res)
    """res = device.set_pulses_unipolar(
        [
            [24], [23], [22], [21], [20], [19], [18], [17], [16], [15], [14],
            [13], [12], [11], [10], [9], [8], [7], [6], [5], [4], [3], [2], [1]
        ], value_type='list'
    )"""
    res = device.set_pulses_unipolar(
        [
            [24], [23], [0], [0], [0], [0], [0], [0], [0], [0], [0],
            [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0]
        ], value_type='list'
    )
    print(res)
    device.close_serial()

    print("Quitting...")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Controller options')
    parser.add_argument('-d', '--device', help='Device serial port')
    parser.add_argument('-l', '--logging_level', help='Logging level')
    arguments = parser.parse_args()
    main(arguments)
