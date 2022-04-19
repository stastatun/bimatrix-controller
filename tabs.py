from PyQt6.QtWidgets import QWidget, QFormLayout, QLineEdit, QPushButton, QLabel
from PyQt6.QtCore import QThread, pyqtSignal, QObject
import time
import xlsxwriter
from datetime import datetime

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(list)

    def __init__(self, pairs, between):
        """
        QWorker for sweeping without logging, GUI hangs if this is done w/o a thread
        """
        # TODO muuttujanimet
        super().__init__()
        self.pairs = pairs
        self.between = between

    def run(self):
        for pair in self.pairs:
            self.progress.emit(pair)
            time.sleep(self.between)
        self.finished.emit()

class WorkerInt(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, pairs, between):
        """
        QWorker for sweeping without logging, GUI hangs if this is done w/o a thread
        Some parameters are passed to controller as int instead of list,
        need another Worker for this
        """
        super().__init__()
        self.pairs = pairs
        self.between = between

    def run(self):
        for pair in self.pairs:
            self.progress.emit(pair)
            time.sleep(self.between)
        self.finished.emit()

class ChannelSwipe(QWidget):
    def __init__(self, channels, device, handmap):
        super().__init__()
        self.device = device
        self.layout = QFormLayout()
        # settings
        self.voltage = QLineEdit("150")
        self.num_nplets = QLineEdit("10")
        self.amplitudes = QLineEdit("1.5")
        self.widths = QLineEdit("1000")
        self.freq = QLineEdit("50")
        self.between = QLineEdit("1.5")
        #self.between = QLineEdit()
        self.layout.addRow("Voltage (V)", self.voltage)
        self.layout.addRow("Pulse repetitions", self.num_nplets)
        self.layout.addRow("Amplitude (mA)", self.amplitudes)
        self.layout.addRow("Frequency (Hz)", self.freq)
        self.layout.addRow("Pulse width (us)", self.widths)
        self.layout.addRow("Time between stims (s)", self.between)
        self.apply = QPushButton("Apply settings")
        self.apply.clicked.connect(self.apply_settings)
        self.layout.addWidget(self.apply)

        self.settings_status = QLabel("")
        self.layout.addWidget(self.settings_status)
        
        self.sweep = QPushButton("Sweep")
        self.sweep.clicked.connect(self.trigger_sweep)
        self.layout.addWidget(self.sweep)

        self.stim_status = QLabel("")
        self.layout.addWidget(self.stim_status)

        self.stop_stim = QPushButton("Stop stimulation")
        self.stop_stim.clicked.connect(lambda: abort_serial(self.device))
        self.layout.addWidget(self.stop_stim)

        self.excel_file_id = QLineEdit("")
        self.layout.addRow("Electrode position ID", self.excel_file_id)

        self.setLayout(self.layout)

        self.channels = channels
        self.tofile = ""

        self.handmap = handmap
        self.handmap.scene.stims.connect(self.excel_stim)
        self.excel_stim_in_progress = False

    def excel_stim(self, stims):
        # doesn't do anything if trigger_sweep hasn't been connected
        if self.excel_stim_in_progress:
            # get pair from selected anode/cathode pairs, check that it exists
            if self.current_pairs:
                current_pair = self.current_pairs.pop()
                self.stim_status.setText(f"Currently at {current_pair}")
                res = True
                res = self.device.set_pulses_bipolar(current)
                res = self.device.trigger_pulse_generator()
                if not res:
                    self.stim_status.setText(f"Stimulation failed at {pair}")
                self.excel_results.append([self.previous_excel_stim, stims])
                self.previous_excel_stim = current_pair
            # write last result
            elif (not self.current_pairs) and self.previous_excel_stim:
                self.excel_results.append([self.previous_excel_stim, stims])
                self.previous_excel_stim = None
                self.excel_stim_in_progress = False
                self.save_results_file()
                self.stim_status.setText(f"Stimulation complete!")
                
    def save_results_file(self):
        """ REAL SPAGHETTI HOURS"""

        fname = datetime.now().isoformat()[0:-7].replace(":","")
        fname += "_" + self.excel_file_id.text()
        workbook = xlsxwriter.Workbook(f"./results/{fname}.xlsx")
        worksheet = workbook.add_worksheet()
        labels = ["voltage", "nplets", "amplitude", "frequency", "width", "cathode", "anode",
                  "K1", "K2", "KE", "KK", "KN", "KP", "KPE", "KS1", "KS2", "KSE", "KSK",
                  "KSN", "KSP", "KSPE", "NO"]
        label_dict = {}
        start = 7
        for lbl in labels[7:]:
            label_dict[lbl] = start
            start += 1
        col = 0
        for label in labels:
            worksheet.write(0, col, label)
            col += 1
        row = 1
        for result in self.excel_results[1:]:
            worksheet.write(row, 0, int(self.voltage.text()))
            worksheet.write(row, 1, int(self.num_nplets.text()))
            worksheet.write(row, 2, int(float(self.amplitudes.text()) * 100))
            worksheet.write(row, 3, int(self.freq.text()))
            worksheet.write(row, 4, int(self.widths.text()))
            worksheet.write(row, 5, result[0][0][0][0])
            worksheet.write(row, 6, result[0][0][1][0])
            for stimms in result[1]:
                if stimms:
                    worksheet.write(row, label_dict[stimms], "X")
            row += 1
        workbook.close()
            

    def apply_settings(self):
        res = True
        res = self.device.set_voltage(int(self.voltage.text()))
        res = self.device.set_num_nplets(int(self.num_nplets.text()))
        res = self.device.set_amplitude([int(float(self.amplitudes.text()) * 100)])
        res = self.device.set_repetition_rate(int(self.freq.text()))
        res = self.device.set_pulse_width([int(self.widths.text())])
        if not res:
            self.settings_status.setText("Settings failed")
        else:
            self.settings_status.setText("Settings OK")
    
    def single_stim(self, pair):
        """
        perform single stimulation when QWorker emits a signal
        """
        self.stim_status.setText(f"Currently at {pair}")
        res = True
        res = self.device.set_pulses_bipolar(pair)
        res = self.device.trigger_pulse_generator()
        if not res:
            self.stim_status.setText(f"Stimulation failed at {pair}")

    def trigger_sweep(self):
        """
        Loops over all selected electrode pairs (both anode and cathode is tried for one pair)
        If self.between is selected, just does the run in a thread so GUI doesn't hang
        """
        pairs = self.generate_combinations()
        if not pairs:
            self.stim_status.setText("Please select at least one electrode pair")
            return

        if self.between.text():
            self.thread = QThread()
            self.worker = Worker(pairs, float(self.between.text()))
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.progress.connect(self.single_stim)
            self.thread.start()
        # waits for signals from handmap to stimulate
        else:
            # Copy generated pairs to current pairs
            self.current_pairs = pairs.copy()
            # Save another to map the results XD
            self.current_pairs_saved = pairs.copy()
            # create empty list for values sent from HandMap
            self.previous_excel_stim = None
            self.excel_results = []
            self.excel_stim_in_progress = True
    
    def generate_combinations(self):
        """
        Generates electrode pairs for selected cathodes and anodes
        """
        pairs = []
        cathodes, anodes = self.channels.get_active_channels()

        for i in range(len(cathodes)):
            for j in range(len(anodes)):
                pairs.append([([cathodes[i]],[anodes[j]])])
        return pairs

class AmplitudeSwipe(QWidget):
    def __init__(self, channels, device, handmap):
        super().__init__()
        self.device = device
        self.layout = QFormLayout()
        # settings
        self.voltage = QLineEdit("150")
        self.num_nplets = QLineEdit("10")
        self.freq = QLineEdit("50")
        self.widths = QLineEdit("1000")
        self.between = QLineEdit("1.5")
        self.layout.addRow("Voltage (V)", self.voltage)
        self.layout.addRow("Pulse repetitions", self.num_nplets)
        self.layout.addRow("Frequency (Hz)", self.freq)
        self.layout.addRow("Pulse width (us)", self.widths)
        self.layout.addRow("Time between stims (s)", self.between)
        self.apply = QPushButton("Apply settings")
        self.apply.clicked.connect(self.apply_settings)
        self.layout.addWidget(self.apply)

        self.settings_status = QLabel("")
        self.layout.addWidget(self.settings_status)
 
        self.channels = channels

        self.start = QLineEdit("1")
        self.end = QLineEdit("2")
        self.step = QLineEdit("0.1")
        self.layout.addRow("Starting amp (mA)", self.start)
        self.layout.addRow("Ending amp (mA)", self.end)
        self.layout.addRow("Step (mA)", self.step)
        self.sweep = QPushButton("Sweep")
        self.sweep.clicked.connect(self.trigger_sweep)
        self.layout.addWidget(self.sweep)

        self.stim_status = QLabel("")
        self.layout.addWidget(self.stim_status)

        self.setLayout(self.layout)
        self.tofile = ""

    def apply_settings(self):
        """
        Set settings according to QLineEdits
        """
        res = True
        res = self.device.set_voltage(int(self.voltage.text()))
        res = self.device.set_num_nplets(int(self.num_nplets.text()))
        res = self.device.set_repetition_rate(int(self.freq.text()))
        res = self.device.set_pulse_width([int(self.widths.text())])
        # first element of active channels cathode, second anode
        cathodes, anodes = self.channels.get_active_channels()
        try:
            self.electrodes = [cathodes[0], anodes[0]]
            electrodes = [([self.electrodes[0]], [self.electrodes[1]])]
            res = self.device.set_pulses_bipolar(electrodes)
            if not res:
                self.settings_status.setText("Settings failed")
            else:
                self.settings_status.setText("Settings OK")
        except:
            self.stim_status.setText("Please select a cathode and an anode")

    def single_stim(self, amplitude):
        """
        perform single stimulation when QWorker emits a signal
        """
        self.stim_status.setText(f"Currently at {amplitude}")
        res = True
        res = self.device.set_amplitude([amplitude])
        res = self.device.trigger_pulse_generator()
        if not res:
            self.stim_status.setText(f"Stimulation failed at {pair}")

    def trigger_sweep(self):
        """
        Does amplitude swipe from starting amp to ending amp with step of self.step
        Sweep is done with intervals of self.between
        If self.between is none, function waits for a key press after each stimulation, and finally writes the results in a file
        """

        self.current_amp = int(float(self.start.text()) * 100)
        ending_amp = int(float(self.end.text()) * 100)
        step_amp = int(float(self.step.text()) * 100)
        self.update()

        amplitudes = []
        for amp in range(self.current_amp, ending_amp, step_amp):
            amplitudes.append([amp])

        if self.between.text():
            self.thread = QThread()
            self.worker = Worker(amplitudes, float(self.between.text()))
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.progress.connect(self.single_stim)
            self.thread.start()
 
class FrequencySwipe(QWidget):
    def __init__(self, channels, device, handmap):
        super().__init__()
        self.device = device
        self.layout = QFormLayout()
        # settings
        self.voltage = QLineEdit("150")
        self.num_nplets = QLineEdit("10")
        self.amplitudes = QLineEdit("1")
        self.widths = QLineEdit("1000")
        self.between = QLineEdit("1.5")
        self.layout.addRow("Voltage (V)", self.voltage)
        self.layout.addRow("Pulse repetitions", self.num_nplets)
        self.layout.addRow("Amplitude (mA)", self.amplitudes)
        self.layout.addRow("Pulse width (us)", self.widths)
        self.layout.addRow("Time between stims (s)", self.between)
        self.apply = QPushButton("Apply settings")
        self.apply.clicked.connect(self.apply_settings)
        self.layout.addWidget(self.apply)

        self.settings_status = QLabel("")
        self.layout.addWidget(self.settings_status)

        # freq sweep
        self.start = QLineEdit("30")
        self.end = QLineEdit("60")
        self.step = QLineEdit("5")
        self.layout.addRow("Starting frequency (Hz)", self.start)
        self.layout.addRow("Ending frequency (Hz)", self.end)
        self.layout.addRow("Step (Hz)", self.step)
        self.sweep = QPushButton("Sweep")
        self.sweep.clicked.connect(self.trigger_sweep)
        self.layout.addWidget(self.sweep)

        self.stim_status = QLabel("")
        self.layout.addWidget(self.stim_status)


        self.setLayout(self.layout)

        self.channels = channels
        self.tofile = ""

    def apply_settings(self):
        res = True
        res = self.device.set_voltage(int(self.voltage.text()))
        res = self.device.set_num_nplets(int(self.num_nplets.text()))
        res = self.device.set_amplitude([int(float(self.amplitudes.text()) * 100)])
        res = self.device.set_pulse_width([int(self.widths.text())])
        cathodes, anodes = self.channels.get_active_channels()
        try:
            self.electrodes = [cathodes[0], anodes[0]]
            electrodes = [([self.electrodes[0]], [self.electrodes[1]])]
            res = self.device.set_pulses_bipolar(electrodes)
            if not res:
                self.settings_status.setText("Settings failed")
            else:
                self.settings_status.setText("Settings OK")
        except:
            self.stim_status.setText("Please select a cathode and an anode")

    def single_stim(self, frequency):
        """
        perform single stimulation when QWorker emits a signal
        """
        print(frequency)
        self.stim_status.setText(f"Currently at {frequency}")
        res = True
        res = self.device.set_repetition_rate(frequency)
        res = self.device.trigger_pulse_generator()
        if not res:
            self.stim_status.setText(f"Stimulation failed at {pair}")


    def trigger_sweep(self):
        self.current_freq = int(self.start.text())
        ending_freq = int(self.end.text())
        step_freq = int(self.step.text())

        frequencies = []
        for freq in range(self.current_freq, ending_freq, step_freq):
            frequencies.append(freq)

        if self.between.text():
            self.thread = QThread()
            self.worker = WorkerInt(frequencies, float(self.between.text()))
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.progress.connect(self.single_stim)
            self.thread.start()
 
class VoltageSwipe(QWidget):
    def __init__(self, channels, device, handmap):
        super().__init__()
        self.device = device
        self.layout = QFormLayout()
        # settings
        self.freq = QLineEdit("50")
        self.num_nplets = QLineEdit("10")
        self.amplitudes = QLineEdit("1")
        self.widths = QLineEdit("1000")
        self.between = QLineEdit("1.5")
        self.layout.addRow("Pulse repetitions", self.num_nplets)
        self.layout.addRow("Amplitude (mA)", self.amplitudes)
        self.layout.addRow("Frequency (Hz)", self.freq)
        self.layout.addRow("Pulse width (us)", self.widths)
        self.layout.addRow("Time between stims (s)", self.between)
        self.apply = QPushButton("Apply settings")
        self.apply.clicked.connect(self.apply_settings)
        self.layout.addWidget(self.apply)

        self.settings_status = QLabel("")
        self.layout.addWidget(self.settings_status)

        # freq sweep
        self.start = QLineEdit("70")
        self.end = QLineEdit("150")
        self.step = QLineEdit("10")
        self.layout.addRow("Starting voltage (V)", self.start)
        self.layout.addRow("Ending voltage (V)", self.end)
        self.layout.addRow("Step (V)", self.step)
        self.sweep = QPushButton("Sweep")
        self.sweep.clicked.connect(self.trigger_sweep)
        self.layout.addWidget(self.sweep)

        self.stim_status = QLabel("")
        self.layout.addWidget(self.stim_status)

        self.setLayout(self.layout)

        self.channels = channels
        self.tofile = ""

    def apply_settings(self):
        res = True
        res = self.device.set_repetition_rate(int(self.freq.text()))
        res = self.device.set_num_nplets(int(self.num_nplets.text()))
        res = self.device.set_amplitude([int(float(self.amplitudes.text()) * 100)])
        res = self.device.set_pulse_width([int(self.widths.text())])
        cathodes, anodes = self.channels.get_active_channels()
        try:
            self.electrodes = [cathodes[0], anodes[0]]
            electrodes = [([self.electrodes[0]], [self.electrodes[1]])]
            res = self.device.set_pulses_bipolar(electrodes)
            if not res:
                self.settings_status.setText("Settings failed")
            else:
                self.settings_status.setText("Settings OK")
        except:
            self.stim_status.setText("Please select a cathode and an anode")

    def single_stim(self, voltage):
        """
        perform single stimulation when QWorker emits a signal
        """
        self.stim_status.setText(f"Currently at {voltage}")
        res = True
        res = self.device.set_voltage(voltage)
        res = self.device.trigger_pulse_generator()
        if not res:
            self.stim_status.setText(f"Stimulation failed at {pair}")


    def trigger_sweep(self):
        starting_volt = int(self.start.text())
        ending_volt = int(self.end.text())
        step_volt = int(self.step.text())

        voltages = []
        for volt in range(starting_volt, ending_volt, step_volt):
            voltages.append(volt)

        if self.between.text():
            self.thread = QThread()
            self.worker = WorkerInt(voltages, float(self.between.text()))
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.progress.connect(self.single_stim)
            self.thread.start()
 
