"""
Real-Time Plotting with pyqtgraph
==================================

This module provides fast, interactive time-series plots for the greenhouse
heating system monitoring.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
import pyqtgraph as pg
import numpy as np
from collections import deque


class TimeSeriesPlot(QWidget):
    """
    Base class for time-series plotting with sliding window.
    """

    def __init__(self, title: str, window_size: float = 600.0, parent=None):
        """
        Initialize time-series plot.

        Args:
            title: Plot title
            window_size: Time window to display (seconds)
            parent: Parent widget
        """
        super().__init__(parent)
        self.window_size = window_size
        self.max_points = 10000  # Limit for performance

        # Data buffers (circular)
        self.time_data = deque(maxlen=self.max_points)

        # Setup UI
        self._setup_ui(title)

    def _setup_ui(self, title: str):
        """Setup plot widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setTitle(title, color='k', size='12pt')
        self.plot_widget.setLabel('bottom', 'Time', units='s', color='k')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()

        # Enable crosshair cursor
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('k', style=Qt.PenStyle.DashLine))
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('k', style=Qt.PenStyle.DashLine))
        self.plot_widget.addItem(self.vLine, ignoreBounds=True)
        self.plot_widget.addItem(self.hLine, ignoreBounds=True)

        # Connect mouse move event
        self.plot_widget.scene().sigMouseMoved.connect(self._on_mouse_moved)

        layout.addWidget(self.plot_widget)

        # Curve dictionary
        self.curves = {}

    def add_curve(self, name: str, color: str, width: float = 2.0):
        """
        Add a curve to the plot.

        Args:
            name: Curve name (for legend)
            color: Color (e.g., 'r', 'b', '#FF5733')
            width: Line width
        """
        pen = pg.mkPen(color=color, width=width)
        curve = self.plot_widget.plot([], [], name=name, pen=pen)

        # Data buffer for this curve
        data_buffer = deque(maxlen=self.max_points)

        self.curves[name] = {
            'curve': curve,
            'data': data_buffer,
            'color': color
        }

    def update_curve(self, name: str, time_val: float, y_val: float):
        """
        Update curve with new data point.

        Args:
            name: Curve name
            time_val: Time value (x-axis)
            y_val: Y value
        """
        if name not in self.curves:
            return

        # Add to time buffer (shared across all curves on this plot)
        if not self.time_data or time_val > self.time_data[-1]:
            self.time_data.append(time_val)

        # Add to curve data
        self.curves[name]['data'].append(y_val)

        # Update plot
        self._update_plot()

    def _update_plot(self):
        """Update all curves on the plot"""
        if not self.time_data:
            return

        # Get time window
        current_time = self.time_data[-1]
        time_min = current_time - self.window_size

        # Find indices in window
        time_array = np.array(self.time_data)
        mask = time_array >= time_min

        time_windowed = time_array[mask]

        # Update each curve
        for name, curve_info in self.curves.items():
            data_array = np.array(curve_info['data'])

            # Handle mismatched lengths
            if len(data_array) == 0 or len(time_windowed) == 0:
                continue  # Skip empty data

            if len(data_array) == len(time_array):
                data_windowed = data_array[mask]
            else:
                # Trim to match time_windowed length
                n = min(len(data_array), len(time_windowed))
                data_windowed = data_array[-n:]
                time_windowed_adjusted = time_windowed[-n:]
                curve_info['curve'].setData(time_windowed_adjusted, data_windowed)
                continue

            # Ensure same shape before plotting
            if len(time_windowed) != len(data_windowed):
                n = min(len(time_windowed), len(data_windowed))
                time_windowed = time_windowed[:n]
                data_windowed = data_windowed[:n]

            if len(time_windowed) > 0:
                curve_info['curve'].setData(time_windowed, data_windowed)

        # Auto-range
        self.plot_widget.setXRange(time_min, current_time, padding=0)

    def _on_mouse_moved(self, pos):
        """Handle mouse move for crosshair"""
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            self.vLine.setPos(mouse_point.x())
            self.hLine.setPos(mouse_point.y())

    def clear(self):
        """Clear all data"""
        self.time_data.clear()
        for curve_info in self.curves.values():
            curve_info['data'].clear()
            curve_info['curve'].setData([], [])

    def set_window_size(self, window_size: float):
        """Set time window size"""
        self.window_size = window_size


class GreenhousePlot(TimeSeriesPlot):
    """
    Main plot: T_greenhouse and T_water
    """

    def __init__(self, parent=None):
        super().__init__(title="Greenhouse & Water Temperatures", window_size=600.0, parent=parent)

        # Setup Y-axis
        self.plot_widget.setLabel('left', 'Temperature', units='°C', color='k')

        # Add curves
        self.add_curve('T_greenhouse', color='#FF8C00', width=2.5)  # Dark orange
        self.add_curve('T_water', color='#1E90FF', width=2.5)       # Dodger blue

    def update(self, time_val: float, T_greenhouse: float, T_water: float):
        """
        Update with new data.

        Args:
            time_val: Simulation time
            T_greenhouse: Greenhouse temperature
            T_water: Water temperature
        """
        self.update_curve('T_greenhouse', time_val, T_greenhouse)
        self.update_curve('T_water', time_val, T_water)


class InputsPlot(TimeSeriesPlot):
    """
    Secondary plot: T_out and Flow
    """

    def __init__(self, parent=None):
        super().__init__(title="External Inputs", window_size=600.0, parent=parent)

        # Setup Y-axis (dual scale would be ideal, but simplified here)
        self.plot_widget.setLabel('left', 'Value', color='k')

        # Add curves
        self.add_curve('T_out', color='#808080', width=2.0)   # Gray
        self.add_curve('Flow', color='#32CD32', width=2.0)    # Lime green

    def update(self, time_val: float, T_out: float, Flow: float):
        """
        Update with new data.

        Args:
            time_val: Simulation time
            T_out: Outside temperature
            Flow: Flow control signal
        """
        self.update_curve('T_out', time_val, T_out)
        self.update_curve('Flow', time_val, Flow)
