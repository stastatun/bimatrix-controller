import serial


class Controller:

    def __init__(self, device, baud_rate=921600, data_bits=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                 stop_bits=serial.STOPBITS_ONE, rtscts=True):
        """ Initialize the controller"""
        try:
            self.serial_ = serial.Serial(device, baud_rate, timeout=5, parity=parity, rtscts=rtscts, stopbits=stop_bits,
                                         bytesize=data_bits)
        except serial.SerialException:
            import os
            print("Error connecting")
            os.exit(0)

    def __del__(self):
        self.serial_.close()

    def set_current_range(self, current_range):
        """Sets the current range H for high (up to 100mA) and L for Low (up to 10mA)"""
        pass

    def set_voltage(self, voltage):
        """Sets voltage in volts (value between 70-150)"""
        pass

    def set_pulse_generator(self, is_on):
        """Set pulse generator on or off"""
        pass

    def set_num_nplets(self, num):
        """Set the number of n-plets to be generated"""
        pass

    def set_time_between(self, time_between):
        """Set time between pulses in n-plet"""
        pass

    def set_delay(self, delay):
        """Set delay after trigger"""
        pass

    def trigger_pulse_generator(self):
        """Sets pulse generators either active or not active"""
        pass

    def read_batter(self):
        """Read remaining battery capacity"""
        pass

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
