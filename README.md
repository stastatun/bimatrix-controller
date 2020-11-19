This is python controller for bimatrix electrotactile-stimulation device described in more detail 
[here](docs/BiMatrix%20User%20Manual_70V.pdf). This has only been tested on Ubuntu 18.04. This should work on 
other linux systems. Other operating systems might work but could require extra steps. Check 
[the device manual](docs/BiMatrix%20User%20Manual_70V.pdf) for guide using the device in other operating systems.

## Requirements
Tested with `Python 3.8`

## Installation
Create new virtualenv

Run `pip3 install -r requirements.txt` inside the virtual environment to install required packages

## Device connection
Guide is for linux only. The device should work out of the box in linux. If device is not detected check 
[the device manual](docs/BiMatrix%20User%20Manual_70V.pdf) for additional drivers.

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

## Usage

The program is is executed from file `main.py`. It initializes the device and launches a text interface for controlling 
the device.

### flags
`-d, --device` required, give the serial port of the device

`-l, --logging_level` define logging level- default warning, see possible logging levels from [logging](https://docs.python.org/3/library/logging.html#logging-levels)

`-f, --log_file` define log file for the program. Default none.

`-c, --commands` define file for controller commands to be executed before launching the controller 
interface.

### Example files
`commands1.txt` and `commands2.txt` are example files for command files to be given with flag `-c`

`example.py` includes example usage of the controller functions defined in the `controller.py



