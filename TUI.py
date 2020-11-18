from controller import Controller

import py_cui

import logging

class TUI:
    def __init__(self, device: Controller):

        logging.basicConfig(filename="ui_log.log", level=logging.DEBUG)

        self.labels = [
            "Current range: {}, Voltage: {}, Mode: {}"
        ]
        self.device = device
        self.master = py_cui.PyCUI(30, 10)

        span = 10

        self.stats = self.master.add_block_label(self.labels[0].format(
            device.current_range, device.voltage, device.mode),
            0, 0, column_span=span, center=False)
        self.converter = self.master.add_block_label("DC/DC Converter: {}".format(
            "On" if device.pulse_generator_dc_converter_status else "Off"),
            1, 0, column_span=span, center=False)
        self.master.add_block_label("Pulse generation: {}".format(
            "On" if device.pulse_generator_dc_converter_status else "Off"),
            2, 0, column_span=span, center=False)
        self.master.add_block_label("Number of n-plets: {}".format(
            device.num_nplets if device.num_nplets != 0 else "0 (Infinite)"),
            3, 0, column_span=span, center=False)
        self.master.add_block_label("Time between pulses: {}ms".format(device.time_between),
                             4, 0, column_span=span, center=False)
        self.master.add_block_label("N-plet repetition rate: {}pps".format(device.repetition_rate),
                             5, 0, column_span=span, center=False)
        self.master.add_block_label("Delay after trigger: {}ms".format(device.delay),
                             6, 0, column_span=span, center=False)
        self.master.add_block_label("Pulse widths: {} (unit: μs)".format(device.pulse_widths),
                             7, 0, column_span=span, center=False)
        self.master.add_block_label("Pulse amplitudes: {} (unit: mA)".format(
            self._calculate_amplitudes(device.pulse_amplitudes, device.mode)),
            8, 0, column_span=span, center=False)
        self.master.add_block_label("Output channels (unipolar): {}".format(device.output_channels),
                             9, 0, column_span=span, center=False)
        self.master.add_block_label("Channel pairs (bipolar): {}".format(device.channel_pairs),
                             10, 0, column_span=span, center=False)
        self.battery = self.master.add_block_label("Battery: {}%".format(device.battery_state), 11, 0, column_span=span,
                                       center=False)

        self.command_prompt = self.master.add_text_box("Command: ", 29, 0, column_span=10)
        command_list1 = self.master.add_scroll_menu("Commands", 12, 0, row_span=9, column_span=5)
        commands1 = [
            "battery: Update battery information",
            "mode <mode>: Set stimulatio mode (unipolar or bipolar)",
            "range <range>: ",
            "voltage <voltage>: Set voltage (70-150)"
        ]
        command_list1.add_item_list(commands1)
        command_list2 = self.master.add_scroll_menu("Commands", 12, 5, row_span=9, column_span=5)
        self.command_history = self.master.add_scroll_menu("Command history", 21, 0, row_span=8, column_span=10)

        self.command_prompt.add_key_command(py_cui.keys.KEY_ENTER, self.send_command)

        self.master.start()

    @staticmethod
    def _calculate_amplitudes(amplitudes: list, mode='low') -> list:
        if mode == 'low':
            div = 100
        elif mode == 'high':
            div = 10
        else:
            return amplitudes

        new = []
        for i in amplitudes:
            new.append(i/div)
        return new

    def _parse_input(self, text: str) -> str:
        out = text.lower()
        parts = text.split()
        cmd = parts[0]
        if cmd == 'battery':
            self.device.read_battery()
            self.battery.set_title("Battery: {}%".format(self.device.battery_state))
        elif cmd == 'mode':
            try:
                mode = parts[1]
                succ = self.device.set_mode(mode)
                if succ:
                    self.stats.set_title(self.labels[0].format(
                        self.device.current_range, self.device.voltage, self.device.mode))
                else:
                    out = "Command: {}, failed for unknown reason"
            except ValueError as e:
                logging.debug(e)
                out = "Error: {}".format(e)
            except IndexError:
                out = "Mode command requires one parameter"
        elif cmd == 'range':
            try:
                current_range = parts[1]
                succ = self.device.set_current_range(current_range)
                if succ:
                    self.stats.set_title(self.labels[0].format(
                        self.device.current_range, self.device.voltage, self.device.mode))
            except ValueError as e:
                logging.debug(e)
                out = "Error: {}".format(e)
            except IndexError:
                out = "Range command requires one parameter"
        elif cmd == 'voltage':
            try:
                voltage = parts[1]
                succ = self.device.set_voltage(int(voltage))
                if succ:
                    self.stats.set_title(self.labels[0].format(
                        self.device.current_range, self.device.voltage, self.device.mode))
            except ValueError as e:
                logging.debug(e)
                out = "Error: {}".format(e)
            except IndexError:
                out = "Voltage command requires one parameter"
        else:
            out = "Command not found: {}".format(out)

        return out

    def send_command(self):
        text = self.command_prompt.get()
        out = self._parse_input(text)
        self.command_prompt.clear()
        self.command_history.add_item(out)