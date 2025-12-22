"""
Frequency Response Analysis Plots
==================================

Provides plots for system analysis:
- Step Response (Transient Process / Perekhidnyi protses)
- Bode Amplitude Plot (Amplitudno-chastotna kharakterystyka)
- Bode Phase Plot (Fazovo-chastotna kharakterystyka)
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg
import numpy as np
from scipy import signal
from typing import Dict


class AnalysisWidget(QWidget):
    """
    Widget displaying frequency response analysis plots
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the analysis plots UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("System Analysis / Analiz Systemy")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #2c3e50;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Create tabs for different plots
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #34495e;
                background: white;
            }
            QTabBar::tab {
                background: #ecf0f1;
                color: #2c3e50;
                padding: 8px 20px;
                margin: 2px;
                border: 1px solid #bdc3c7;
                font-size: 11pt;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
                font-weight: bold;
            }
        """)

        # Step Response Plot
        self.step_widget = self._create_step_response_plot()
        self.tabs.addTab(self.step_widget, "Step Response (Perekhidnyi protses)")

        # Bode Amplitude Plot
        self.bode_amp_widget = self._create_bode_amplitude_plot()
        self.tabs.addTab(self.bode_amp_widget, "Amplitude Response (AChKh)")

        # Bode Phase Plot
        self.bode_phase_widget = self._create_bode_phase_plot()
        self.tabs.addTab(self.bode_phase_widget, "Phase Response (FChKh)")

        # Nyquist Plot
        self.nyquist_widget = self._create_nyquist_plot()
        self.tabs.addTab(self.nyquist_widget, "Nyquist Diagram")

        layout.addWidget(self.tabs)

    def _create_step_response_plot(self) -> QWidget:
        """Create step response plot widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Info label
        info = QLabel("Step Response: System response to unit step input (Flow: 0 -> 1)")
        info.setStyleSheet("font-size: 10pt; color: #7f8c8d; padding: 5px;")
        layout.addWidget(info)

        # Plot
        self.step_plot = pg.PlotWidget()
        self.step_plot.setBackground('w')
        self.step_plot.setLabel('left', 'Temperature', units='C', color='k')
        self.step_plot.setLabel('bottom', 'Time', units='s', color='k')
        self.step_plot.showGrid(x=True, y=True, alpha=0.3)
        self.step_plot.addLegend(offset=(10, 10))

        layout.addWidget(self.step_plot)

        return widget

    def _create_bode_amplitude_plot(self) -> QWidget:
        """Create Bode amplitude plot widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Info label
        info = QLabel("Amplitude-Frequency Characteristic (Amplitudno-chastotna kharakterystyka)")
        info.setStyleSheet("font-size: 10pt; color: #7f8c8d; padding: 5px;")
        layout.addWidget(info)

        # Plot
        self.bode_amp_plot = pg.PlotWidget()
        self.bode_amp_plot.setBackground('w')
        self.bode_amp_plot.setLabel('left', 'Magnitude', units='dB', color='k')
        self.bode_amp_plot.setLabel('bottom', 'Frequency', units='Hz', color='k')
        self.bode_amp_plot.setLogMode(x=True, y=False)
        self.bode_amp_plot.showGrid(x=True, y=True, alpha=0.3)

        layout.addWidget(self.bode_amp_plot)

        return widget

    def _create_bode_phase_plot(self) -> QWidget:
        """Create Bode phase plot widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Info label
        info = QLabel("Phase-Frequency Characteristic (Fazovo-chastotna kharakterystyka)")
        info.setStyleSheet("font-size: 10pt; color: #7f8c8d; padding: 5px;")
        layout.addWidget(info)

        # Plot
        self.bode_phase_plot = pg.PlotWidget()
        self.bode_phase_plot.setBackground('w')
        self.bode_phase_plot.setLabel('left', 'Phase', units='deg', color='k')
        self.bode_phase_plot.setLabel('bottom', 'Frequency', units='Hz', color='k')
        self.bode_phase_plot.setLogMode(x=True, y=False)
        self.bode_phase_plot.showGrid(x=True, y=True, alpha=0.3)

        layout.addWidget(self.bode_phase_plot)

        return widget

    def _create_nyquist_plot(self) -> QWidget:
        """Create Nyquist plot widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Info label
        info = QLabel("Nyquist Diagram: Real vs Imaginary frequency response")
        info.setStyleSheet("font-size: 10pt; color: #7f8c8d; padding: 5px;")
        layout.addWidget(info)

        # Plot
        self.nyquist_plot = pg.PlotWidget()
        self.nyquist_plot.setBackground('w')
        self.nyquist_plot.setLabel('left', 'Imaginary', color='k')
        self.nyquist_plot.setLabel('bottom', 'Real', color='k')
        self.nyquist_plot.showGrid(x=True, y=True, alpha=0.3)
        self.nyquist_plot.setAspectLocked(True)

        # Add unit circle reference
        theta = np.linspace(0, 2*np.pi, 100)
        circle_x = np.cos(theta)
        circle_y = np.sin(theta)
        self.nyquist_plot.plot(circle_x, circle_y, pen=pg.mkPen('gray', style=Qt.PenStyle.DashLine, width=1))

        layout.addWidget(self.nyquist_plot)

        return widget

    def update_analysis(self, params: Dict):
        """
        Update all analysis plots based on current system parameters

        Args:
            params: Dictionary with K, T1, T2, L, Kz, TambRef
        """
        K = params.get('K', 41.67)
        T1 = params.get('T1', 120.0)
        T2 = params.get('T2', 60.0)
        L = params.get('L', 10.0)
        Kz = params.get('Kz', 1.0)
        TambRef = params.get('TambRef', 0.0)

        # Create transfer function (without delay for frequency analysis)
        # H(s) = 1 / (T1*T2*s^2 + (T1+T2)*s + 1)
        num = [1.0]
        den = [T1*T2, T1+T2, 1.0]
        sys = signal.TransferFunction(num, den)

        # 1. Step Response
        self._update_step_response(K, T1, T2, L, Kz, TambRef)

        # 2. Bode Plots
        self._update_bode_plots(sys, K)

        # 3. Nyquist Plot
        self._update_nyquist_plot(sys, K)

    def _update_step_response(self, K: float, T1: float, T2: float, L: float, Kz: float, TambRef: float):
        """Calculate and plot step response"""
        # Simulate step response
        duration = max(1200.0, 10 * T1)  # At least 10*T1 for settling
        dt = 0.5
        time_points = np.arange(0, duration, dt)

        # Transfer function
        num = [1.0]
        den = [T1*T2, T1+T2, 1.0]
        sys = signal.TransferFunction(num, den)

        # Step response
        t_resp, y_resp = signal.step(sys, T=time_points)

        # Scale by gain K (assuming unit step in Flow)
        y_resp = K * y_resp

        # Add delay effect (shift the response)
        delay_samples = int(L / dt)
        y_delayed = np.zeros_like(y_resp)
        if delay_samples < len(y_resp):
            y_delayed[delay_samples:] = y_resp[:-delay_samples] if delay_samples > 0 else y_resp

        # Clear and plot
        self.step_plot.clear()
        self.step_plot.plot(t_resp, y_delayed, pen=pg.mkPen('#3498db', width=2.5), name=f'T_greenhouse (K={K:.1f})')

        # Add settling time line
        settling_idx = np.where(np.abs(y_delayed - y_delayed[-1]) < 0.02 * y_delayed[-1])[0]
        if len(settling_idx) > 0:
            settling_time = t_resp[settling_idx[0]]
            self.step_plot.addLine(x=settling_time, pen=pg.mkPen('r', style=Qt.PenStyle.DashLine, width=1.5),
                                   label=f'Settling time: {settling_time:.0f}s')

        # Add final value line
        self.step_plot.addLine(y=y_delayed[-1], pen=pg.mkPen('g', style=Qt.PenStyle.DashLine, width=1.5),
                               label=f'Steady-state: {y_delayed[-1]:.1f}C')

    def _update_bode_plots(self, sys, K: float):
        """Calculate and plot Bode diagrams"""
        # Frequency range (logarithmic)
        frequencies = np.logspace(-5, -1, 500)  # 0.00001 to 0.1 Hz

        # Frequency response
        w = 2 * np.pi * frequencies  # Convert Hz to rad/s
        w_resp, h_resp = signal.freqresp(sys, w=w)

        # Scale by gain
        h_resp = K * h_resp

        # Magnitude in dB
        magnitude_db = 20 * np.log10(np.abs(h_resp))

        # Phase in degrees
        phase_deg = np.angle(h_resp, deg=True)

        # Plot amplitude
        self.bode_amp_plot.clear()
        self.bode_amp_plot.plot(frequencies, magnitude_db, pen=pg.mkPen('#e74c3c', width=2.5))
        self.bode_amp_plot.addLine(y=0, pen=pg.mkPen('gray', style=Qt.PenStyle.DashLine, width=1))

        # Plot phase
        self.bode_phase_plot.clear()
        self.bode_phase_plot.plot(frequencies, phase_deg, pen=pg.mkPen('#9b59b6', width=2.5))
        self.bode_phase_plot.addLine(y=-180, pen=pg.mkPen('gray', style=Qt.PenStyle.DashLine, width=1))
        self.bode_phase_plot.addLine(y=-90, pen=pg.mkPen('gray', style=Qt.PenStyle.DashLine, width=1))

    def _update_nyquist_plot(self, sys, K: float):
        """Calculate and plot Nyquist diagram"""
        # Frequency range
        frequencies = np.logspace(-5, 0, 1000)
        w = 2 * np.pi * frequencies

        # Frequency response
        w_resp, h_resp = signal.freqresp(sys, w=w)
        h_resp = K * h_resp

        # Real and imaginary parts
        real_part = np.real(h_resp)
        imag_part = np.imag(h_resp)

        # Plot
        self.nyquist_plot.clear()

        # Re-add unit circle
        theta = np.linspace(0, 2*np.pi, 100)
        circle_x = np.cos(theta)
        circle_y = np.sin(theta)
        self.nyquist_plot.plot(circle_x, circle_y, pen=pg.mkPen('gray', style=Qt.PenStyle.DashLine, width=1))

        # Plot Nyquist curve
        self.nyquist_plot.plot(real_part, imag_part, pen=pg.mkPen('#16a085', width=2.5))

        # Add critical point (-1, 0)
        self.nyquist_plot.plot([-1], [0], pen=None, symbol='o', symbolSize=10,
                               symbolBrush='r', symbolPen='r')
