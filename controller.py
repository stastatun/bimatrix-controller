import serial
import logging

from typing import List, Tuple


class Controller:

    def __init__(self, device, baud_rate=921600, data_bits=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                 stop_bits=serial.STOPBITS_ONE, rtscts=True, logging_level=logging.WARNING, log_file=""):
        """ Initialize the controller"""

        logging.basicConfig(filename=log_file, level=logging_level)

        self.current_range = 'high'  # high or low
        self.voltage = 150  # range 70V - 150V
        self.pulse_generator_dc_converter_status = False
        self.num_nplets = 0  # 0 (infinity) - 16777215
        self.time_between = 1  # 1ms - 255ms
        self.delay = 0  # 0ms - 16777215ms
        self.pulse_generator_triggered = False
        self.battery_state = -1
        self.repetition_rate = 50  # 1 - 400pps (pulses per second)
        self.pulse_widths = [250]  # 50 - 1000 microseconds
        self.pulse_amplitudes = [100]  # w = 100 - 1000, unit w/10 mA (High), w/100 mA (Low)
        self.mode = 'none'  # unipolar or bipolar
        self.common_electrode = 'cathode'  # cathode or anode
        self.output_channels = []
        self.channel_pairs = []
        self.is_short_protocol = False

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

    def check_nplet_parameter_validity(self, pulse_widths=None, time_between=None, repetition_rate=None) -> bool:
        if pulse_widths is None:
            pulse_widths = self.pulse_widths
        if time_between is None:
            time_between = self.time_between
        if repetition_rate is None:
            repetition_rate = self.repetition_rate
        t1 = sum(pulse_widths)*10**-6 + (len(pulse_widths)-1)*time_between*10**-3
        t2 = 1/repetition_rate
        return t1 <= t2

    def print_state(self) -> None:
        print("""
Device state (Battery: {}%):
    Device mode: {}
        - unipolar common electrode: {}
        - output channels (unipolar): {}
        - channel pairs (bipolar): {}
    Current range: {}, voltage: {}V
    Current generator dc/dc converter is on: {}
    Number of n-plets: {}
    Time between pulses: {}ms
    Delay after trigger: {}ms
    Pulse generation is triggered: {}
    N-plet repetition rate: {}pps
    Pulse widths: {} (unit: μs)
    Pulse amplitudes: {} (unit: mA)
    Short protocol activated: {}
        """.format(self.battery_state, self.mode, self.common_electrode, self.output_channels, self.channel_pairs,
                   self.current_range, self.voltage, self.pulse_generator_dc_converter_status, self.num_nplets,
                   self.time_between, self.delay, self.pulse_generator_triggered, self.repetition_rate,
                   self.pulse_widths, self.pulse_amplitudes, self.is_short_protocol))
        print("Is current n-plet generation parameters possible: {}".format(self.check_nplet_parameter_validity()))

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

    def set_current_range(self, current_range: str) -> bool:
        """Sets the current range H for high (up to 100mA) and L for Low (up to 10mA)"""
        if current_range.lower() == 'high':
            c = 'H'
        elif current_range.lower() == 'low':
            c = 'L'
        else:
            raise ValueError("Current range must be set to 'high' or 'low'. Was set to: {}".format(current_range))
        cmd = ">SR;{}<".format(c)
        cmd = self.to_bytes_(cmd)

        res = self.send_command(cmd)

        if res:
            self.current_range = current_range.lower()
        else:
            logging.warning("Failed to set current range")

        return res

    def set_voltage(self, voltage: int) -> bool:
        """Sets voltage in volts (value between 70-150)"""
        if voltage < 70 or voltage > 150:
            raise ValueError("Given voltage is out of range. Voltage must be between 70-150")
        res = self.send_command(self.command_builder("SV", voltage, 1))
        if res:
            self.voltage = voltage

        return res

    def set_pulse_generator(self, status: bool) -> bool:
        """Set pulse DC/DC pulse generator on or off

        :param status: Status of pulse generator

        :return: True if setting pulse generator succeeded.
        """
        if status:
            cmd = ">ON<"
        else:
            cmd = ">OFF<"

        res = self.send_command(self.to_bytes_(cmd))
        if res:
            self.pulse_generator_dc_converter_status = status

        return res

    def toggle_pulse_generator(self) -> bool:
        """Set pulse DC/DC pulse generator on or off"""
        if self.pulse_generator_dc_converter_status:
            cmd = ">OFF<"
        else:
            cmd = ">ON<"

        res = self.send_command(self.to_bytes_(cmd))
        if res:
            self.pulse_generator_dc_converter_status = not self.pulse_generator_dc_converter_status

        return res

    def set_num_nplets(self, num: int) -> bool:
        """Set the number of n-plets to be generated (0 - 16777215)"""
        if num < 0 or num > 16777215:
            raise ValueError("Number of n-plets (num) must be between 0 and 16777215, was {}".format(num))

        res = self.send_command(self.command_builder('SN', num, 4))
        if res:
            self.num_nplets = num

        return res

    def set_time_between(self, time_between: int) -> bool:
        """Set time between pulses in n-plet (1-255ms)"""
        if time_between < 1 or time_between > 255:
            raise ValueError("Time between must be between 1 and 255, was {}".format(time_between))

        res = self.send_command(self.command_builder('ST', time_between, 1))
        if res:
            self.time_between = time_between

        return res

    def set_delay(self, delay: int) -> bool:
        """Set delay after trigger (0ms - 16777215ms)"""
        if delay < 0 or delay > 16777215:
            raise ValueError("Delay must be between 0 and 16777215, was {}".format(delay))

        res = self.send_command(self.command_builder('SD', delay, 4))
        if res:
            self.delay = delay

        return res

    def trigger_pulse_generator(self) -> bool:
        """Sets pulse generators either active or not active"""
        res = self.send_command(self.to_bytes_(">T<"))
        if res:
            self.pulse_generator_triggered = not self.pulse_generator_triggered

        return res

    def read_battery(self) -> int:
        """Read remaining battery capacity"""
        cmd = ">SOC<"
        self.serial_.write(self.to_bytes_(cmd))

        logging.debug(cmd)

        res = self.read_response_()
        if res.startswith('>SOC;'):
            battery_level = int.from_bytes(self.to_bytes_(res[-2]), byteorder="big")
            self.battery_state = battery_level
            return battery_level
        else:
            return -1

    # long protocol

    def set_repetition_rate(self, num: int = 50) -> bool:
        """Set n-plet repetition rate (1-400)"""
        if num < 1 or num > 400:
            raise ValueError("Repetition rate (num) must be between 1-400, was {}".format(num))

        res = self.send_command(self.command_builder('SF', num, 2))
        if res:
            self.repetition_rate = num
        return res

    def set_pulse_width(self, widths: List[int]):
        """Set pulse width for every pulse in n-plet (50 - 1000 microseconds)"""
        if not all(50 <= i <= 1000 or i == 0 for i in widths):
            raise ValueError("Pulse widths must be between 50 and 1000")

        w_pad = widths + (24-len(widths))*[0]
        cmd = self.to_bytes_('>PW;')

        for idx, num in enumerate(w_pad):
            cmd += num.to_bytes(2, byteorder='big')

        cmd += self.to_bytes_('<')

        res = self.send_command(cmd)
        if res:
            self.pulse_widths = widths

        return res

    def set_amplitude(self, amplitudes: List[int]) -> bool:
        """Set amplitude of the pulses in n-plet (0 - 1000) unit: w/10 or w/100"""
        if not all(0 <= i <= 1000 for i in amplitudes):
            raise ValueError("Pulse amplitudes must be between 0 and 1000")

        a_pad = amplitudes + (24 - len(amplitudes)) * [0]
        cmd = self.to_bytes_('>SC;')

        for idx, num in enumerate(a_pad):
            cmd += num.to_bytes(2, byteorder='big')

        cmd += self.to_bytes_('<')

        res = self.send_command(cmd)
        if res:
            self.pulse_amplitudes = amplitudes

        return res

    def set_mode(self, mode: str) -> bool:
        """Set mode to either unipolar or bipolar"""
        if mode == 'unipolar':
            cmd = '>MUX;OFF<'
        elif mode == 'bipolar':
            cmd = '>MUX;ON<'
        else:
            raise ValueError('No mode named: {}, use value unipolar or bipolar'.format(mode))

        res = self.send_command(self.to_bytes_(cmd))
        if res:
            self.mode = mode

        return res

    def set_common_electrode(self, electrode: str) -> bool:
        """Set common electrode to anode or cathode, unipolar only"""
        if electrode.lower() == 'anode':
            e = 'A'
        elif electrode.lower() == 'cathode':
            e = 'C'
        else:
            raise ValueError('No option: {}, use value "anode" or "cathode" for cathode'.format(electrode))
        cmd = '>ASYNC;{}<'.format(e)

        res = self.send_command(self.to_bytes_(cmd))
        if res:
            self.common_electrode = electrode
            self.is_short_protocol = False

        return res

    def set_pulses_unipolar(self, output_channels: List, value_type: str = 'list') -> bool:
        """Set n-plet pulses and output channels for each pulse, unipolar only"""
        if len(output_channels) > 24:
            raise ValueError('Too many pulses defined. Maximum length for the output channels is 24, was {}'
                             .format(len(output_channels)))

        cmd = self.to_bytes_('>SA;')
        if value_type == "hex":
            padded_output = output_channels + (24 - len(output_channels)) * ['000000']
            for idx, channels in enumerate(padded_output):
                value = bytes(bytearray.fromhex(channels))
                cmd += value
        else:
            padded_output = output_channels + (24 - len(output_channels)) * [[0]]
            for i, channels in enumerate(padded_output):
                value = 0
                for j, c in enumerate(channels):
                    if c == 0:
                        continue
                    value += pow(2, c-1)
                cmd += value.to_bytes(3, byteorder='big')

        cmd += self.to_bytes_('<')

        res = self.send_command(cmd)
        if res:
            self.output_channels = output_channels

        return res

    def set_pulses_bipolar(self, channel_pairs: List[Tuple], value_type: str = 'list') -> bool:
        """Set n-plet pulses and output channels cathode/anode pairs for each pulse, bipolar only"""
        if len(channel_pairs) > 24:
            raise ValueError('Too many pulses defined. Maximum length for the channels pairs is 24, was {}'
                             .format(len(channel_pairs)))

        cmd = self.to_bytes_(">CA;")
        if value_type == 'hex':
            padded_pairs = channel_pairs + (24 - len(channel_pairs))*[('000000', '000000')]
            for x, y in padded_pairs:
                cathode = bytes(bytearray.fromhex(x))
                anode = bytes(bytearray.fromhex(y))
                cmd += cathode
                cmd += anode
        else:
            padded_pairs = channel_pairs + (24 - len(channel_pairs)) * [([0], [0])]
            for x, y in padded_pairs:
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

        res = self.send_command(cmd)
        if res:
            self.channel_pairs = channel_pairs

        return res

    # Short protocol mode

    def set_common_electrode_short(self, electrode) -> bool:
        if electrode.lower() == 'anode':
            e = 'A'
        elif electrode.lower() == 'cathode':
            e = 'C'
        else:
            raise ValueError('No option: {}, use value "anode" or "cathode" for cathode'.format(electrode))
        cmd = '>SYNC;{}<'.format(e)

        res = self.send_command(self.to_bytes_(cmd))

        if res:
            self.common_electrode = electrode
            self.is_short_protocol = True

        return res

    def set_output_channel_activity(self, output_channels, repetition_rate: int, value_type: str = 'list') -> bool:
        if repetition_rate < 1 or repetition_rate > 255:
            raise ValueError("Repetition rate must be between 1 and 255 in short mode, was {}".format(repetition_rate))
        if value_type == 'hex' and len(output_channels) != 6:
            raise ValueError('Output channels is not of a correct format, must be 6 character hex number')
        if value_type != 'hex' and len(output_channels) > 24:
            raise ValueError('Too many output channels defined. Max is 24, was {}'.format(len(output_channels)))

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

        res = self.send_command(cmd)
        if res:
            self.output_channels = output_channels
            self.repetition_rate = repetition_rate

        return res
