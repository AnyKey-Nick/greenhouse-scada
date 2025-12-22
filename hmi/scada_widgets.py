"""
Professional SCADA-Style Widgets (TRACE MODE Style)
====================================================

Industrial-quality HMI widgets for process visualization.
"""

from PyQt6.QtWidgets import QWidget, QFrame
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal
from PyQt6.QtGui import (QPainter, QColor, QPen, QBrush, QFont,
                         QLinearGradient, QRadialGradient, QPainterPath, QPolygonF)
import math


class StatusLED(QWidget):
    """Industrial LED indicator"""

    def __init__(self, label="", parent=None):
        super().__init__(parent)
        self.label = label
        self.state = False
        self.color_on = QColor(0, 255, 0)  # Green
        self.color_off = QColor(50, 50, 50)  # Dark gray
        self.setFixedSize(80, 30)

    def setState(self, state: bool):
        self.state = state
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # LED circle
        color = self.color_on if self.state else self.color_off

        # Gradient for 3D effect
        gradient = QRadialGradient(12, 12, 10)
        if self.state:
            gradient.setColorAt(0, color.lighter(150))
            gradient.setColorAt(1, color)
        else:
            gradient.setColorAt(0, color.lighter(120))
            gradient.setColorAt(1, color.darker(120))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(30, 30, 30), 2))
        painter.drawEllipse(5, 5, 20, 20)

        # Label
        painter.setPen(QColor(220, 220, 220))
        painter.setFont(QFont("Arial", 9))
        painter.drawText(30, 18, self.label)


class AnalogGauge(QWidget):
    """Analog gauge indicator (like TRACE MODE)"""

    def __init__(self, label="", min_val=0, max_val=100, units="", parent=None):
        super().__init__(parent)
        self.label = label
        self.min_val = min_val
        self.max_val = max_val
        self.units = units
        self.value = min_val
        self.setFixedSize(120, 120)

    def setValue(self, value: float):
        self.value = max(self.min_val, min(self.max_val, value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = 60, 70
        radius = 45

        # Background circle
        gradient = QRadialGradient(cx, cy, radius)
        gradient.setColorAt(0, QColor(60, 60, 60))
        gradient.setColorAt(1, QColor(40, 40, 40))
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

        # Scale marks
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        for i in range(11):
            angle = 225 - i * 27  # -135° to +135° (270° range)
            angle_rad = math.radians(angle)
            x1 = cx + (radius - 8) * math.cos(angle_rad)
            y1 = cy - (radius - 8) * math.sin(angle_rad)
            x2 = cx + (radius - 3) * math.cos(angle_rad)
            y2 = cy - (radius - 3) * math.sin(angle_rad)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Needle
        normalized = (self.value - self.min_val) / (self.max_val - self.min_val)
        angle = 225 - normalized * 270
        angle_rad = math.radians(angle)

        needle_len = radius - 10
        nx = cx + needle_len * math.cos(angle_rad)
        ny = cy - needle_len * math.sin(angle_rad)

        painter.setPen(QPen(QColor(255, 50, 50), 3))
        painter.drawLine(cx, cy, int(nx), int(ny))

        # Center hub
        painter.setBrush(QBrush(QColor(80, 80, 80)))
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        painter.drawEllipse(cx - 5, cy - 5, 10, 10)

        # Value display
        painter.setPen(QColor(255, 255, 0))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        text = f"{self.value:.1f} {self.units}"
        painter.drawText(QRectF(10, 100, 100, 20), Qt.AlignmentFlag.AlignCenter, text)

        # Label
        painter.setPen(QColor(200, 200, 200))
        painter.setFont(QFont("Arial", 8))
        painter.drawText(QRectF(10, 5, 100, 20), Qt.AlignmentFlag.AlignCenter, self.label)


class Pipe(QWidget):
    """Animated pipe with flow indication"""

    def __init__(self, width, height, horizontal=True, parent=None):
        super().__init__(parent)
        self.horizontal = horizontal
        self.flow_active = False
        self.flow_offset = 0
        self.setFixedSize(width, height)

        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._animate)

    def setFlow(self, active: bool):
        if active and not self.flow_active:
            self.timer.start(50)  # 20 FPS
        elif not active and self.flow_active:
            self.timer.stop()
        self.flow_active = active
        self.update()

    def _animate(self):
        self.flow_offset = (self.flow_offset + 2) % 20
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        if self.horizontal:
            # Horizontal pipe
            pipe_y = h // 2 - 10

            # Pipe body (3D effect)
            gradient = QLinearGradient(0, pipe_y, 0, pipe_y + 20)
            gradient.setColorAt(0, QColor(100, 100, 120))
            gradient.setColorAt(0.5, QColor(140, 140, 160))
            gradient.setColorAt(1, QColor(100, 100, 120))

            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(60, 60, 80), 2))
            painter.drawRect(0, pipe_y, w, 20)

            # Flow indication (animated stripes)
            if self.flow_active:
                painter.setPen(QPen(QColor(0, 150, 255, 150), 2))
                for i in range(0, w + 20, 20):
                    x = i - self.flow_offset
                    painter.drawLine(x, pipe_y + 5, x, pipe_y + 15)
        else:
            # Vertical pipe
            pipe_x = w // 2 - 10

            gradient = QLinearGradient(pipe_x, 0, pipe_x + 20, 0)
            gradient.setColorAt(0, QColor(100, 100, 120))
            gradient.setColorAt(0.5, QColor(140, 140, 160))
            gradient.setColorAt(1, QColor(100, 100, 120))

            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(60, 60, 80), 2))
            painter.drawRect(pipe_x, 0, 20, h)

            if self.flow_active:
                painter.setPen(QPen(QColor(0, 150, 255, 150), 2))
                for i in range(0, h + 20, 20):
                    y = i - self.flow_offset
                    painter.drawLine(pipe_x + 5, y, pipe_x + 15, y)


class Valve(QWidget):
    """Industrial valve with position indicator"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.position = 0.0  # 0.0 = closed, 1.0 = open
        self.setFixedSize(60, 80)

    def setPosition(self, position: float):
        self.position = max(0.0, min(1.0, position))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = 30, 40

        # Valve body (circle)
        gradient = QRadialGradient(cx, cy, 20)
        gradient.setColorAt(0, QColor(120, 120, 140))
        gradient.setColorAt(1, QColor(80, 80, 100))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(50, 50, 60), 2))
        painter.drawEllipse(cx - 20, cy - 20, 40, 40)

        # Valve disk (rotates based on position)
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.position * 90)  # 0° to 90°

        # Disk
        painter.setBrush(QBrush(QColor(180, 180, 200)))
        painter.setPen(QPen(QColor(100, 100, 120), 2))
        painter.drawRect(-3, -18, 6, 36)

        painter.restore()

        # Position indicator
        color = QColor(0, 255, 0) if self.position > 0.8 else \
                QColor(255, 255, 0) if self.position > 0.2 else \
                QColor(255, 0, 0)

        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - 5, 5, 10, 10)

        # Position text
        painter.setPen(QColor(220, 220, 220))
        painter.setFont(QFont("Arial", 8))
        painter.drawText(QRectF(0, 65, 60, 15), Qt.AlignmentFlag.AlignCenter,
                        f"{self.position * 100:.0f}%")


class HeatExchanger(QWidget):
    """Shell-and-tube heat exchanger visualization"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.T_in = 20.0
        self.T_out = 20.0
        self.active = False
        self.setFixedSize(100, 150)

    def setTemperatures(self, T_in: float, T_out: float):
        self.T_in = T_in
        self.T_out = T_out
        self.update()

    def setActive(self, active: bool):
        self.active = active
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        # Shell (vertical cylinder)
        shell_w, shell_h = 60, 120
        shell_x = cx - shell_w // 2
        shell_y = cy - shell_h // 2

        # 3D shell body
        gradient = QLinearGradient(shell_x, 0, shell_x + shell_w, 0)
        gradient.setColorAt(0, QColor(139, 90, 43))  # Brown
        gradient.setColorAt(0.5, QColor(184, 115, 51))  # Copper
        gradient.setColorAt(1, QColor(139, 90, 43))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(80, 50, 20), 2))
        painter.drawRoundedRect(shell_x, shell_y, shell_w, shell_h, 5, 5)

        # Tubes (simplified - show as lines)
        painter.setPen(QPen(QColor(200, 200, 220), 2))
        for i in range(5):
            x = shell_x + 15 + i * 8
            painter.drawLine(x, shell_y + 10, x, shell_y + shell_h - 10)

        # Nozzles
        painter.setBrush(QBrush(QColor(100, 100, 120)))
        painter.setPen(QPen(QColor(60, 60, 80), 2))

        # Top nozzle (steam in)
        painter.drawRect(shell_x + 10, shell_y - 8, 15, 10)

        # Bottom nozzle (condensate out)
        painter.drawRect(shell_x + 10, shell_y + shell_h - 2, 15, 10)

        # Side nozzles (water)
        painter.drawRect(shell_x + shell_w - 2, cy - 15, 12, 10)  # Water in
        painter.drawRect(shell_x - 10, cy + 5, 12, 10)  # Water out

        # Temperature labels
        painter.setPen(QColor(255, 255, 0))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        painter.drawText(QRectF(0, shell_y - 25, w, 15),
                        Qt.AlignmentFlag.AlignCenter, f"{self.T_in:.1f}°C")
        painter.drawText(QRectF(0, shell_y + shell_h + 10, w, 15),
                        Qt.AlignmentFlag.AlignCenter, f"{self.T_out:.1f}°C")

        # Active indicator (glow effect)
        if self.active:
            painter.setPen(QPen(QColor(255, 100, 0, 100), 8))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(shell_x - 4, shell_y - 4,
                                   shell_w + 8, shell_h + 8, 8, 8)


class Pump(QWidget):
    """Centrifugal pump with rotation animation"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.angle = 0
        self.setFixedSize(60, 60)

        self.timer = QTimer()
        self.timer.timeout.connect(self._animate)

    def setRunning(self, running: bool):
        if running and not self.running:
            self.timer.start(30)  # 33 FPS
        elif not running and self.running:
            self.timer.stop()
        self.running = running

    def _animate(self):
        self.angle = (self.angle + 10) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = 30, 30

        # Pump casing
        gradient = QRadialGradient(cx, cy, 25)
        gradient.setColorAt(0, QColor(100, 100, 140))
        gradient.setColorAt(1, QColor(60, 60, 100))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(40, 40, 60), 2))
        painter.drawEllipse(cx - 25, cy - 25, 50, 50)

        # Impeller (rotating)
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle)

        painter.setPen(QPen(QColor(200, 200, 220), 3))
        for i in range(6):
            angle = i * 60
            angle_rad = math.radians(angle)
            x = 15 * math.cos(angle_rad)
            y = 15 * math.sin(angle_rad)
            painter.drawLine(0, 0, int(x), int(y))

        painter.restore()

        # Center hub
        painter.setBrush(QBrush(QColor(150, 150, 170)))
        painter.drawEllipse(cx - 5, cy - 5, 10, 10)

        # Status LED
        color = QColor(0, 255, 0) if self.running else QColor(100, 100, 100)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - 4, 5, 8, 8)


class DigitalDisplay(QWidget):
    """7-segment style digital display"""

    def __init__(self, label="", units="", decimals=1, parent=None):
        super().__init__(parent)
        self.label = label
        self.units = units
        self.decimals = decimals
        self.value = 0.0
        self.alarm = False
        self.setFixedSize(120, 50)

    def setValue(self, value: float):
        self.value = value
        self.update()

    def setAlarm(self, alarm: bool):
        self.alarm = alarm
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        bg_color = QColor(60, 20, 20) if self.alarm else QColor(20, 20, 30)
        painter.fillRect(self.rect(), bg_color)

        # Border
        painter.setPen(QPen(QColor(100, 100, 120), 2))
        painter.drawRect(1, 1, self.width() - 2, self.height() - 2)

        # Label
        painter.setPen(QColor(150, 150, 170))
        painter.setFont(QFont("Arial", 7))
        painter.drawText(QRectF(5, 3, 80, 12), Qt.AlignmentFlag.AlignLeft, self.label)

        # Value (large digital font)
        value_color = QColor(255, 50, 50) if self.alarm else QColor(0, 255, 0)
        painter.setPen(value_color)
        painter.setFont(QFont("Courier New", 16, QFont.Weight.Bold))
        value_text = f"{self.value:.{self.decimals}f}"
        painter.drawText(QRectF(5, 15, 85, 30), Qt.AlignmentFlag.AlignRight, value_text)

        # Units
        painter.setPen(QColor(150, 150, 170))
        painter.setFont(QFont("Arial", 8))
        painter.drawText(QRectF(90, 25, 25, 20), Qt.AlignmentFlag.AlignLeft, self.units)


class ProcessTag(QWidget):
    """Process tag label (TRACE MODE style)"""

    clicked = pyqtSignal(str)

    def __init__(self, tag="TAG", value=0.0, units="", parent=None):
        super().__init__(parent)
        self.tag = tag
        self.value = value
        self.units = units
        self.setFixedSize(100, 40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def setValue(self, value: float):
        self.value = value
        self.update()

    def mousePressEvent(self, event):
        self.clicked.emit(self.tag)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background (rounded rectangle)
        gradient = QLinearGradient(0, 0, 0, 40)
        gradient.setColorAt(0, QColor(70, 70, 90))
        gradient.setColorAt(1, QColor(50, 50, 70))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(120, 120, 140), 2))
        painter.drawRoundedRect(2, 2, self.width() - 4, self.height() - 4, 5, 5)

        # Tag name
        painter.setPen(QColor(200, 200, 220))
        painter.setFont(QFont("Arial", 8))
        painter.drawText(QRectF(5, 5, 90, 12), Qt.AlignmentFlag.AlignCenter, self.tag)

        # Value
        painter.setPen(QColor(0, 255, 255))
        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        value_text = f"{self.value:.1f} {self.units}"
        painter.drawText(QRectF(5, 18, 90, 18), Qt.AlignmentFlag.AlignCenter, value_text)
