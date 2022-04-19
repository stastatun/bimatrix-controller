from PyQt6.QtWidgets import QGraphicsView, QWidget, QGraphicsPixmapItem, QGraphicsScene, \
                            QGraphicsPathItem, QGraphicsRectItem
from PyQt6.QtGui import QImage, QPen, QColor, QBrush, QPixmap, QPolygon, QPainterPath, QPolygonF
import os
from PyQt6.QtCore import QPointF, Qt, QRectF, pyqtSignal

class GraphicsScene(QGraphicsScene):
    stims = pyqtSignal(list)
    def __init__(self):
        super(QGraphicsScene, self).__init__()
        self.setSceneRect(QRectF(0,0,800,550))
        self.polygon = QPolygonF()
        self.vector = []
        self.allpaths = []
        self.pathitem = QGraphicsPathItem()
        self.pathitem.setZValue(10)
        self.pathitem.setPen(QPen(QColor(255,0,0,), 3))
        self.addItem(self.pathitem)

        self.create_hand_zones()
    
    def create_hand_zones(self):
        self.hand_zones = {}

        for fname in os.listdir("./hand_zones"):
            with open(f"./hand_zones/{fname}", "r") as f:
                points = []
                for line in f:
                    x,y = line.rstrip().split(",")
                    x = float(x)
                    y = float(y)
                    points.append(QPointF(x,y))
            poly = QPolygonF(points)
            self.hand_zones[fname[0:-4]] = poly

        rect = QGraphicsRectItem(300,360,150,150)
        rect.setBrush(QBrush(QColor(255,0,0)))
        rect.setZValue(10)
        self.addItem(rect)
        rectf = QPolygonF([QPointF(300,360), QPointF(450,360), QPointF(450,510), QPointF(300,510)])
        self.hand_zones["NO"] = rectf


    def mousePressEvent(self, event):
        self.pressed = True
        qpointf = QPointF(event.scenePos().toPoint())
        self.vector.append(qpointf)

    def mouseMoveEvent(self, event):
        if self.pressed:
            self.path = QPainterPath()
            qpointf = QPointF(event.scenePos().toPoint())
            self.vector.append(qpointf)
            self.polygon = QPolygonF(self.vector) 
            self.path.addPolygon(self.polygon)
            #self.allpaths.append(self.path)
            self.pathitem.setPath(self.path)
        
    def mouseReleaseEvent(self, event):
        zones = []
        for pos in self.vector:
            for key, value in self.hand_zones.items():
                if value.containsPoint(pos, Qt.FillRule.OddEvenFill):
                    if key not in zones:
                        zones.append(key)

        self.polygon.clear()
        self.vector = []
        self.pressed = False
        self.removeItem(self.pathitem)
        self.pathitem = QGraphicsPathItem()
        self.pathitem.setZValue(10)
        self.pathitem.setPen(QPen(QColor(255,0,0,), 3))
        self.addItem(self.pathitem)

        debug = False
        if debug:
            print(zones)
    
        self.stims.emit(zones)
        
        

class HandMap(QGraphicsView):
    def __init__(self, channelview):
        super(QWidget, self).__init__()
        self.setGeometry(0, 0, 500, 500) 
        self.scene = GraphicsScene()
        self.setScene(self.scene)
        hand_diagram = QPixmap("./handbw.jpg").scaledToWidth(800)
        hand_graphics_diagram = QGraphicsPixmapItem(hand_diagram)
        hand_graphics_diagram.setZValue(0)
        self.scene.addItem(hand_graphics_diagram)
        #hand_graphics_diagram.setPos(0,-500)
