"""
Scalable Process Graphics - TRACE MODE Style
==============================================

QGraphicsView/QGraphicsScene-based process visualization.
All elements scale correctly and maintain proportions.
"""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsTextItem, QGraphicsRectItem
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import (QPainter, QColor, QPen, QBrush, QFont,
                         QLinearGradient, QRadialGradient, QPainterPath, QPolygonF, QTransform)
import math


# Design coordinate system: 1600x900 (16:9 aspect ratio)
DESIGN_WIDTH = 1600
DESIGN_HEIGHT = 900


class TagItem(QGraphicsItem):
    """
    TRACE MODE style tag - rounded panel with title and large numeric value.
    Clickable for interaction.
    """

    def __init__(self, tag_name, value=0.0, units="°C", width=140, height=80):
        super().__init__()
        self.tag_name = tag_name
        self.value = value
        self.units = units
        self.tag_width = width
        self.tag_height = height
        self.highlighted = False

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)

    def boundingRect(self):
        return QRectF(0, 0, self.tag_width, self.tag_height)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background gradient - dark blue/graphite TRACE MODE style
        gradient = QLinearGradient(0, 0, 0, self.tag_height)
        if self.highlighted:
            gradient.setColorAt(0, QColor(80, 150, 200))
            gradient.setColorAt(1, QColor(60, 120, 170))
        else:
            gradient.setColorAt(0, QColor(55, 75, 95))
            gradient.setColorAt(1, QColor(40, 55, 70))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(120, 140, 160), 2))
        painter.drawRoundedRect(QRectF(0, 0, self.tag_width, self.tag_height), 8, 8)

        # Tag name (title)
        painter.setPen(QColor(200, 210, 220))
        font_title = QFont("Arial", 11, QFont.Weight.Bold)
        painter.setFont(font_title)
        painter.drawText(QRectF(5, 5, self.tag_width - 10, 25), Qt.AlignmentFlag.AlignCenter, self.tag_name)

        # Value - LARGE YELLOW (TRACE MODE style)
        painter.setPen(QColor(255, 255, 100))
        font_value = QFont("Arial", 20, QFont.Weight.Bold)
        painter.setFont(font_value)
        value_text = f"{self.value:.1f}"
        painter.drawText(QRectF(5, 30, self.tag_width - 10, 35), Qt.AlignmentFlag.AlignCenter, value_text)

        # Units - small below value
        painter.setPen(QColor(180, 190, 200))
        font_units = QFont("Arial", 9)
        painter.setFont(font_units)
        painter.drawText(QRectF(5, 60, self.tag_width - 10, 15), Qt.AlignmentFlag.AlignCenter, self.units)

    def setValue(self, value):
        self.value = value
        self.update()

    def setHighlighted(self, highlighted):
        self.highlighted = highlighted
        self.update()

    def mousePressEvent(self, event):
        # Emit signal through scene
        if self.scene():
            self.scene().tagClicked.emit(self.tag_name)
        super().mousePressEvent(event)


class PipeItem(QGraphicsItem):
    """
    Metallic pipe with gradient and flow animation.
    Animation speed varies with flow intensity.
    """

    def __init__(self, length=100, thickness=30, horizontal=True):
        super().__init__()
        self.length = length
        self.thickness = thickness
        self.horizontal = horizontal
        self.flow_active = False
        self.flow_intensity = 0.0  # 0.0-1.0 to control animation speed
        self.flow_offset = 0

        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)

        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._animate)
        self.timer.start(50)

    def boundingRect(self):
        if self.horizontal:
            return QRectF(0, 0, self.length, self.thickness)
        else:
            return QRectF(0, 0, self.thickness, self.length)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Metallic grey gradient
        if self.horizontal:
            gradient = QLinearGradient(0, 0, 0, self.thickness)
        else:
            gradient = QLinearGradient(0, 0, self.thickness, 0)

        if self.flow_active:
            # Active pipe - blue-ish
            gradient.setColorAt(0, QColor(100, 110, 120))
            gradient.setColorAt(0.5, QColor(140, 150, 160))
            gradient.setColorAt(1, QColor(100, 110, 120))
        else:
            # Inactive pipe - grey
            gradient.setColorAt(0, QColor(80, 85, 90))
            gradient.setColorAt(0.5, QColor(110, 115, 120))
            gradient.setColorAt(1, QColor(80, 85, 90))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(60, 65, 70), 2))

        if self.horizontal:
            painter.drawRect(QRectF(0, 0, self.length, self.thickness))
        else:
            painter.drawRect(QRectF(0, 0, self.thickness, self.length))

        # ADDED: Draw animated flow indicators (moving highlights)
        if self.flow_active:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(200, 220, 255, 120)))  # Light blue highlight

            spacing = 40  # Spacing between flow indicators
            size = 8      # Size of flow indicator

            if self.horizontal:
                # Horizontal flow indicators
                for i in range(0, int(self.length) + spacing, spacing):
                    x = (i + self.flow_offset) % (self.length + spacing)
                    if x < self.length:
                        painter.drawEllipse(QRectF(x - size/2, self.thickness/2 - size/2, size, size))
            else:
                # Vertical flow indicators
                for i in range(0, int(self.length) + spacing, spacing):
                    y = (i + self.flow_offset) % (self.length + spacing)
                    if y < self.length:
                        painter.drawEllipse(QRectF(self.thickness/2 - size/2, y - size/2, size, size))

    def setActive(self, active, intensity=1.0):
        """
        Set flow animation active state and intensity.

        Args:
            active: Boolean, whether flow is active
            intensity: Float 0.0-1.0, animation speed multiplier
        """
        self.flow_active = active
        self.flow_intensity = max(0.0, min(1.0, intensity))
        self.update()

    def _animate(self):
        if self.flow_active:
            # Speed varies from 2 (low) to 8 (high) based on intensity
            speed = 2 + 6 * self.flow_intensity
            self.flow_offset = (self.flow_offset + speed) % 40
            self.update()


class ArrowItem(QGraphicsItem):
    """
    Flow direction arrow inside pipe.
    """

    def __init__(self, x, y, direction='right', size=20):
        super().__init__()
        self.arrow_x = x
        self.arrow_y = y
        self.direction = direction  # 'right', 'left', 'down', 'up'
        self.arrow_size = size
        self.active = False

        self.setPos(x, y)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)

    def boundingRect(self):
        return QRectF(-self.arrow_size, -self.arrow_size, self.arrow_size * 2, self.arrow_size * 2)

    def paint(self, painter, option, widget):
        if not self.active:
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Arrow color
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.setPen(QPen(QColor(200, 200, 200), 2))

        # Create arrow polygon based on direction
        path = QPainterPath()

        if self.direction == 'right':
            path.moveTo(-10, -8)
            path.lineTo(10, 0)
            path.lineTo(-10, 8)
            path.closeSubpath()
        elif self.direction == 'left':
            path.moveTo(10, -8)
            path.lineTo(-10, 0)
            path.lineTo(10, 8)
            path.closeSubpath()
        elif self.direction == 'down':
            path.moveTo(-8, -10)
            path.lineTo(0, 10)
            path.lineTo(8, -10)
            path.closeSubpath()
        elif self.direction == 'up':
            path.moveTo(-8, 10)
            path.lineTo(0, -10)
            path.lineTo(8, 10)
            path.closeSubpath()

        painter.drawPath(path)

    def setActive(self, active):
        self.active = active
        self.update()


class ValveItem(QGraphicsItem):
    """
    Valve symbol with green wheel indicator and position indicator.
    """

    def __init__(self, size=60):
        super().__init__()
        self.valve_size = size
        self.position = 0.0  # 0.0 = closed, 1.0 = fully open
        self.highlighted = False

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)

    def boundingRect(self):
        return QRectF(-self.valve_size / 2, -self.valve_size / 2, self.valve_size, self.valve_size)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Valve body - diamond shape
        path = QPainterPath()
        half = self.valve_size / 2
        path.moveTo(0, -half)
        path.lineTo(half, 0)
        path.lineTo(0, half)
        path.lineTo(-half, 0)
        path.closeSubpath()

        # Gradient based on position
        gradient = QLinearGradient(-half, -half, half, half)
        if self.position > 0.5:
            # More open - greenish
            gradient.setColorAt(0, QColor(80, 150, 100))
            gradient.setColorAt(1, QColor(60, 120, 80))
        elif self.position > 0.1:
            # Partially open - yellow-ish
            gradient.setColorAt(0, QColor(150, 150, 80))
            gradient.setColorAt(1, QColor(120, 120, 60))
        else:
            # Closed - grey
            gradient.setColorAt(0, QColor(100, 100, 100))
            gradient.setColorAt(1, QColor(70, 70, 70))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(50, 50, 50), 3))
        painter.drawPath(path)

        # Green wheel indicator on top
        wheel_radius = 15
        wheel_gradient = QRadialGradient(0, -half - 20, wheel_radius)
        wheel_gradient.setColorAt(0, QColor(100, 255, 100))
        wheel_gradient.setColorAt(1, QColor(50, 200, 50))

        painter.setBrush(QBrush(wheel_gradient))
        painter.setPen(QPen(QColor(30, 30, 30), 2))
        painter.drawEllipse(QPointF(0, -half - 20), wheel_radius, wheel_radius)

        # Wheel spokes (rotate based on position)
        painter.setPen(QPen(QColor(30, 30, 30), 2))
        angle_offset = self.position * 360  # Rotate wheel based on opening
        for i in range(6):
            angle = math.radians(i * 60 + angle_offset)
            x_end = wheel_radius * 0.7 * math.cos(angle)
            y_end = wheel_radius * 0.7 * math.sin(angle)
            painter.drawLine(QPointF(0, -half - 20), QPointF(x_end, -half - 20 + y_end))

        # Position indicator badge
        painter.setBrush(QBrush(QColor(50, 50, 50, 200)))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        badge_rect = QRectF(-25, 10, 50, 20)
        painter.drawRoundedRect(badge_rect, 5, 5)

        painter.setPen(QColor(255, 255, 100))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, f"{self.position * 100:.0f}%")

    def setPosition(self, position):
        self.position = max(0.0, min(1.0, position))
        self.update()

    def setHighlighted(self, highlighted):
        self.highlighted = highlighted
        self.update()

    def mousePressEvent(self, event):
        if self.scene():
            self.scene().valveClicked.emit()
        super().mousePressEvent(event)


class HeatExchangerItem(QGraphicsItem):
    """
    Shell-and-tube heat exchanger - copper/brown with highlights.
    """

    def __init__(self, width=120, height=180):
        super().__init__()
        self.hex_width = width
        self.hex_height = height
        self.hot_temp = 100.0
        self.cold_temp = 20.0
        self.active = False
        self.highlighted = False

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)

    def boundingRect(self):
        return QRectF(-self.hex_width / 2, -self.hex_height / 2, self.hex_width, self.hex_height)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Shell - copper/brown gradient
        gradient = QLinearGradient(-self.hex_width / 2, -self.hex_height / 2,
                                   self.hex_width / 2, self.hex_height / 2)
        if self.active:
            gradient.setColorAt(0, QColor(205, 140, 80))  # Light copper
            gradient.setColorAt(0.5, QColor(184, 115, 51))  # Copper
            gradient.setColorAt(1, QColor(150, 90, 40))  # Dark copper
        else:
            gradient.setColorAt(0, QColor(130, 100, 80))
            gradient.setColorAt(0.5, QColor(110, 80, 60))
            gradient.setColorAt(1, QColor(90, 60, 40))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(80, 50, 30), 3))
        painter.drawRoundedRect(QRectF(-self.hex_width / 2, -self.hex_height / 2,
                                       self.hex_width, self.hex_height), 8, 8)

        # Tubes inside (vertical lines)
        painter.setPen(QPen(QColor(100, 70, 50), 2))
        tube_spacing = self.hex_width / 6
        for i in range(1, 6):
            x = -self.hex_width / 2 + i * tube_spacing
            painter.drawLine(QPointF(x, -self.hex_height / 2 + 10),
                           QPointF(x, self.hex_height / 2 - 10))

        # Steam nozzles (left side)
        painter.setPen(QPen(QColor(80, 80, 80), 4))
        painter.setBrush(QBrush(QColor(120, 120, 120)))
        # Inlet (top)
        painter.drawRect(QRectF(-self.hex_width / 2 - 20, -self.hex_height / 3, 20, 12))
        # Outlet (bottom)
        painter.drawRect(QRectF(-self.hex_width / 2 - 20, self.hex_height / 3 - 12, 20, 12))

        # Water/air nozzles (right side - horizontal)
        painter.setPen(QPen(QColor(70, 120, 180), 4))
        painter.setBrush(QBrush(QColor(100, 150, 200)))
        # Inlet
        painter.drawRect(QRectF(self.hex_width / 2, -10, 20, 20))
        # Outlet
        painter.drawRect(QRectF(self.hex_width / 2, -10, 20, 20))

        # Temperature badge
        painter.setBrush(QBrush(QColor(50, 50, 50, 200)))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        badge_rect = QRectF(-35, 0, 70, 25)
        painter.drawRoundedRect(badge_rect, 5, 5)

        painter.setPen(QColor(255, 200, 100))
        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, f"ΔT={self.hot_temp - self.cold_temp:.1f}°")

    def setTemperatures(self, hot, cold):
        self.hot_temp = hot
        self.cold_temp = cold
        self.update()

    def setActive(self, active):
        self.active = active
        self.update()

    def setHighlighted(self, highlighted):
        self.highlighted = highlighted
        self.update()

    def mousePressEvent(self, event):
        if self.scene():
            self.scene().hexClicked.emit()
        super().mousePressEvent(event)


class SensorTagItem(QGraphicsItem):
    """
    Sensor tag (like THK-0083) with different style than process tags.
    """

    def __init__(self, sensor_id="THK-0083", value=0.0, units="°C", width=100, height=60):
        super().__init__()
        self.sensor_id = sensor_id
        self.value = value
        self.units = units
        self.tag_width = width
        self.tag_height = height
        self.highlighted = False

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)

    def boundingRect(self):
        return QRectF(0, 0, self.tag_width, self.tag_height)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background - slightly different color for sensors
        gradient = QLinearGradient(0, 0, 0, self.tag_height)
        if self.highlighted:
            gradient.setColorAt(0, QColor(100, 180, 100))
            gradient.setColorAt(1, QColor(70, 140, 70))
        else:
            gradient.setColorAt(0, QColor(60, 80, 70))
            gradient.setColorAt(1, QColor(45, 60, 55))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(100, 120, 110), 2))
        painter.drawRoundedRect(QRectF(0, 0, self.tag_width, self.tag_height), 6, 6)

        # Sensor ID
        painter.setPen(QColor(180, 220, 180))
        font_id = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(font_id)
        painter.drawText(QRectF(5, 5, self.tag_width - 10, 18), Qt.AlignmentFlag.AlignCenter, self.sensor_id)

        # Value
        painter.setPen(QColor(255, 255, 150))
        font_value = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(font_value)
        value_text = f"{self.value:.1f} {self.units}"
        painter.drawText(QRectF(5, 25, self.tag_width - 10, 30), Qt.AlignmentFlag.AlignCenter, value_text)

    def setValue(self, value):
        self.value = value
        self.update()

    def setHighlighted(self, highlighted):
        self.highlighted = highlighted
        self.update()

    def mousePressEvent(self, event):
        if self.scene():
            self.scene().sensorClicked.emit(self.sensor_id)
        super().mousePressEvent(event)


class ProcessOverviewScene(QGraphicsScene):
    """
    Scene containing the entire process diagram.
    Uses design coordinate system (1600x900).
    """

    # Signals for interactivity
    tagClicked = pyqtSignal(str)
    valveClicked = pyqtSignal()
    hexClicked = pyqtSignal()
    sensorClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set scene rect to design coordinates
        self.setSceneRect(0, 0, DESIGN_WIDTH, DESIGN_HEIGHT)

        # Background - dark blue/graphite TRACE MODE style
        self.setBackgroundBrush(QBrush(QColor(45, 55, 65)))

        # Create all process elements
        self._create_process_diagram()

    def _create_process_diagram(self):
        """Create the complete process diagram in design coordinates"""

        # Header bar
        header_rect = QGraphicsRectItem(0, 0, DESIGN_WIDTH, 60)
        gradient = QLinearGradient(0, 0, 0, 60)
        gradient.setColorAt(0, QColor(52, 73, 94))
        gradient.setColorAt(1, QColor(44, 62, 80))
        header_rect.setBrush(QBrush(gradient))
        header_rect.setPen(QPen(Qt.PenStyle.NoPen))
        self.addItem(header_rect)

        # Header text
        header_text = QGraphicsTextItem("PROCESS OVERVIEW - Steam Heating System")
        header_text.setDefaultTextColor(QColor(236, 240, 241))
        header_text.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header_text.setPos(50, 12)
        self.addItem(header_text)

        # Process elements in vertical flow (steam → valve → HEX → condensate)
        # Horizontal air flow through HEX

        # STEAM SOURCE (top left - ~100°C secondary steam)
        self.steam_tag = TagItem("STEAM\n~100°C", 100.0, "°C", 160, 90)
        self.steam_tag.setPos(720, 100)
        self.addItem(self.steam_tag)

        # Pipe 1: Steam down to valve
        self.pipe1 = PipeItem(length=120, thickness=35, horizontal=False)
        self.pipe1.setPos(783, 200)
        self.addItem(self.pipe1)

        # Arrow in pipe 1
        self.arrow1 = ArrowItem(800, 260, 'down', 18)
        self.addItem(self.arrow1)

        # VALVE
        self.valve = ValveItem(size=70)
        self.valve.setPos(800, 360)
        self.addItem(self.valve)

        # Pipe 2: Valve to HEX (steam)
        self.pipe2 = PipeItem(length=140, thickness=35, horizontal=False)
        self.pipe2.setPos(783, 410)
        self.addItem(self.pipe2)

        # Arrow in pipe 2
        self.arrow2 = ArrowItem(800, 480, 'down', 18)
        self.addItem(self.arrow2)

        # HEAT EXCHANGER (center)
        self.hex = HeatExchangerItem(width=140, height=200)
        self.hex.setPos(800, 620)
        self.addItem(self.hex)

        # THK-0083 Sensor tag (top right - measures outlet air temperature)
        self.sensor_tag = SensorTagItem("THK-0083", 20.0, "°C", 110, 65)
        self.sensor_tag.setPos(1080, 480)
        self.addItem(self.sensor_tag)

        # Pipe 3: HEX to condensate drain
        self.pipe3 = PipeItem(length=100, thickness=35, horizontal=False)
        self.pipe3.setPos(783, 730)
        self.addItem(self.pipe3)

        # Arrow in pipe 3
        self.arrow3 = ArrowItem(800, 780, 'down', 18)
        self.addItem(self.arrow3)

        # CONDENSATE (bottom - steam condensate drain)
        self.condensate_tag = TagItem("CONDENSATE\nDRAIN", 100.0, "°C", 160, 90)
        self.condensate_tag.setPos(720, 820)
        self.addItem(self.condensate_tag)

        # AIR INLET (left - bottom inlet, ~16-22°C ambient air)
        self.air_in_tag = TagItem("AIR IN\n(bottom)", 20.0, "°C", 140, 80)
        self.air_in_tag.setPos(200, 575)
        self.addItem(self.air_in_tag)

        # Pipe air in (horizontal from left into HEX)
        self.pipe_air_in = PipeItem(length=350, thickness=30, horizontal=True)
        self.pipe_air_in.setPos(350, 605)
        self.addItem(self.pipe_air_in)

        # Arrow in air inlet pipe
        self.arrow_air_in = ArrowItem(525, 620, 'right', 18)
        self.addItem(self.arrow_air_in)

        # Pipe air out vertical (from HEX top upward)
        self.pipe_air_out_vert = PipeItem(length=100, thickness=30, horizontal=False)
        self.pipe_air_out_vert.setPos(870, 420)
        self.addItem(self.pipe_air_out_vert)

        # Arrow in air vertical outlet pipe
        self.arrow_air_out_vert = ArrowItem(885, 470, 'up', 18)
        self.addItem(self.arrow_air_out_vert)

        # Pipe air out horizontal (to the right toward greenhouse)
        self.pipe_air_out_horiz = PipeItem(length=200, thickness=30, horizontal=True)
        self.pipe_air_out_horiz.setPos(885, 405)
        self.addItem(self.pipe_air_out_horiz)

        # Arrow in air horizontal outlet pipe
        self.arrow_air_out_horiz = ArrowItem(985, 420, 'right', 18)
        self.addItem(self.arrow_air_out_horiz)

        # AIR OUT (top right - heated air exits to greenhouse)
        self.air_out_tag = TagItem("AIR OUT\n(top/THK-0083)", 22.0, "°C", 180, 90)
        self.air_out_tag.setPos(1090, 380)
        self.addItem(self.air_out_tag)

        # Store references for easy update
        self.tags = {
            'steam': self.steam_tag,
            'air_in': self.air_in_tag,
            'air_out': self.air_out_tag,
            'condensate': self.condensate_tag,
            'sensor': self.sensor_tag
        }

        self.pipes = [self.pipe1, self.pipe2, self.pipe3, self.pipe_air_in,
                      self.pipe_air_out_vert, self.pipe_air_out_horiz]
        self.arrows = [self.arrow1, self.arrow2, self.arrow3, self.arrow_air_in,
                       self.arrow_air_out_vert, self.arrow_air_out_horiz]

    def updateValues(self, T_air_in, Flow, T_air_out, T_condensate):
        """
        Update all values in the diagram per diploma process description.

        Args:
            T_air_in: Inlet air temperature (ambient, ~16-22°C)
            Flow: Valve opening (0-1)
            T_air_out: Outlet air temperature (measured by THK-0083)
            T_condensate: Steam condensate temperature
        """
        self.steam_tag.setValue(100.0)  # Secondary steam always ~100°C
        self.air_in_tag.setValue(T_air_in)
        self.air_out_tag.setValue(T_air_out)
        self.condensate_tag.setValue(T_condensate)
        self.sensor_tag.setValue(T_air_out)  # THK-0083 measures outlet air temperature
        self.valve.setPosition(Flow)
        self.hex.setTemperatures(T_condensate, T_air_out)

        # Update steam flow animations (driven by Flow valve opening)
        flow_active = Flow > 0.1
        self.pipe1.setActive(flow_active, Flow)
        self.pipe2.setActive(flow_active, Flow)
        self.pipe3.setActive(flow_active, Flow)
        self.arrow1.setActive(flow_active)
        self.arrow2.setActive(flow_active)
        self.arrow3.setActive(flow_active)

        # Air flow intensity is driven by Flow (more steam = more heating = stronger circulation)
        air_active = Flow > 0.05
        air_intensity = max(0.3, Flow)  # Minimum 30% even at low flow for visibility
        self.pipe_air_in.setActive(air_active, air_intensity)
        self.pipe_air_out_vert.setActive(air_active, air_intensity)
        self.pipe_air_out_horiz.setActive(air_active, air_intensity)
        self.arrow_air_in.setActive(air_active)
        self.arrow_air_out_vert.setActive(air_active)
        self.arrow_air_out_horiz.setActive(air_active)

        self.hex.setActive(flow_active)


class ProcessOverviewView(QGraphicsView):
    """
    View for the process diagram.
    Handles scaling, zoom, and pan.
    """

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)

        # Setup view
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Zoom state
        self.zoom_factor = 1.0
        self.min_zoom = 0.3
        self.max_zoom = 3.0

        # Initial fit
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event):
        """Maintain aspect ratio on resize"""
        super().resizeEvent(event)
        # Fit scene in view while preserving aspect ratio
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        """Handle zoom with Ctrl+wheel"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom
            delta = event.angleDelta().y()
            zoom_in = delta > 0

            if zoom_in:
                factor = 1.15
                self.zoom_factor *= factor
            else:
                factor = 1 / 1.15
                self.zoom_factor *= factor

            # Clamp zoom
            if self.zoom_factor < self.min_zoom:
                factor = self.min_zoom / (self.zoom_factor / factor)
                self.zoom_factor = self.min_zoom
            elif self.zoom_factor > self.max_zoom:
                factor = self.max_zoom / (self.zoom_factor / factor)
                self.zoom_factor = self.max_zoom

            self.scale(factor, factor)
            event.accept()
        else:
            super().wheelEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Reset zoom on double-click"""
        self.resetTransform()
        self.zoom_factor = 1.0
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        event.accept()
