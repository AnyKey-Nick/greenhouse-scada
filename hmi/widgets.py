"""
Custom Widgets for HMI
=======================

This module provides custom widgets for controls and P&ID visualization.
"""

from PyQt6.QtWidgets import (QWidget, QLabel, QDoubleSpinBox, QPushButton,
                              QVBoxLayout, QHBoxLayout, QGroupBox, QComboBox,
                              QGridLayout, QSlider, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
import math


class ParameterControl(QWidget):
    """
    Parameter control with spinbox and reset button.
    """
    valueChanged = pyqtSignal(float)

    def __init__(self, name: str, default_value: float, min_val: float = -1000.0,
                 max_val: float = 1000.0, decimals: int = 2, suffix: str = "",
                 parent=None):
        """
        Initialize parameter control.

        Args:
            name: Parameter name
            default_value: Default value
            min_val: Minimum value
            max_val: Maximum value
            decimals: Number of decimal places
            suffix: Unit suffix (e.g., " °C", " s")
            parent: Parent widget
        """
        super().__init__(parent)
        self.default_value = default_value

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Label
        label = QLabel(f"{name}:")
        label.setMinimumWidth(80)
        layout.addWidget(label)

        # Spinbox
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setRange(min_val, max_val)
        self.spinbox.setDecimals(decimals)
        self.spinbox.setValue(default_value)
        self.spinbox.setSuffix(suffix)
        self.spinbox.setMinimumWidth(100)
        self.spinbox.valueChanged.connect(self.valueChanged.emit)
        layout.addWidget(self.spinbox)

        # Reset button
        reset_btn = QPushButton("↺")
        reset_btn.setMaximumWidth(30)
        reset_btn.setToolTip("Reset to default")
        reset_btn.clicked.connect(self.reset)
        layout.addWidget(reset_btn)

        layout.addStretch()

    def value(self) -> float:
        """Get current value"""
        return self.spinbox.value()

    def setValue(self, value: float):
        """Set value"""
        self.spinbox.setValue(value)

    def reset(self):
        """Reset to default value"""
        self.spinbox.setValue(self.default_value)


class ControlPanel(QWidget):
    """
    Right-side control panel with all parameters and inputs.
    """
    paramChanged = pyqtSignal(str, float)  # (param_name, value)
    inputChanged = pyqtSignal(str, float)  # (input_name, value)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Setup control panel UI"""
        layout = QVBoxLayout(self)

        # Model parameters group
        params_group = QGroupBox("Model Parameters")
        params_layout = QVBoxLayout()

        self.param_controls = {
            'K': ParameterControl('K', 0.8, 0.0, 10.0, 2, parent=self),
            'T1': ParameterControl('T1', 120.0, 0.1, 1000.0, 1, ' s', parent=self),
            'T2': ParameterControl('T2', 60.0, 0.1, 1000.0, 1, ' s', parent=self),
            'L': ParameterControl('L', 10.0, 0.0, 100.0, 1, ' s', parent=self),
            'Kz': ParameterControl('Kz', 0.02, 0.0, 1.0, 3, parent=self),
            'TambRef': ParameterControl('TambRef', 0.0, -50.0, 50.0, 1, ' °C', parent=self),
            'KUW': ParameterControl('KUW', 0.5, 0.0, 10.0, 2, parent=self),
            'TW': ParameterControl('TW', 90.0, 0.1, 500.0, 1, ' s', parent=self),
        }

        for name, control in self.param_controls.items():
            control.valueChanged.connect(lambda val, n=name: self.paramChanged.emit(n, val))
            params_layout.addWidget(control)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # Inputs group
        inputs_group = QGroupBox("Inputs")
        inputs_layout = QVBoxLayout()

        self.input_controls = {
            'T_out': ParameterControl('T_out', 10.0, -50.0, 50.0, 1, ' °C', parent=self),
            'Flow': ParameterControl('Flow', 0.6, 0.0, 1.0, 2, parent=self),
            'dt_sec': ParameterControl('dt_sec', 0.5, 0.1, 10.0, 2, ' s', parent=self),
        }

        for name, control in self.input_controls.items():
            control.valueChanged.connect(lambda val, n=name: self.inputChanged.emit(n, val))
            inputs_layout.addWidget(control)

        inputs_group.setLayout(inputs_layout)
        layout.addWidget(inputs_group)

        layout.addStretch()

    def get_param_values(self):
        """Get all parameter values as dict"""
        return {name: ctrl.value() for name, ctrl in self.param_controls.items()}

    def get_input_values(self):
        """Get all input values as dict"""
        return {name: ctrl.value() for name, ctrl in self.input_controls.items()}

    def set_param_value(self, name: str, value: float):
        """Set parameter value"""
        if name in self.param_controls:
            self.param_controls[name].setValue(value)

    def set_input_value(self, name: str, value: float):
        """Set input value"""
        if name in self.input_controls:
            self.input_controls[name].setValue(value)


class PIDWidget(QWidget):
    """
    P&ID-style visualization of the steam-water heating system.
    Uses normalized coordinates (0-1) that scale with widget size.
    """
    badgeClicked = pyqtSignal(str)  # Signal when a badge is clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 300)

        # Current values for display
        self.values = {
            'T_out': 10.0,
            'Flow': 0.6,
            'T_greenhouse': 20.0,
            'T_water': 20.0,
            'u_dead': 0.0
        }

        # Badge positions (will be computed in paintEvent)
        self.badge_rects = {}

        # Normalized positions (0-1 relative to widget size)
        self.layout_normalized = {
            'steam_x': 0.08,
            'valve_x': 0.20,
            'hex_x': 0.40,
            'pump_x': 0.65,
            'greenhouse_x': 0.85,
            'center_y': 0.50
        }

    def update_values(self, **kwargs):
        """Update displayed values"""
        self.values.update(kwargs)
        self.update()

    def paintEvent(self, event):
        """Draw P&ID diagram with normalized coordinates"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Calculate scale factor based on minimum dimension
        scale = min(w / 800, h / 300)

        # Background
        painter.fillRect(0, 0, w, h, QColor(240, 240, 240))

        # Convert normalized positions to pixel coordinates
        layout = self.layout_normalized
        steam_x = int(w * layout['steam_x'])
        valve_x = int(w * layout['valve_x'])
        hex_x = int(w * layout['hex_x'])
        pump_x = int(w * layout['pump_x'])
        greenhouse_x = int(w * layout['greenhouse_x'])
        hex_y = int(h * layout['center_y'])

        # Scaled dimensions
        hex_w = int(80 * scale)
        hex_h = int(120 * scale)
        element_radius = int(20 * scale)
        pipe_width = max(2, int(3 * scale))

        # ===== Steam Source =====
        painter.setBrush(QBrush(QColor(200, 200, 200)))
        painter.setPen(QPen(Qt.GlobalColor.black, max(2, int(2 * scale))))
        painter.drawEllipse(steam_x - element_radius, hex_y - element_radius,
                          element_radius * 2, element_radius * 2)
        font_scaled = QFont("Arial", max(8, int(10 * scale)))
        painter.setFont(font_scaled)
        painter.drawText(steam_x - element_radius // 2, hex_y + 5, "S")

        # ===== Control Valve =====
        painter.setPen(QPen(Qt.GlobalColor.black, pipe_width))
        # Horizontal pipe to valve
        painter.drawLine(steam_x + element_radius, hex_y, valve_x - element_radius, hex_y)

        # Valve symbol (triangle) - scaled
        valve_path = QPainterPath()
        valve_size = int(20 * scale)
        valve_path.moveTo(valve_x - valve_size, hex_y - int(15 * scale))
        valve_path.lineTo(valve_x + valve_size, hex_y)
        valve_path.lineTo(valve_x - valve_size, hex_y + int(15 * scale))
        valve_path.closeSubpath()
        painter.setBrush(QBrush(QColor(150, 200, 150)))
        painter.drawPath(valve_path)

        # Flow badge near valve
        self._draw_badge(painter, valve_x, hex_y - int(40 * scale), "Flow",
                        self.values['Flow'], 2, '', scale)

        # ===== Shell-and-Tube Heat Exchanger =====
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        # Pipe from valve to HEX
        painter.drawLine(valve_x + 20, hex_y, hex_x - 50, hex_y)

        # HEX shell (vertical rectangle)
        hex_w = 80
        hex_h = 120
        painter.setBrush(QBrush(QColor(184, 115, 51)))  # Copper-brown
        painter.drawRect(hex_x - hex_w // 2, hex_y - hex_h // 2, hex_w, hex_h)

        # Steam inlet/outlet nozzles
        painter.setPen(QPen(Qt.GlobalColor.black, 3))
        painter.drawLine(hex_x - hex_w // 2 - 15, hex_y - 30, hex_x - hex_w // 2, hex_y - 30)  # In
        painter.drawLine(hex_x - hex_w // 2 - 15, hex_y + 30, hex_x - hex_w // 2, hex_y + 30)  # Out

        # Water pass (vertical line inside)
        painter.setPen(QPen(QColor(30, 144, 255), 4))  # Dodger blue
        painter.drawLine(hex_x, hex_y - hex_h // 2 + 10, hex_x, hex_y + hex_h // 2 - 10)

        # Water inlet/outlet
        painter.setPen(QPen(QColor(30, 144, 255), 3))
        painter.drawLine(hex_x, hex_y + hex_h // 2, hex_x, hex_y + hex_h // 2 + 30)  # Outlet down
        painter.drawLine(pump_x, hex_y + hex_h // 2 + 30, hex_x, hex_y + hex_h // 2 + 30)  # To pump

        # T_water badge
        self._draw_badge(painter, hex_x + int(50 * scale), hex_y + hex_h // 2 + int(30 * scale),
                        "T_water", self.values['T_water'], 1, '°C', scale)

        # ===== Pump =====
        pump_radius = int(25 * scale)
        painter.setBrush(QBrush(QColor(150, 150, 200)))
        painter.setPen(QPen(Qt.GlobalColor.black, pipe_width))
        painter.drawEllipse(pump_x - pump_radius, hex_y + hex_h // 2 + int(15 * scale),
                          pump_radius * 2, int(30 * scale))

        # Pump blades (simple) - scaled
        painter.drawLine(pump_x - int(10 * scale), hex_y + hex_h // 2 + int(20 * scale),
                        pump_x + int(10 * scale), hex_y + hex_h // 2 + int(40 * scale))
        painter.drawLine(pump_x - int(10 * scale), hex_y + hex_h // 2 + int(40 * scale),
                        pump_x + int(10 * scale), hex_y + hex_h // 2 + int(20 * scale))

        # Return pipe to HEX top
        painter.setPen(QPen(QColor(30, 144, 255), pipe_width))
        gh_offset = int(50 * scale)
        painter.drawLine(pump_x + pump_radius, hex_y + hex_h // 2 + int(30 * scale),
                        greenhouse_x - gh_offset, hex_y + hex_h // 2 + int(30 * scale))
        painter.drawLine(greenhouse_x - gh_offset, hex_y + hex_h // 2 + int(30 * scale),
                        greenhouse_x - gh_offset, hex_y)

        # ===== Greenhouse Block =====
        gh_size = int(100 * scale)
        painter.setBrush(QBrush(QColor(144, 238, 144)))  # Light green
        painter.setPen(QPen(Qt.GlobalColor.black, pipe_width))
        painter.drawRect(greenhouse_x - gh_size // 2, hex_y - gh_size // 2, gh_size, gh_size)

        font = QFont("Arial", max(8, int(10 * scale)), QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(greenhouse_x - int(40 * scale), hex_y - int(30 * scale), "Green-")
        painter.drawText(greenhouse_x - int(40 * scale), hex_y - int(15 * scale), "house")

        # T_greenhouse badge
        self._draw_badge(painter, greenhouse_x + int(60 * scale), hex_y - int(20 * scale),
                        "T_gh", self.values['T_greenhouse'], 1, '°C', scale)

        # ===== T_out badge (ambient) =====
        self._draw_badge(painter, int(50 * scale), int(30 * scale),
                        "T_out", self.values['T_out'], 1, '°C', scale)

        # ===== u_dead badge =====
        self._draw_badge(painter, valve_x, hex_y + int(40 * scale),
                        "u_dead", self.values['u_dead'], 2, '', scale)

    def _draw_badge(self, painter, x, y, label, value, decimals, unit='', scale=1.0):
        """Draw a digital value badge with scaling support"""
        text = f"{label}: {value:.{decimals}f}{unit}"

        font = QFont("Arial", max(7, int(9 * scale)))
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(text)
        text_height = metrics.height()

        badge_w = text_width + int(10 * scale)
        badge_h = text_height + int(6 * scale)

        # Background
        painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
        painter.setPen(QPen(Qt.GlobalColor.black, max(1, int(scale))))
        rect = QRectF(x - badge_w / 2, y - badge_h / 2, badge_w, badge_h)
        painter.drawRoundedRect(rect, int(3 * scale), int(3 * scale))

        # Text
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

        # Store badge rect for click detection
        self.badge_rects[label] = rect

    def mousePressEvent(self, event):
        """Handle badge clicks"""
        pos = event.pos()
        for label, rect in self.badge_rects.items():
            if rect.contains(pos.x(), pos.y()):
                self.badgeClicked.emit(label)
                break


class SimulationControls(QWidget):
    """
    Simulation control buttons (run/pause/step/reset).
    """
    runClicked = pyqtSignal()
    pauseClicked = pyqtSignal()
    stepClicked = pyqtSignal()
    resetClicked = pyqtSignal()
    speedChanged = pyqtSignal(float)  # Speed multiplier

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Setup control UI"""
        layout = QHBoxLayout(self)

        # Run button
        self.run_btn = QPushButton("▶ Run")
        self.run_btn.clicked.connect(self.runClicked.emit)
        layout.addWidget(self.run_btn)

        # Pause button
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self.pauseClicked.emit)
        layout.addWidget(self.pause_btn)

        # Step button
        self.step_btn = QPushButton("⏭ Step")
        self.step_btn.clicked.connect(self.stepClicked.emit)
        layout.addWidget(self.step_btn)

        # Reset button
        self.reset_btn = QPushButton("↻ Reset")
        self.reset_btn.clicked.connect(self.resetClicked.emit)
        layout.addWidget(self.reset_btn)

        layout.addSpacing(20)

        # Speed selector
        speed_label = QLabel("Speed:")
        layout.addWidget(speed_label)

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["×1", "×5", "×10"])
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)
        layout.addWidget(self.speed_combo)

        layout.addStretch()

    def _on_speed_changed(self, text: str):
        """Handle speed change"""
        multiplier = float(text.replace('×', ''))
        self.speedChanged.emit(multiplier)

    def set_running(self, running: bool):
        """Update button states based on running status"""
        self.run_btn.setEnabled(not running)
        self.pause_btn.setEnabled(running)
        self.step_btn.setEnabled(not running)
