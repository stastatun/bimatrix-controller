from typing import Callable

from controller import Controller

import py_cui

import logging


class TUI:
    def __init__(self, device: Controller):

        logging.basicConfig(filename="ui_log.log", level=logging.DEBUG)

        self.labels = [
            "Current range: {}, Voltage: {}, Mode: {}",
            "DC/DC Converter: {}",
            "Pulse generation: {}",
            "Number of n-plets: {}",
            "Time between pulses: {}ms",
            "N-plet repetition rate: {}pps",
            "Delay after trigger: {}ms",
            "Pulse widths: {} (unit: μs)",
            "Pulse amplitudes: {} (unit: mA)",
            "Output channels (unipolar): {}",
            "Channel pairs (bipolar): {}",
            "Battery: {}%",
            "Common electrode: {}"
        ]
        self.device = device
        self.master = py_cui.PyCUI(30, 10)
        self.master.set_title("Bimatrix controller (Battery: {}%)".format(device.read_battery()))

        span = 5

        self.stats = self.master.add_block_label(self.labels[0].format(
            device.current_range, device.voltage, device.mode),
            0, 0, column_span=span, center=False)
        self.converter = self.master.add_block_label(self.labels[1].format(self._bool_to_string(
            device.pulse_generator_dc_converter_status)),
            1, 0, column_span=span, center=False)
        self.pulse_generation = self.master.add_block_label(self.labels[2].format(self._bool_to_string(
            device.pulse_generator_triggered)),
            2, 0, column_span=span, center=False)
        self.num_nplet = self.master.add_block_label(self.labels[3].format(
            device.num_nplets if device.num_nplets != 0 else "0 (Infinite)"),
            3, 0, column_span=span, center=False)
        self.electrode = self.master.add_block_label(self.labels[12].format(device.common_electrode),
                                                        0, 5, column_span=span, center=False)
        self.time_between = self.master.add_block_label(self.labels[4].format(device.time_between),
                                                        1, 5, column_span=span, center=False)
        self.repetition_rate = self.master.add_block_label(self.labels[5].format(device.repetition_rate),
                                                        2, 5, column_span=span, center=False)
        self.delay = self.master.add_block_label(self.labels[6].format(device.delay),
                                                 3, 5, column_span=span, center=False)
        self.widths = self.master.add_block_label(self.labels[7].format(device.pulse_widths),
                                                  4, 0, column_span=span, center=False)
        self.amplitudes = self.master.add_block_label(self.labels[8].format(
            self._calculate_amplitudes(device.pulse_amplitudes, device.mode)),
            5, 0, column_span=span, center=False)
        self.outputs = self.master.add_block_label(self.labels[9].format(device.output_channels),
                                                   6, 0, column_span=span, center=False)
        self.pairs = self.master.add_block_label(self.labels[10].format(device.channel_pairs),
                                                 7, 0, column_span=span, center=False)

        self.command_prompt = self.master.add_text_box("Command: ", 29, 0, column_span=10)
        command_list1 = self.master.add_scroll_menu("Commands", 8, 0, row_span=8, column_span=10)
        commands1 = [
            "battery: Update battery information",
            "mode <mode>: Set stimulatio mode (unipolar or bipolar)",
            "range <range>: ",
            "voltage <voltage>: Set voltage in Volts (70-150)",
            "dc: trigger dc converter, dc <status>: set dc converter on or off",
            "trigger: trigger pulse generator (activate stimulation)",
            "nplets <num>: set the number of n-plets to be generated (0 [Infinity] - 16777215)",
            "time_between <time>: set time between pulses in ms (1-255)",
            "repetition_rate <rate>: set repetition rate in nplets-per-second (1-400)",
            "delay <delay>: set stimulation delay after trigger in ms (0 - 16777215)",
            "pulse_widths [widths]: set width for every pulse, each width separated by space",
            "pulse_amplitudes [amplitudes]: set amplitude for every pulse, list of comma separated values. " +
            "high: x/10 mA, low: x/100 mA",
            "output [channels]: list of channels in format x,y,z;i,j,k",
            "pairs [channels]: list of channels pairs in format x;y x;y",
            "common_electrode: set common electrode to cathode or anode"

        ]
        command_list1.add_item_list(commands1)
        self.command_history = self.master.add_scroll_menu("Command history", 16, 0, row_span=12, column_span=10)

        self.command_prompt.add_key_command(py_cui.keys.KEY_ENTER, self.send_command)

        self.master.start()

    @staticmethod
    def _bool_to_string(status: bool) -> str:
        return "On" if status else "Off"

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
            new.append(i / div)
        return new

    def _input_func(self, command: str, params: list, device_func: Callable,
                    set_title: Callable, title_base: str, device: Controller, format_params: list):
        try:
            succ = device_func(*params)
            if succ:
                new_list = [getattr(device, i) for i in format_params]
                formatted_list = []
                for i in new_list:
                    if type(i) is bool:
                        formatted_list.append("On" if i else "Off")
                    else:
                        formatted_list.append(i)
                set_title(title_base.format(*formatted_list))
                out = command
            else:
                out = "Command: {}, failed for unknown reason".format(command)
        except ValueError as e:
            logging.debug(e)
            out = "Error: {}".format(e)

        return out

    def _parse_input(self, text: str) -> str:
        out = text.lower()
        parts = text.split()
        cmd = parts[0]
        params = parts[1:]
        if cmd == 'battery':
            self.device.read_battery()
            self.master.set_title("Bimatrix controller (Battery: {}%)".format(self.device.battery_state))
        elif cmd == 'mode':
            if len(params) == 1:
                out = self._input_func(out, params, self.device.set_mode,
                                       self.stats.set_title, self.labels[0], self.device,
                                       ["current_range", "voltage", "mode"])
            else:
                out = "Mode command requires one parameter"
        elif cmd == 'range':
            if len(params) == 1:
                out = self._input_func(out, params, self.device.set_current_range,
                                       self.stats.set_title, self.labels[0], self.device,
                                       ["current_range", "voltage", "mode"])
            else:
                out = "Current range command requires one parameter"
        elif cmd == 'voltage':
            if len(params) == 1:
                out = self._input_func(out, params, self.device.set_voltage,
                                       self.stats.set_title, self.labels[0], self.device,
                                       ["current_range", "voltage", "mode"])
            else:
                out = "Voltage command requires one parameter"
        elif cmd == 'dc':
            if len(params) == 0:
                out = self._input_func(out, params, self.device.toggle_pulse_generator,
                                       self.converter.set_title, self.labels[1], self.device,
                                       ["pulse_generator_dc_converter_status"])
            elif len(params) == 1:
                params = [params[0].lower() == 'on']
                out = self._input_func(out, params, self.device.set_pulse_generator,
                                       self.converter.set_title, self.labels[1], self.device,
                                       ["pulse_generator_dc_converter_status"])
            else:
                out = "Dc: too many parameters, expected 0 or 1"
        elif cmd == 'trigger':
            if len(params) == 0:
                out = self._input_func(out, params, self.device.trigger_pulse_generator,
                                       self.pulse_generation.set_title, self.labels[2], self.device,
                                       ["pulse_generator_triggered"])
            else:
                out = "Trigger: Too many parameters, expected 0"
        elif cmd == 'nplets':
            if len(params) == 1:
                new_params = [int(params[0])]
                out = self._input_func(out, new_params, self.device.set_num_nplets,
                                       self.num_nplet.set_title, self.labels[3], self.device,
                                       ["num_nplets"])
            else:
                out = "Number of n-plets: incorrent number of parameters, expected one"
        elif cmd == 'time_between':
            if len(params) == 1:
                new_params = [int(params[0])]
                out = self._input_func(out, new_params, self.device.set_time_between,
                                       self.time_between.set_title, self.labels[4], self.device,
                                       ["time_between"])
            else:
                out = "Time between: incorrent number of parameters, expected one"
        elif cmd == 'repetition_rate':
            if len(params) == 1:
                new_params = [int(params[0])]
                out = self._input_func(out, new_params, self.device.set_repetition_rate,
                                       self.repetition_rate.set_title, self.labels[5], self.device,
                                       ["repetition_rate"])
            else:
                out = "Repetition rate: incorrent number of parameters, expected one"
        elif cmd == 'delay':
            if len(params) == 1:
                new_params = [int(params[0])]
                out = self._input_func(out, new_params, self.device.set_delay,
                                       self.delay.set_title, self.labels[6], self.device,
                                       ["delay"])
            else:
                out = "Delay: incorrent number of parameters, expected one"
        elif cmd == 'pulse_widths':
            if 0 <= len(params) <= 24:
                new_params = [[int(i) for i in params]]
                out = self._input_func(out, new_params, self.device.set_pulse_width,
                                       self.widths.set_title, self.labels[7], self.device,
                                       ["pulse_widths"])
            else:
                out = "pulse_widths: incorrect number of parameters"
        elif cmd == 'pulse_amplitudes':
            if 0 <= len(params) <= 24:
                new_params = [[int(i) for i in params]]
                out = self._input_func(out, new_params, self.device.set_amplitude,
                                       self.amplitudes.set_title, self.labels[8], self.device,
                                       ["pulse_amplitudes"])
            else:
                out = "pulse_amplitudes: incorrect number of parameters"
        elif cmd == 'output':
            if 0 <= len(params) <= 24:
                new_params = []
                for pulse in params:
                    channels = pulse.split(',')
                    new_channels = [int(i) for i in channels]
                    new_params.append(new_channels)
                out = self._input_func(out, [new_params], self.device.set_pulses_unipolar,
                                       self.outputs.set_title, self.labels[9], self.device,
                                       ["output_channels"])
            else:
                out = "outputs: incorrect number of parameters"
        elif cmd == 'pairs':
            if 0 <= len(params) <= 24:
                new_params = []
                for pulse in params:
                    pair = pulse.split(';')

                    p1 = [int(i) for i in pair[0].split(',')]
                    p2 = [int(i) for i in pair[1].split(',')]
                    new_params.append((p1, p2))
                logging.debug(new_params)
                out = self._input_func(out, [new_params], self.device.set_pulses_bipolar,
                                       self.pairs.set_title, self.labels[10], self.device,
                                       ["channel_pairs"])
            else:
                out = "pairs: incorrect number of parameters"
        elif cmd == 'electrode':
            if len(params) == 1:
                out = self._input_func(out, params, self.device.set_common_electrode,
                                       self.electrode.set_title, self.labels[12], self.device,
                                       ["common_electrode"])
            else:
                out = "Electrode: incorrent number of parameters, expected one"
        else:
            out = "Command not found: {}".format(out)
        return out

    def send_command(self):
        text = self.command_prompt.get()
        out = self._parse_input(text)
        self.command_prompt.clear()
        self.command_history.add_item(out)
