from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QGraphicsView, QGraphicsEllipseItem, \
     QPushButton, QHBoxLayout, QVBoxLayout, QTableView, QDialog, QLabel, QLineEdit, QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsTextItem, \
     QTabWidget, QFormLayout, QGraphicsLineItem, QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsSceneDragDropEvent
from PyQt6.QtGui import QPen, QColor, QBrush, QPixmap, QPolygon
from PyQt6.QtCore import Qt, QRectF, QEventLoop, QEvent, QObject, QThread, pyqtSignal
import sys
from controller import Controller
import time
from datetime import datetime
from tabs import FrequencySwipe, AmplitudeSwipe, ChannelSwipe, VoltageSwipe
from handmap import HandMap

# device on top
channel_layout = [15,12,9,6,16,13,8,5,17,14,7,4,18,11,10,3]

# device on the right side
channel_layout = [18,17,16,15,11,14,13,12,10,7,8,9,3,4,5,6]

class ExitButton(QPushButton):
    def __init__(self):
        super().__init__("Exit")
        self.clicked.connect(sys.exit)
    
class Channel(QGraphicsEllipseItem):
    def __init__(self, y, x, sz, channel_n):
        super().__init__()
        self.rectsize = sz #Length of the side of a square that can surround the circle
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
    

class GraphicsScene(QGraphicsScene):
    """Subclassed graphicsscene to accept custom commands"""
    def __init__(self):
        super(QGraphicsScene, self).__init__()
        self.pol = QPolygon()

    def mouseMoveEvent(self, event):
        event.scenePos().toPoint()
        
    def mouseRelaseEvent(self, event):
        pass

class ChannelView(QGraphicsView):
    def __init__(self):
        super(QWidget, self).__init__()
        self.setGeometry(0,0,900,1000)
        self.scene = GraphicsScene()
        #self.scene = QGraphicsScene()
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

        # two lines to show where the electrode array connects to device
        pen = QPen(QColor(0,0,0), 10)
        line = QGraphicsLineItem(420, 170, 470, 170)
        line.setPen(pen)
        self.scene.addItem(line)
        line = QGraphicsLineItem(420, 270, 470, 270)
        line.setPen(pen)
        self.scene.addItem(line)
        
        
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


class MainWindow(QWidget): 
    def __init__(self, device=None):
        super().__init__()
        self.device = device

        self.setGeometry(0,0,1500,1000)
    
        self.horizontal_layout = QHBoxLayout() 
        self.vertical_layout = QVBoxLayout()

        self.channels = ChannelView()
        self.handmap = HandMap(self.channels)
        self.horizontal_layout.addWidget(self.channels)

        self.create_tabs()

        self.create_menu()

        self.horizontal_layout.addWidget(self.tabs)
        self.horizontal_layout.addLayout(self.menubar)
        self.horizontal_layout.addWidget(self.handmap)
        self.setLayout(self.horizontal_layout)
        self.showMaximized()


    def set_settings(self):
        self.step = QLineEdit()
        self.vertical_layout.addWidget(self.step)
        self.step.returnPressed.connect(self.update_btn)
        self.exit = ExitButton()
        self.vertical_layout.addWidget(self.exit)
        
    def create_tabs(self):
        self.tabs = QTabWidget()
        self.tab1 = ChannelSwipe(self.channels, self.device, self.handmap) 
        self.tab2 = AmplitudeSwipe(self.channels, self.device, self.handmap)
        self.tab3 = FrequencySwipe(self.channels, self.device, self.handmap)
        self.tab4 = VoltageSwipe(self.channels, self.device, self.handmap)
        self.tabs.addTab(self.tab1,"Swipe channels")
        self.tabs.addTab(self.tab2,"Swipe amplitudes")
        self.tabs.addTab(self.tab3,"Swipe frequencies")
        self.tabs.addTab(self.tab4,"Swipe voltages")
        
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
        self.tab4.apply.clicked.connect(self.get_current_settings)

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
    dont set current_range to high
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

