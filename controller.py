import serial
import array
import logging
from typing import Iterable


class Controller:

    def __init__(self, device, baud_rate=921600, data_bits=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                 stop_bits=serial.STOPBITS_ONE, rtscts=True, logging_level=logging.WARNING):
        """ Initialize the controller"""

        logging.basicConfig(filename="", level=logging_level)

        self.mode = 'none'  # unipolar or bipolar
        self.repetition_rate = 0
        self.pulse_widths = []
        self.time_between = 0

        try:
            self.serial_ = serial.Serial(device, baud_rate, timeout=5, parity=parity, rtscts=rtscts, stopbits=stop_bits,
                                         bytesize=data_bits)

            # The device seems to establish the connection little slowly,
            # so just some test read before starting actual commands.
            # The device when using Bluetooth connection sends random 'g' on new connections
            try:
                res = self.serial_.read(10)
                logging.debug("{}, {}, {}".format(res, len(res), int.from_bytes(res, byteorder="big")))
            except serial.SerialException as e:
                print("Initial test read failed")
                logging.error(e)

        except serial.SerialException as e:
            print("Error connecting to serial port")
            logging.error(e)
            exit(0)

    def __del__(self):
        try:
            self.serial_.close()
        except serial.SerialException as e:
            print("Error closing serial port")
            logging.error(e)
            exit(0)

    def close_serial(self):
        try:
            self.serial_.close()
        except serial.SerialException as e:
            print("Error closing serial port")
            logging.error(e)
            exit(0)

    @staticmethod
    def res_to_bool_(res):
        return res == ">OK<"

    @staticmethod
    def to_bytes_(cmd):
        return bytes(cmd, 'ascii')

    @staticmethod
    def command_builder(command: str, param: int, num_bytes: int) -> bytes:
        formatted = ">{};".format(command)
        cmd = Controller.to_bytes_(formatted)
        cmd += param.to_bytes(num_bytes, byteorder='big')
        cmd += Controller.to_bytes_('<')

        return cmd

    def send_command(self, cmd: bytes) -> bool:
        logging.debug(cmd)

        self.serial_.write(cmd)
        res = self.read_response_()

        return self.res_to_bool_(res)

    def read_response_(self):
        ser = self.serial_
        res = ""
        while True:
            r = ser.read()
            if r:
                res += r.decode('ascii')
                if "<" in res:
                    break
            else:
                break
        logging.debug(res)
        return res

    # Common commands

    def set_current_range(self, current_range) -> bool:
        """Sets the current range H for high (up to 100mA) and L for Low (up to 10mA)"""
        cmd = ">SR;{}<".format(current_range)
        cmd = self.to_bytes_(cmd)

        return self.send_command(cmd)

    def set_voltage(self, voltage: int) -> bool:
        """Sets voltage in volts (value between 70-150)"""
        return self.send_command(self.command_builder("SV", voltage, 1))

    def set_pulse_generator(self, status: bool) -> bool:
        """Set pulse DC/DC pulse generator on or off

        :param status: Status of pulse generator

        :return: True if setting pulse generator succeeded.
        """
        if status:
            cmd = ">ON<"
        else:
            cmd = ">OFF<"

        cmd = self.to_bytes_(cmd)
        return self.send_command(cmd)

    def set_num_nplets(self, num: int) -> bool:
        """Set the number of n-plets to be generated (0 - 16777215)"""
        return self.send_command(self.command_builder('SN', num, 4))

    def set_time_between(self, time_between: int) -> bool:
        """Set time between pulses in n-plet (1-255ms)"""
        return self.send_command(self.command_builder('ST', time_between, 1))

    def set_delay(self, delay):
        """Set delay after trigger"""
        return self.send_command(self.command_builder('SD', delay, 4))

    def trigger_pulse_generator(self):
        """Sets pulse generators either active or not active"""
        cmd = self.to_bytes_(">T<")
        return self.send_command(cmd)

    def read_battery(self):
        """Read remaining battery capacity"""
        cmd = ">SOC<"
        self.serial_.write(self.to_bytes_(cmd))

        logging.debug(cmd)

        res = self.read_response_()
        if res.startswith('>SOC;'):
            battery_level = int.from_bytes(self.to_bytes_(res[-2]), byteorder="big")
            return battery_level
        else:
            return -1

    # long protocol

    def set_repetition_rate(self, num=50) -> bool:
        """Set n-plet repetition rate (1-400)"""
        return self.send_command(self.command_builder('SF', num, 2))

    def set_pulse_width(self, widths: Iterable[int]):
        """Set pulse width for every pulse in n-plet (50 - 1000 microseconds)"""
        cmd = self.to_bytes_('>PW;')

        for idx, num in enumerate(widths):
            cmd += num.to_bytes(2, byteorder='big')

        cmd += self.to_bytes_('<')

        return self.send_command(cmd)

    def set_amplitude(self, amplitudes: Iterable[int]) -> bool:
        """Set amplitude of the pulses in n-plet (0 - 1000) unit: w/10 or w/100"""
        cmd = self.to_bytes_('>SC;')

        for idx, num in enumerate(amplitudes):
            cmd += num.to_bytes(2, byteorder='big')

        cmd += self.to_bytes_('<')

        return self.send_command(cmd)

    def set_mode(self, mode: str) -> bool:
        """Set mode to either unipolar or bipolar"""
        if mode == 'unipolar':
            cmd = '>MUX;OFF<'
        elif mode == 'bipolar':
            cmd = '>MUX;ON<'
        else:
            raise ValueError('No mode named: {}, use value unipolar or bipolar'.format(mode))
        cmd = self.to_bytes_(cmd)
        return self.send_command(cmd)

    def set_common_electrode(self, electrode: str) -> bool:
        """Set common electrode to anode or cathode, unipolar only"""
        if not (electrode == 'C' or electrode == 'A'):
            raise ValueError('No option: {}, use value "A" for anode and "C" for cathode')
        cmd = '>ASYNC;{}<'.format(electrode)
        cmd = self.to_bytes_(cmd)
        return self.send_command(cmd)

    def set_pulses_unipolar(self, output_channels, value_type: str = 'list') -> bool:
        """Set n-plet pulses and output channels for each pulse, unipolar only"""
        cmd = self.to_bytes_('>SA;')
        if value_type == "hex":
            for idx, channels in enumerate(output_channels):
                value = bytes(bytearray.fromhex(channels))
                cmd += value
        else:
            for i, channels in enumerate(output_channels):
                value = 0
                for j, c in enumerate(channels):
                    if c == 0:
                        continue
                    value += pow(2, c-1)
                cmd += value.to_bytes(3, byteorder='big')

        cmd += self.to_bytes_('<')

        return self.send_command(cmd)

    def set_pulses_bipolar(self, channel_pairs, value_type: str = 'list') -> bool:
        """Set n-plet pulses and output channels cathode/anode pairs for each pulse, bipolar only"""
        cmd = self.to_bytes_(">CA;")
        for x, y in channel_pairs:
            if value_type == 'hex':
                cathode = bytes(bytearray.fromhex(x))
                anode = bytes(bytearray.fromhex(y))
                cmd += cathode
                cmd += anode
            else:
                cathode = 0
                anode = 0
                for i, c in enumerate(x):
                    if c == 0:
                        continue
                    cathode += pow(2, c - 1)
                for i, c in enumerate(y):
                    if c == 0:
                        continue
                    anode += pow(2, c - 1)
                cmd += cathode.to_bytes(3, byteorder='big')
                cmd += anode.to_bytes(3, byteorder='big')

        cmd += self.to_bytes_('<')

        return self.send_command(cmd)

    # Short protocol mode

    def set_common_electrode_short(self, electrode) -> bool:
        if not (electrode == 'C' or electrode == 'A'):
            raise ValueError('No option: {}, use value "A" for anode and "C" for cathode')
        cmd = '>SYNC;{}<'.format(electrode)
        cmd = self.to_bytes_(cmd)

        return self.send_command(cmd)

    def set_output_channel_activity(self, output_channels, repetition_rate: int, value_type: str = 'list') -> bool:
        cmd = self.to_bytes_('>MP;')
        if value_type == 'hex':
            cmd += bytes(bytearray.fromhex(output_channels))
        else:
            value = 0
            for i, c in enumerate(output_channels):
                value += pow(2, c - 1)
            cmd += value.to_bytes(3, byteorder='big')

        cmd += repetition_rate.to_bytes(1, byteorder='big')
        cmd += self.to_bytes_('<')

        return self.send_command(cmd)
