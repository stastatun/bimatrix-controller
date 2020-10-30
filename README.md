This is python controller for bimatrix electrotactile-stimulation device described in more detail [here](docs/BiMatrix%20User%20Manual_70V.pdf)

## Requirements
Tested with `Python 3.8`

## Installation
Create new virtualenv

Run `pip3 install -r requirements.txt` inside the virtual environment to install required packages

## Device connection
Guide is for linux only (for now)

### USB
Connect the bimatrix device to the host computer with USB cable

Find the serial port name `dmesg | grep tty`
Look for name **FTDI USB Serial Device converter**

Check that serial port has proper permissions assigned if program is not working

Run the program with `python3 main.py --device /dev/<serial_port>`

### Bluetooth
Pair the bimatrix device.

Find the controller MAC-address (e.g. using bluetoothctl)

create serial channel between the host and the bimatrix device `rfcomm bind 0 <device MAC-address> [channel]`

Check that serial port has proper permissions assigned if program is not working

Run the program with `python3 main.py --device /dev/rfcomm0`

Release the serial binding with `rfcomm release 0`



