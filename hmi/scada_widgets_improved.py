"""
Improved SCADA Widgets - BRIGHT and VISIBLE
============================================

Much better visibility with bright colors and larger sizes.
"""

from PyQt6.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal
from PyQt6.QtGui import (QPainter, QColor, QPen, QBrush, QFont,
                         QLinearGradient, QRadialGradient, QPainterPath, QPolygonF)
import math


class ProcessTag(QWidget):
    """Process tag - BRIGHT and LARGE for visibility"""

    clicked = pyqtSignal(str)

    def __init__(self, tag="TAG", value=0.0, units="", parent=None):
        super().__init__(parent)
        self.tag = tag
        self.value = value
        self.units = units
        self.setFixedSize(160, 80)  # Much larger
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def setValue(self, value: float):
        self.value = value
        self.update()

    def mousePressEvent(self, event):
        self.clicked.emit(self.tag)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Bright background
        gradient = QLinearGradient(0, 0, 0, 80)
        gradient.setColorAt(0, QColor(70, 130, 180))  # Steel blue
        gradient.setColorAt(1, QColor(50, 100, 150))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(255, 255, 255), 4))  # Thick white border
        painter.drawRoundedRect(2, 2, self.width() - 4, self.height() - 4, 10, 10)

        # Tag name - with shadow for contrast
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        painter.drawText(QRectF(6, 11, 150, 25), Qt.AlignmentFlag.AlignCenter, self.tag)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(QRectF(5, 10, 150, 25), Qt.AlignmentFlag.AlignCenter, self.tag)

        # Value - BRIGHT YELLOW with shadow
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        value_text = f"{self.value:.1f}"
        painter.drawText(QRectF(6, 41, 150, 30), Qt.AlignmentFlag.AlignCenter, value_text)
        painter.setPen(QColor(255, 255, 0))  # Bright yellow
        painter.drawText(QRectF(5, 40, 150, 30), Qt.AlignmentFlag.AlignCenter, value_text)

        # Units - smaller
        painter.setPen(QColor(220, 220, 220))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(QRectF(5, 62, 150, 15), Qt.AlignmentFlag.AlignCenter, self.units)


class Pipe(QWidget):
    """Animated pipe - BRIGHTER colors"""

    def __init__(self, length=100, diameter=40, horizontal=True, parent=None):
        super().__init__(parent)
        self.length = length
        self.diameter = diameter
        self.horizontal = horizontal
        self.flow_active = False
        self.flow_pos = 0

        if horizontal:
            self.setFixedSize(length, diameter)
        else:
            self.setFixedSize(diameter, length)

        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._animate)
        self.timer.start(50)

    def setActive(self, active: bool):
        self.flow_active = active

    def _animate(self):
        if self.flow_active:
            self.flow_pos = (self.flow_pos + 5) % 20
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.horizontal:
            # Horizontal pipe - BRIGHTER
            gradient = QLinearGradient(0, 0, 0, self.diameter)
            if self.flow_active:
                gradient.setColorAt(0, QColor(100, 149, 237))  # Cornflower blue
                gradient.setColorAt(0.5, QColor(135, 206, 250))  # Light sky blue
                gradient.setColorAt(1, QColor(100, 149, 237))
            else:
                gradient.setColorAt(0, QColor(120, 120, 120))
                gradient.setColorAt(0.5, QColor(160, 160, 160))
                gradient.setColorAt(1, QColor(120, 120, 120))

            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(200, 200, 200), 3))  # Bright border
            painter.drawRect(0, 0, self.length, self.diameter)

            # Flow indicators - BRIGHT
            if self.flow_active:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(255, 255, 255, 180)))  # White indicators
                for i in range(0, self.length + 20, 20):
                    x = (i + self.flow_pos) % (self.length + 20)
                    if x < self.length:
                        painter.drawEllipse(int(x), self.diameter // 2 - 3, 8, 6)
        else:
            # Vertical pipe - BRIGHTER
            gradient = QLinearGradient(0, 0, self.diameter, 0)
            if self.flow_active:
                gradient.setColorAt(0, QColor(100, 149, 237))
                gradient.setColorAt(0.5, QColor(135, 206, 250))
                gradient.setColorAt(1, QColor(100, 149, 237))
            else:
                gradient.setColorAt(0, QColor(120, 120, 120))
                gradient.setColorAt(0.5, QColor(160, 160, 160))
                gradient.setColorAt(1, QColor(120, 120, 120))

            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(200, 200, 200), 3))
            painter.drawRect(0, 0, self.diameter, self.length)

            # Flow indicators - BRIGHT
            if self.flow_active:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
                for i in range(0, self.length + 20, 20):
                    y = (i + self.flow_pos) % (self.length + 20)
                    if y < self.length:
                        painter.drawEllipse(self.diameter // 2 - 3, int(y), 6, 8)


class Valve(QWidget):
    """Control valve - BRIGHTER and LARGER"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.position = 0.6  # 0 to 1
        self.setFixedSize(80, 100)  # Larger

    def setPosition(self, pos: float):
        self.position = max(0.0, min(1.0, pos))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = 40, 60

        # Valve body - BRIGHT
        gradient = QRadialGradient(cx, cy, 30)
        gradient.setColorAt(0, QColor(180, 180, 200))
        gradient.setColorAt(1, QColor(140, 140, 160))
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(220, 220, 220), 3))  # Bright border
        painter.drawEllipse(cx - 30, cy - 30, 60, 60)

        # Valve stem - BRIGHT
        painter.setPen(QPen(QColor(255, 215, 0), 6))  # Gold stem
        painter.drawLine(cx, cy - 30, cx, 10)

        # Position indicator - BRIGHT YELLOW
        painter.setBrush(QBrush(QColor(255, 255, 0)))
        painter.setPen(QPen(QColor(255, 165, 0), 2))  # Orange border
        painter.drawEllipse(cx - 8, 2, 16, 16)

        # Valve disc (rotates) - BRIGHT
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.position * 90)  # 0-90 degrees

        # Disc - BRIGHT
        painter.setBrush(QBrush(QColor(255, 140, 0)))  # Dark orange
        painter.setPen(QPen(QColor(255, 215, 0), 2))
        painter.drawRect(-25, -4, 50, 8)

        painter.restore()

        # Position text - BRIGHT
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 85, 80, 15), Qt.AlignmentFlag.AlignCenter,
                        f"{int(self.position * 100)}%")


class HeatExchanger(QWidget):
    """Shell-and-tube heat exchanger - BRIGHTER and LARGER"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hot_temp = 100.0
        self.cold_temp = 20.0
        self.active = False
        self.setFixedSize(120, 100)  # Larger

    def setTemperatures(self, hot: float, cold: float):
        self.hot_temp = hot
        self.cold_temp = cold
        self.update()

    def setActive(self, active: bool):
        self.active = active
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Shell - BRIGHT
        gradient = QLinearGradient(0, 0, 0, 100)
        if self.active:
            gradient.setColorAt(0, QColor(255, 140, 0))  # Dark orange
            gradient.setColorAt(1, QColor(255, 69, 0))   # Orange red
        else:
            gradient.setColorAt(0, QColor(140, 140, 140))
            gradient.setColorAt(1, QColor(100, 100, 100))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(220, 220, 220), 3))
        painter.drawRoundedRect(10, 10, 100, 80, 10, 10)

        # Tubes (horizontal lines) - BRIGHT
        painter.setPen(QPen(QColor(200, 200, 255), 3))  # Light blue
        for i in range(4):
            y = 25 + i * 18
            painter.drawLine(15, y, 105, y)

        # Temperature labels - BRIGHT
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))

        # Hot side - RED
        painter.setPen(QColor(255, 100, 100))
        painter.drawText(QRectF(15, 12, 40, 15), Qt.AlignmentFlag.AlignLeft,
                        f"{self.hot_temp:.0f}°C")

        # Cold side - CYAN
        painter.setPen(QColor(100, 255, 255))
        painter.drawText(QRectF(65, 73, 40, 15), Qt.AlignmentFlag.AlignRight,
                        f"{self.cold_temp:.0f}°C")


class Pump(QWidget):
    """Centrifugal pump - BRIGHTER and LARGER"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.rotation = 0
        self.setFixedSize(80, 80)  # Larger

        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._animate)
        self.timer.start(50)

    def setRunning(self, running: bool):
        self.running = running

    def _animate(self):
        if self.running:
            self.rotation = (self.rotation + 10) % 360
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = 40, 40

        # Pump casing - BRIGHT
        gradient = QRadialGradient(cx, cy, 35)
        if self.running:
            gradient.setColorAt(0, QColor(100, 200, 100))  # Light green
            gradient.setColorAt(1, QColor(50, 150, 50))    # Green
        else:
            gradient.setColorAt(0, QColor(140, 140, 140))
            gradient.setColorAt(1, QColor(100, 100, 100))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(220, 220, 220), 3))
        painter.drawEllipse(cx - 35, cy - 35, 70, 70)

        # Impeller (rotating) - BRIGHT
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.rotation)

        if self.running:
            painter.setPen(QPen(QColor(255, 255, 100), 4))  # Bright yellow
        else:
            painter.setPen(QPen(QColor(120, 120, 120), 4))

        # Draw 4 impeller blades
        for i in range(4):
            painter.drawLine(0, 0, 25, 0)
            painter.rotate(90)

        painter.restore()

        # Center hub - BRIGHT
        if self.running:
            painter.setBrush(QBrush(QColor(255, 215, 0)))  # Gold
        else:
            painter.setBrush(QBrush(QColor(80, 80, 80)))

        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.drawEllipse(cx - 8, cy - 8, 16, 16)
