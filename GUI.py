from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QGraphicsView, QGraphicsEllipseItem, \
     QPushButton, QHBoxLayout, QVBoxLayout, QTableView, QDialog, QLabel, QLineEdit, QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsTextItem, \
     QTabWidget, QFormLayout
from PyQt6.QtGui import QPen, QColor
from PyQt6.QtCore import Qt, QRectF, QEventLoop, QEvent, QObject, QThread, pyqtSignal
import sys
from controller import Controller
import time
from datetime import datetime

channel_layout = [15,12,9,6,16,13,8,5,17,14,7,4,18,11,10,3]

class ExitButton(QPushButton):
    def __init__(self):
        super().__init__("Exit")
        self.clicked.connect(sys.exit)
    
class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(list)

    def __init__(self, pairs, between):
        """
        QWorker for sweeping without logging, GUI hangs if this is done w/o a thread
        """
        super().__init__()
        self.pairs = pairs
        self.between = between

    def run(self):
        for pair in self.pairs:
            self.progress.emit(pair)
            time.sleep(self.between)
        self.finished.emit()

class Channel(QGraphicsEllipseItem):
    def __init__(self, y, x, sz, channel_n):
        super().__init__()
        self.rectsize = sz #Length of the side of a square that can surround     the circle
        self.channel_n = channel_n 
        self.x = 15+x*sz  #Adjusting the circle's position
        self.y = 15+y*sz
 
        self.setRect(self.x, self.y, self.rectsize, self.rectsize)
        self.setBrush(QColor(238, 238, 238))
        self.show()

        self.mode = "off"

    def mousePressEvent(self, *args, **kwargs):
        if self.mode == "off":
            self.setBrush(QColor(0, 0, 255))
            self.mode = "cathode"
            self.scene().views()[0].active_cathodes.append(self.channel_n)
        elif self.mode == "cathode":
            self.setBrush(QColor(255, 0, 0))
            self.mode = "anode"
            self.scene().views()[0].active_cathodes.remove(self.channel_n)
            self.scene().views()[0].active_anodes.append(self.channel_n)
        else:
            self.setBrush(QColor(238, 238, 238))
            self.mode = "off"
            self.scene().views()[0].active_anodes.remove(self.channel_n)
            

class ChannelView(QGraphicsView):
    def __init__(self):
        super(QWidget, self).__init__()
        self.setGeometry(0,0,500,500)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.sz = 100
        self.add_channels()
        self.active_cathodes = []
        self.active_anodes = []
        
        # Show labels
        cat = QGraphicsEllipseItem(0,0,20,20)
        cat.setBrush(QColor(0,0,255))
        cat_label = QGraphicsTextItem(f"Cathode")
        cat_label.setPos(25,-5)
        self.scene.addItem(cat_label)
        self.scene.addItem(cat)
        
        ano = QGraphicsEllipseItem(0,-25,20,20)
        ano.setBrush(QColor(255,0,0))
        ano_label = QGraphicsTextItem(f"Anode")
        ano_label.setPos(25,-25)
        self.scene.addItem(ano_label)
        self.scene.addItem(ano)

    def add_channels(self):
        for y in range(4):
            for x in range(4):
                channel_n = channel_layout[y*4+x]
                self.scene.addItem(Channel(y,x,self.sz, channel_n)) 
                label = QGraphicsTextItem(f"{channel_n}")
                label.setPos(self.sz/2+x*self.sz, self.sz/2+y*self.sz)
                self.scene.addItem(label)

    def get_active_channels(self):
        return self.active_cathodes, self.active_anodes

class ChannelSwipe(QWidget):
    def __init__(self, channels, device):
        super().__init__()
        self.device = device
        self.layout = QFormLayout()
        # settings
        self.voltage = QLineEdit("150")
        self.num_nplets = QLineEdit("10")
        self.amplitudes = QLineEdit("1.5")
        self.widths = QLineEdit("1000")
        self.freq = QLineEdit("50")
        self.between = QLineEdit("1")
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

        self.setLayout(self.layout)

        self.channels = channels
        self.tofile = ""
        self.loop = None

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
        If self.between is empty, prompts user for key press to record stimulation result, finally saving res to file
        """
        pairs = self.generate_combinations()
        if not pairs:
            raise Exception("Please select at least one electrode pair")

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
    
        else:
            for pair in pairs:
                self.electrodes = pair
                res = True
                res = self.device.set_pulses_bipolar(pair)
                res = self.device.trigger_pulse_generator()
                if not res:
                    raise Exception("Device trigger failed")
                else:
                    self.stim_status.setText(f"Currently at {pair}")
                    self.loop = QEventLoop()
                    self.loop.exec()
                self.loop = None
            self.stim_status.setText(f"Done")

            fname = f"./mittaukset/channelsweep_{datetime.now().isoformat().replace(':', '')}.csv"
            with open(fname, "w") as file:
                file.write("voltage,nplets,freq,width,amplitude,cathode,anode,result\n")
                file.write(self.tofile)
                self.tofile = ""

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

    def keyPressEvent(self, event):
        """
        If event loop is active, write stimulation parameters and result of stimulation (keypress) to string
        """
        if self.loop:
            self.tofile += f"{self.voltage.text()},{self.num_nplets.text()},{self.freq.text()},{self.widths.text()},{self.amplitudes.text()},{self.electrodes[0][0]},{self.electrodes[0][1]},{event.text()}"
            self.tofile += "\n"
            self.loop.quit()

class AmplitudeSwipe(QWidget):
    def __init__(self, channels, device):
        super().__init__()
        self.device = device
        self.layout = QFormLayout()
        # settings
        self.voltage = QLineEdit("70")
        self.num_nplets = QLineEdit("5")
        self.freq = QLineEdit("50")
        self.widths = QLineEdit("1000")
        self.between = QLineEdit("0.5")
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
        self.end = QLineEdit("1.4")
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
        self.loop = None

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
        while self.current_amp <= ending_amp:
            res = True
            res = self.device.set_amplitude([self.current_amp])
            res = self.device.trigger_pulse_generator()
            if not res:
                # Tähän vielä serial quit
                raise Exception("Device trigger failed")   
            if self.between.text():
                time.sleep(float(self.between.text()))
            else:
                self.stim_status.setText(f"Currently at: {self.current_amp}")
                self.loop = QEventLoop()
                self.loop.exec()
            self.current_amp += step_amp
        self.loop = None
        self.stim_status.setText(f"Done")
        if not self.between.text():
            with open(f"mittaukset/ampsweep_{datetime.now().isoformat().replace(':','')}.csv", "w") as file:
                file.write("voltage,nplets,freq,width,amplitude,cathode,anode,result\n")
                file.write(self.tofile)
                self.tofile = ""

    def keyPressEvent(self, event):
        """
        If event loop is active, write stimulation parameters and result of stimulation (keypress) to string
        """
        if self.loop:
            self.tofile += f"{self.voltage.text()},{self.num_nplets.text()},{self.freq.text()},{self.widths.text()},{self.current_amp},{self.electrodes[0]},{self.electrodes[1]},{event.text()}"
            self.tofile += "\n"
            self.loop.quit()
        
class FrequencySwipe(QWidget):
    def __init__(self, channels, device):
        super().__init__()
        self.device = device
        self.layout = QFormLayout()
        # settings
        self.voltage = QLineEdit("70")
        self.num_nplets = QLineEdit("5")
        self.amplitudes = QLineEdit("1")
        self.widths = QLineEdit("1000")
        self.between = QLineEdit("0.5")
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
        self.start = QLineEdit()
        self.end = QLineEdit()
        self.step = QLineEdit()
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
        self.loop = None

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
    def trigger_sweep(self):
        self.current_freq = int(self.start.text())
        ending_freq = int(self.end.text())
        step_freq = int(self.step.text())

        while self.current_freq <= ending_freq:
            res = True
            res = self.device.set_repetition_rate(self.current_freq)
            res = self.device.trigger_pulse_generator()
            if not res:
                raise Exception("Device trigger failed") 
            if self.between.text():
                time.sleep(float(self.between.text()))
            else:
                self.stim_status.setText(f"Currently at: {self.current_freq}")
                self.loop = QEventLoop()
                self.loop.exec()
            self.current_freq += step_freq
        self.loop = None
        self.stim_status.setText("Done")
        if not self.between.text():
            with open(f"mittaukset/freq_sweep{datetime.now().isoformat().replace(':', '')}.csv", "w") as file:
                file.write("voltage,nplets,freq,width,amplitude,cathode,anode,result\n")
                file.write(self.tofile)
                self.tofile = ""

    def keyPressEvent(self, event):
        """
        If event loop is active, write stimulation parameters and result of stimulation (keypress) to string
        """
        if self.loop:
            self.tofile += f"{self.voltage.text()},{self.num_nplets.text()},{self.current_freq},{self.widths.text()},{self.amplitudes.text()},{self.electrodes[0]},{self.electrodes[1]},{event.text()}"
            self.tofile += "\n"
            self.loop.quit()
 


class MainWindow(QWidget): 
    def __init__(self, device=None):
        super().__init__()
        self.device = device

        self.setGeometry(0,0,1200,500)
    
        self.horizontal_layout = QHBoxLayout() 
        self.vertical_layout = QVBoxLayout()

        self.channels = ChannelView()
        self.horizontal_layout.addWidget(self.channels)

        self.create_tabs()

        self.create_menu()

        self.horizontal_layout.addWidget(self.tabs)
        self.horizontal_layout.addLayout(self.menubar)
        self.setLayout(self.horizontal_layout)
        self.show()


    def set_settings(self):
        self.step = QLineEdit()
        self.vertical_layout.addWidget(self.step)
        self.step.returnPressed.connect(self.update_btn)
        self.exit = ExitButton()
        self.vertical_layout.addWidget(self.exit)
        
    def create_tabs(self):
        self.tabs = QTabWidget()
        self.tab1 = ChannelSwipe(self.channels, self.device) 
        self.tab2 = AmplitudeSwipe(self.channels, self.device)
        self.tab3 = FrequencySwipe(self.channels, self.device)
        self.tabs.addTab(self.tab1,"Swipe channels")
        self.tabs.addTab(self.tab2,"Swipe amplitudes")
        self.tabs.addTab(self.tab3,"Swipe frequencies")
        
    def create_menu(self):
        self.menubar = QVBoxLayout()
        self.exitbtn = QPushButton("Close serial and exit")
        self.exitbtn.clicked.connect(self.close_and_exit)
        self.menubar.addWidget(self.exitbtn)

        self.devicebtn = QPushButton("Get device settings")
        self.devicebtn.clicked.connect(self.get_current_settings)
        self.menubar.addWidget(self.devicebtn)

        self.statistics = QLabel("")
        self.menubar.addWidget(self.statistics)
        # refaktorointi tulee olemaan 5/5 kokemus XD osaispa koodaa
        self.tab1.apply.clicked.connect(self.get_current_settings)
        self.tab2.apply.clicked.connect(self.get_current_settings)
        self.tab3.apply.clicked.connect(self.get_current_settings)

    def close_and_exit(self):
        sys.exit()

    def get_current_settings(self):
        if device:
            self.statistics.setText(device.__str__())
        else:
            self.statistics.setText("No device")

def abort_serial(device):
    # TODO joku parempi ratkasu, nyt vaan hätäjarru
    device.serial_.close()         
    

def set_base_settings(device):
    """
    NEVER set current_range to high
    """
    device.set_current_range('low')
    device.set_voltage(70) 
    device.set_pulse_generator(True)
    device.set_mode('bipolar')
    device.set_delay(0)
    
if __name__ == "__main__":
    try:
        # hardcodettu portti koska ei ginost
        device = Controller("COM4")
        set_base_settings(device)
    except:
        device = None
    app = QApplication([])
    window = MainWindow(device)
    sys.exit(app.exec())

