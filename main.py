import serial

BAUD_RATE = 921600
DATA_BITS = 8
PARITY = serial.PARITY_NONE
STOP_BITS = 1
RTSCTS = 1


def main():
    ser = serial.Serial("")

if __name__ == '__main__':
    main()
