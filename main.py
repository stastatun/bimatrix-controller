import time

import serial
import argparse

import controller

BAUD_RATE = 921600
DATA_BITS = serial.EIGHTBITS
PARITY = serial.PARITY_NONE
STOP_BITS = serial.STOPBITS_ONE
RTSCTS = True


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
def main(arg):
    device = controller.Controller(arg.device)
    commands = ['ON', 'SV;0x78', 'MUX;OFF', 'SYNC;A', 'SR;H', 'MP;0x000015 0x32',
                'SC;0x0064 0x0000 0x00C8 0x0000 0x01F4 0x0000 0x0000',
                'PW;0x00FA 0x00FA 0x00FA 0x00FA 0x00FA 0x00FA', 'T', 'OFF', 'SOC']

    #for c in commands:
        #print(bytes(c, 'utf-8'))
    #commadline_mode(arg)
    #predefined_mode(arg)
    print("Starting")
    test = device.read_response_()
    print(test)
    res = device.set_pulse_generator(True)
    print(res)
    battery_level = device.read_battery()
    print("Battery level is: {}%".format(battery_level))
    res = device.set_pulse_generator(False)
    print(res)

    print("Quitting...")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Controller options')
    parser.add_argument('-d', '--device', help='Device serial port')
    args = parser.parse_args()
    main(args)
