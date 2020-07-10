import serial
import argparse

BAUD_RATE = 921600
DATA_BITS = serial.EIGHTBITS
PARITY = serial.PARITY_NONE
STOP_BITS = serial.STOPBITS_ONE
RTSCTS = True


def main(args):

    # Example commands
    commands = ['ON', 'SV;0x78', 'MUX;OFF', 'SYNC;A', 'SR;H', 'MP;0x000015 0x32',
                'SC;0x0064 0x0000 0x00C8 0x0000 0x01F4 0x0000 0x0000',
                'PW;0x00FA 0x00FA 0x00FA 0x00FA 0x00FA 0x00FA', 'T', ]

    with serial.Serial(args.device, BAUD_RATE, timeout=1, parity=PARITY, rtscts=RTSCTS, stopbits=STOP_BITS, bytesize=DATA_BITS) as ser:
        for command in commands:
            s = '>%s<' % command
            ser.write(ascii(s))
            x = ser.read_until('<')
            print(x)
    print("Quitting...")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Controller options')
    parser.add_argument('-d', '--device', help='Device serial port')
    args = parser.parse_args()
    main(args)
