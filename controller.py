import serial
import logging


class Controller:

    def __init__(self, device, baud_rate=921600, data_bits=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                 stop_bits=serial.STOPBITS_ONE, rtscts=True, logging_level=logging.WARNING):
        """ Initialize the controller"""

        logging.basicConfig(filename="", level=logging_level)
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

    def command_builder(self, command: str, param: int, num_bytes: int) -> bool:
        formatted = ">{};".format(command)
        cmd = bytes(formatted, 'ascii')
        cmd += param.to_bytes(num_bytes, byteorder='big')
        cmd += bytes('<', 'ascii')

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

        logging.debug(cmd)

        self.serial_.write(self.to_bytes_(cmd))
        res = self.read_response_()

        return self.res_to_bool_(res)

    def set_voltage(self, voltage: int) -> bool:
        """Sets voltage in volts (value between 70-150)"""
        return self.command_builder("SV", voltage, 1)

    def set_pulse_generator(self, status: bool) -> bool:
        """Set pulse DC/DC pulse generator on or off

        :param status: Status of pulse generator

        :return: True if setting pulse generator succeeded.
        """
        if status:
            cmd = ">ON<"
        else:
            cmd = ">OFF<"

        logging.debug(cmd)

        self.serial_.write(self.to_bytes_(cmd))
        res = self.read_response_()

        return self.res_to_bool_(res)

    def set_num_nplets(self, num: int) -> bool:
        """Set the number of n-plets to be generated (0 - 16777215)"""
        return self.command_builder('SN', num, 4)

    def set_time_between(self, time_between: int) -> bool:
        """Set time between pulses in n-plet (1-255ms)"""
        return self.command_builder('ST', time_between, 1)

    def set_delay(self, delay):
        """Set delay after trigger"""
        pass

    def trigger_pulse_generator(self):
        """Sets pulse generators either active or not active"""
        pass

    def read_battery(self):
        """Read remaining battery capacity"""
        cmd = ">SOC<"
        cmd = bytes(cmd, 'utf-8')
        self.serial_.write(cmd)

        logging.debug(cmd)

        res = self.read_response_()
        battery_level = int.from_bytes(bytes(res[-2], 'ascii'), byteorder="big")
        return battery_level

    # long protocol

    def set_repetition_rate(self, num):
        """Set n-plet repetition rate"""
        pass

    def set_pulse_width(self, width):
        """Set pulse width for every pulse in n-plet"""
        pass

    def set_amplitude(self, amplitude):
        """Set amplitude of the pulses in n-plet"""
        pass

    def set_mode(self, mode):
        """Set mode to either unipolar or bipolar"""
        pass

    def set_common_electrode(self, electrode):
        """Set common electrode to anode or cathode, unipolar only"""
        pass

    def set_pulses_unipolar(self, output_channels):
        """Set n-plet pulses and output channels for each pulse, unipolar only"""
        pass

    def set_pulses_bipolar(self, output_cathodes, output_anodes):
        """Set n-plet pulses and output channels cathode/anode pairs for each pulse, bipolar only"""
        pass
