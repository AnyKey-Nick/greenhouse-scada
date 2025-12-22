"""
Professional SCADA-Style Main Window (TRACE MODE Style)
========================================================

Industrial-quality HMI with realistic graphics and animations.
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QToolBar, QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
                              QStatusBar, QFrame, QTabWidget, QGroupBox, QGridLayout,
                              QFileDialog, QMessageBox, QSplitter, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QTime, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QFont, QPalette, QColor
import time

from .scada_widgets import (StatusLED, AnalogGauge, DigitalDisplay)
from .scada_widgets_improved import (Pipe, Valve, HeatExchanger, Pump, ProcessTag)
from .plots import GreenhousePlot, InputsPlot
from .analysis_plots import AnalysisWidget
from .formula_tab import FormulaTab
from .calculations_tab import CalculationsTab
from .process_graphics import ProcessOverviewScene, ProcessOverviewView
from controllers import Controller, ControllerType, AntiWindupMode
from alarm_config import AlarmManager


class SCADAMainWindow(QMainWindow):
    """Professional SCADA-style main window"""

    closed = pyqtSignal()

    def __init__(self, model, channels, presets_module):
        super().__init__()
        self.model = model
        self.channels = channels
        self.presets = presets_module

        # Simulation state
        self.running = False
        self.speed_multiplier = 1.0
        self.last_wall_time = None

        # Language state (default: English)
        self.language = 'en'  # 'en' or 'uk'

        # Controller for automatic temperature control
        self.controller = Controller(
            controller_type=ControllerType.PI,
            Kp=0.05,          # Proportional gain
            Ki=0.005,         # Integral gain
            Kd=0.0,           # Derivative gain (not used in PI mode)
            setpoint=22.0,    # Target: 22°C
            output_min=0.0,   # Min flow
            output_max=1.0,   # Max flow
            anti_windup=AntiWindupMode.BACK_CALCULATION
        )
        self.auto_mode = False  # Manual mode by default

        # Alarm Manager - configurable alarm system with hysteresis
        self.alarm_manager = AlarmManager()

        # Setup dark theme
        self._setup_theme()

        # Setup UI
        self._setup_ui()
        self._create_toolbar()
        self._create_statusbar()

        # Simulation timer
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self._on_timer_tick)
        self.timer_interval_ms = 50  # 20 Hz UI update

        # Subscribe to channel updates
        self.channels.subscribe(self._on_channel_update)

        # Initial update
        self._update_display()

        # Initialize analysis plots
        self._update_analysis_plots()

        # Start clock
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)

    def _setup_theme(self):
        """Setup BRIGHT industrial theme - IMPROVED VISIBILITY"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(200, 210, 220))  # Light blue-gray
        palette.setColor(QPalette.ColorRole.WindowText, QColor(20, 20, 20))  # Dark text
        palette.setColor(QPalette.ColorRole.Base, QColor(240, 245, 250))  # Almost white
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(220, 230, 240))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 200))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(20, 20, 20))
        palette.setColor(QPalette.ColorRole.Button, QColor(180, 190, 200))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(20, 20, 20))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(70, 130, 180))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

        self.setPalette(palette)

        # Set application-wide stylesheet - BRIGHT THEME
        self.setStyleSheet("""
            QMainWindow {
                background-color: #c8d6e5;
            }
            QToolBar {
                background-color: #5a6f80;
                border-bottom: 2px solid #2c3e50;
                spacing: 5px;
                padding: 3px;
            }
            QToolButton {
                background-color: #7f8c8d;
                border: 1px solid #34495e;
                border-radius: 3px;
                padding: 5px;
                color: #ecf0f1;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #95a5a6;
                border: 1px solid #2c3e50;
            }
            QToolButton:pressed {
                background-color: #34495e;
            }
            QPushButton {
                background-color: #3498db;
                border: 2px solid #2980b9;
                border-radius: 5px;
                padding: 6px 12px;
                color: white;
                min-width: 70px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5dade2;
                border: 2px solid #3498db;
            }
            QPushButton:pressed {
                background-color: #2874a6;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
                color: #bdc3c7;
            }
            QGroupBox {
                border: 2px solid #34495e;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #34495e;
            }
            QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: white;
                border: 2px solid #7f8c8d;
                border-radius: 3px;
                padding: 3px;
                color: #2c3e50;
                font-weight: bold;
            }
            QStatusBar {
                background-color: #34495e;
                border-top: 2px solid #2c3e50;
                color: #ecf0f1;
                font-weight: bold;
            }
            QFrame {
                background-color: #ecf0f1;
                border: 2px solid #7f8c8d;
            }
            QTabWidget::pane {
                border: 2px solid #34495e;
                background-color: #ecf0f1;
            }
            QTabBar::tab {
                background-color: #95a5a6;
                border: 2px solid #7f8c8d;
                padding: 8px 20px;
                margin-right: 2px;
                color: #2c3e50;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
                border-bottom: 3px solid #2980b9;
            }
        """)

    def _setup_ui(self):
        """Setup main user interface"""
        self.setWindowTitle("Greenhouse Heating System - SCADA HMI")
        self.setGeometry(50, 50, 1600, 900)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Main horizontal splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: Process overview
        left_panel = self._create_process_panel()
        main_splitter.addWidget(left_panel)

        # Right side: Trends and controls
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)

        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 1)

        main_layout.addWidget(main_splitter)

    def _create_process_panel(self):
        """Create process overview panel with scalable QGraphicsView"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Info label about zoom and controls
        info_label = QLabel("🔍 Ctrl+Wheel: Zoom  |  Double-click: Reset  |  Drag: Pan")
        info_label.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 5px; font-size: 11px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        # Create process scene and view
        self.process_scene = ProcessOverviewScene()
        self.process_view = ProcessOverviewView(self.process_scene)
        self.process_view.setMinimumSize(800, 450)  # Minimum 16:9 aspect ratio

        # Connect click signals for interactivity
        self.process_scene.tagClicked.connect(self._on_tag_clicked)
        self.process_scene.valveClicked.connect(self._on_valve_clicked)
        self.process_scene.hexClicked.connect(self._on_hex_clicked)
        self.process_scene.sensorClicked.connect(self._on_sensor_clicked)

        layout.addWidget(self.process_view, stretch=1)

        # Status LEDs
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(0, 0, 0, 0)

        self.led_system = StatusLED("SYSTEM")
        self.led_heating = StatusLED("HEATING")
        self.led_alarm = StatusLED("ALARM")
        self.led_alarm.color_on = QColor(255, 0, 0)  # Red for alarm

        status_layout.addWidget(self.led_system)
        status_layout.addWidget(self.led_heating)
        status_layout.addWidget(self.led_alarm)
        status_layout.addStretch()

        layout.addWidget(status_frame)

        # Analog gauges - corrected labels per diploma
        gauge_frame = QFrame()
        gauge_layout = QHBoxLayout(gauge_frame)
        gauge_layout.setContentsMargins(0, 0, 0, 0)

        self.gauge_tgh = AnalogGauge("T_AIR_OUT", 0, 50, "°C")  # Outlet air 0-50°C
        self.gauge_tw = AnalogGauge("T_COND", 0, 120, "°C")  # Condensate 0-120°C
        self.gauge_flow = AnalogGauge("VALVE", 0, 1, "")  # Valve 0-1

        gauge_layout.addWidget(self.gauge_tgh)
        gauge_layout.addWidget(self.gauge_tw)
        gauge_layout.addWidget(self.gauge_flow)
        gauge_layout.addStretch()

        layout.addWidget(gauge_frame)

        return panel

    def _create_right_panel(self):
        """Create right panel with trends and controls"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Tabs for different views
        self.right_tabs = QTabWidget()

        # Tab 1: Trends
        trends_tab = self._create_trends_tab()
        self.right_tabs.addTab(trends_tab, "Trends")

        # Tab 2: Analysis (Frequency Response)
        self.analysis_widget = AnalysisWidget()
        self.right_tabs.addTab(self.analysis_widget, "Analysis (AChKh/FChKh)")

        # Tab 3: Formula
        self.formula_tab = FormulaTab(language=self.language)
        self.right_tabs.addTab(self.formula_tab, "Formula")

        # Tab 4: Calculations
        self.calculations_tab = CalculationsTab(language=self.language)
        self.right_tabs.addTab(self.calculations_tab, "Calculations")

        # Tab 5: Controls
        controls_tab = self._create_controls_tab()
        self.right_tabs.addTab(controls_tab, "Controls")

        # Tab 4: Alarms
        alarms_tab = self._create_alarms_tab()
        self.right_tabs.addTab(alarms_tab, "Alarms")

        layout.addWidget(self.right_tabs)

        return panel

    def _create_trends_tab(self):
        """Create trends tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Digital displays - corrected labels per diploma
        display_frame = QFrame()
        display_layout = QHBoxLayout(display_frame)

        self.display_tgh = DigitalDisplay("T_AIR_OUT (THK-0083)", "°C", 1)
        self.display_tw = DigitalDisplay("T_CONDENSATE", "°C", 1)
        self.display_tout = DigitalDisplay("T_AIR_IN", "°C", 1)

        display_layout.addWidget(self.display_tgh)
        display_layout.addWidget(self.display_tw)
        display_layout.addWidget(self.display_tout)

        layout.addWidget(display_frame)

        # Plots
        self.greenhouse_plot = GreenhousePlot()
        self.inputs_plot = InputsPlot()

        layout.addWidget(self.greenhouse_plot)
        layout.addWidget(self.inputs_plot)

        return widget

    def _create_controls_tab(self):
        """Create controls tab"""
        # Main container widget with scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        widget = QWidget()
        widget.setStyleSheet("""
            QLabel { color: #2c3e50; font-weight: bold; }
            QGroupBox {
                color: #2c3e50;
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #34495e;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #1976d2;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinAndMaxSize)

        # Parameters group
        params_group = QGroupBox("Model Parameters")
        params_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        params_layout = QGridLayout()
        params_layout.setColumnStretch(0, 0)
        params_layout.setColumnStretch(1, 1)
        params_layout.setHorizontalSpacing(10)
        params_layout.setVerticalSpacing(6)
        params_layout.setContentsMargins(12, 14, 12, 12)

        param_names = ['K', 'T1', 'T2', 'L', 'Kz', 'TambRef', 'KUW', 'TW']
        self.param_spinboxes = {}

        for i, name in enumerate(param_names):
            label = QLabel(f"{name}:")
            label.setMinimumWidth(140)
            label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

            # Use QSpinBox for all, scale values internally
            spinbox = QSpinBox()
            spinbox.setMinimumHeight(28)

            # Configure range
            if name in ['K', 'Kz', 'KUW']:
                spinbox.setRange(0, 200)
                spinbox.setSingleStep(1)
                spinbox.setSuffix(" %")
            elif name == 'TambRef':
                spinbox.setRange(-50, 50)
                spinbox.setSingleStep(1)
            else:
                spinbox.setRange(1, 500)
                spinbox.setSingleStep(1)

            # Set default values
            default_values = {'K': 80, 'T1': 120, 'T2': 60, 'L': 10,
                            'Kz': 2, 'TambRef': 0, 'KUW': 50, 'TW': 90}
            spinbox.setValue(default_values.get(name, 10))

            # Connect with proper scaling
            if name in ['K', 'Kz', 'KUW']:
                spinbox.valueChanged.connect(lambda v, n=name: self._on_param_changed(n, v/100.0))
            else:
                spinbox.valueChanged.connect(lambda v, n=name: self._on_param_changed(n, float(v)))

            params_layout.addWidget(label, i, 0)
            params_layout.addWidget(spinbox, i, 1)

            self.param_spinboxes[name] = spinbox

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # Inputs group
        inputs_group = QGroupBox("Process Inputs")
        inputs_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        inputs_layout = QGridLayout()
        inputs_layout.setColumnStretch(0, 0)
        inputs_layout.setColumnStretch(1, 1)
        inputs_layout.setHorizontalSpacing(10)
        inputs_layout.setVerticalSpacing(6)
        inputs_layout.setContentsMargins(12, 14, 12, 12)

        # Helper to create properly sized label
        def make_input_label(text, min_width=140):
            lbl = QLabel(text)
            lbl.setMinimumWidth(min_width)
            lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            return lbl

        # T_out
        inputs_layout.addWidget(make_input_label("T_out (°C):"), 0, 0)
        self.spin_tout = QSpinBox()
        self.spin_tout.setRange(-50, 50)
        self.spin_tout.setValue(10)
        self.spin_tout.setMinimumHeight(28)
        self.spin_tout.valueChanged.connect(lambda v: setattr(self.channels, 'T_out', float(v)))
        inputs_layout.addWidget(self.spin_tout, 0, 1)

        # Flow - CANONICAL: Internal 0.0-1.0 (normalized valve opening), Display 0-100%
        inputs_layout.addWidget(make_input_label("Flow (valve):"), 1, 0)
        self.spin_flow = QSpinBox()
        self.spin_flow.setRange(0, 100)
        self.spin_flow.setValue(60)
        self.spin_flow.setSuffix(" %")
        self.spin_flow.setMinimumHeight(28)  # Ensure readable height
        self.spin_flow.setToolTip("Valve opening: 0% = closed, 100% = fully open")
        self.spin_flow.valueChanged.connect(lambda v: setattr(self.channels, 'Flow', v/100.0))
        inputs_layout.addWidget(self.spin_flow, 1, 1)

        # dt - FIXED: Use QDoubleSpinBox for proper seconds display
        inputs_layout.addWidget(make_input_label("dt (timestep):"), 2, 0)
        self.spin_dt = QDoubleSpinBox()
        self.spin_dt.setRange(0.01, 10.0)
        self.spin_dt.setDecimals(2)
        self.spin_dt.setSingleStep(0.1)
        self.spin_dt.setValue(0.5)  # Default 0.5 seconds
        self.spin_dt.setSuffix(" s")
        self.spin_dt.setMinimumHeight(28)
        self.spin_dt.setToolTip("Simulation timestep in SECONDS (e.g., 0.5 = 500ms)")
        self.spin_dt.valueChanged.connect(lambda v: self._on_dt_changed(v))  # Direct value in seconds!
        inputs_layout.addWidget(self.spin_dt, 2, 1)

        inputs_group.setLayout(inputs_layout)
        layout.addWidget(inputs_group)

        # === VERIFICATION PANEL ===
        verify_group = QGroupBox("🔍 CONTROLLER VERIFICATION (Live Status)")
        verify_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        verify_group.setStyleSheet("""
            QGroupBox {
                color: #3498db;
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #2980b9;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                background: #ecf0f1;
            }
            QGroupBox::title {
                color: #2980b9;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        verify_layout = QGridLayout()
        verify_layout.setColumnStretch(0, 0)
        verify_layout.setColumnStretch(1, 1)
        verify_layout.setHorizontalSpacing(10)
        verify_layout.setVerticalSpacing(6)
        verify_layout.setContentsMargins(12, 14, 12, 12)

        # Helper to create properly sized label
        def make_label(text, min_width=140):
            lbl = QLabel(text)
            lbl.setMinimumWidth(min_width)
            lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            return lbl

        verify_layout.addWidget(make_label("Mode:"), 0, 0)
        self.verify_mode_label = QLabel("MANUAL")
        self.verify_mode_label.setStyleSheet("color: #95a5a6; font-weight: bold; font-size: 12px; padding: 2px 6px;")
        self.verify_mode_label.setMinimumHeight(24)
        verify_layout.addWidget(self.verify_mode_label, 0, 1)

        verify_layout.addWidget(make_label("PV (THK-0083):"), 1, 0)
        self.verify_pv_label = QLabel("--")
        self.verify_pv_label.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 12px; padding: 2px 6px;")
        self.verify_pv_label.setMinimumHeight(24)
        verify_layout.addWidget(self.verify_pv_label, 1, 1)

        verify_layout.addWidget(make_label("SP (setpoint):"), 2, 0)
        self.verify_sp_label = QLabel("--")
        self.verify_sp_label.setStyleSheet("color: #16a085; font-weight: bold; font-size: 12px; padding: 2px 6px;")
        self.verify_sp_label.setMinimumHeight(24)
        verify_layout.addWidget(self.verify_sp_label, 2, 1)

        verify_layout.addWidget(make_label("Error (SP-PV):"), 3, 0)
        self.verify_error_label = QLabel("--")
        self.verify_error_label.setStyleSheet("color: #e67e22; font-weight: bold; font-size: 12px; padding: 2px 6px;")
        self.verify_error_label.setMinimumHeight(24)
        verify_layout.addWidget(self.verify_error_label, 3, 1)

        verify_layout.addWidget(make_label("P term:"), 4, 0)
        self.verify_p_label = QLabel("--")
        self.verify_p_label.setStyleSheet("color: #3498db; font-weight: bold; font-size: 11px; padding: 2px 6px;")
        self.verify_p_label.setMinimumHeight(24)
        verify_layout.addWidget(self.verify_p_label, 4, 1)

        verify_layout.addWidget(make_label("I term:"), 5, 0)
        self.verify_i_label = QLabel("--")
        self.verify_i_label.setStyleSheet("color: #9b59b6; font-weight: bold; font-size: 11px; padding: 2px 6px;")
        self.verify_i_label.setMinimumHeight(24)
        verify_layout.addWidget(self.verify_i_label, 5, 1)

        verify_layout.addWidget(make_label("D term:"), 6, 0)
        self.verify_d_label = QLabel("--")
        self.verify_d_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 11px; padding: 2px 6px;")
        self.verify_d_label.setMinimumHeight(24)
        verify_layout.addWidget(self.verify_d_label, 6, 1)

        verify_layout.addWidget(make_label("Output (Flow):"), 7, 0)
        self.verify_output_label = QLabel("--")
        self.verify_output_label.setStyleSheet("color: #8e44ad; font-weight: bold; font-size: 12px; padding: 2px 6px;")
        self.verify_output_label.setMinimumHeight(24)
        verify_layout.addWidget(self.verify_output_label, 7, 1)

        verify_layout.addWidget(make_label("Saturation:"), 8, 0)
        self.verify_saturation_label = QLabel("--")
        self.verify_saturation_label.setStyleSheet("color: #c0392b; font-weight: bold; font-size: 12px; padding: 2px 6px;")
        self.verify_saturation_label.setMinimumHeight(24)
        verify_layout.addWidget(self.verify_saturation_label, 8, 1)

        verify_layout.addWidget(make_label("Alarms:"), 9, 0)
        self.verify_alarms_label = QLabel("--")
        self.verify_alarms_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 12px; padding: 2px 6px;")
        self.verify_alarms_label.setMinimumHeight(24)
        verify_layout.addWidget(self.verify_alarms_label, 9, 1)

        verify_group.setLayout(verify_layout)
        layout.addWidget(verify_group)

        # Controller group
        pi_group = QGroupBox("🎯 Controller (P/PI/PID)")
        pi_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        pi_group.setStyleSheet("""
            QGroupBox {
                color: #2ecc71;
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #27ae60;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                color: #2ecc71;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        pi_layout = QGridLayout()
        pi_layout.setColumnStretch(0, 0)
        pi_layout.setColumnStretch(1, 1)
        pi_layout.setHorizontalSpacing(10)
        pi_layout.setVerticalSpacing(6)
        pi_layout.setContentsMargins(12, 14, 12, 12)

        # Helper to create properly sized label
        def make_ctrl_label(text, min_width=140):
            lbl = QLabel(text)
            lbl.setMinimumWidth(min_width)
            lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            return lbl

        # Controller Type selector
        pi_layout.addWidget(make_ctrl_label("Type:"), 0, 0)
        self.controller_type_combo = QComboBox()
        self.controller_type_combo.addItems(["P", "PI", "PID"])
        self.controller_type_combo.setCurrentText("PI")
        self.controller_type_combo.setMinimumHeight(28)
        self.controller_type_combo.currentTextChanged.connect(self._on_controller_type_changed)
        pi_layout.addWidget(self.controller_type_combo, 0, 1)

        # Auto/Manual toggle
        pi_layout.addWidget(make_ctrl_label("Mode:"), 1, 0)
        self.auto_manual_btn = QPushButton("MANUAL")
        self.auto_manual_btn.setCheckable(True)
        self.auto_manual_btn.setMinimumHeight(32)
        self.auto_manual_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
                min-height: 28px;
            }
            QPushButton:checked {
                background-color: #27ae60;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:checked:hover {
                background-color: #229954;
            }
        """)
        self.auto_manual_btn.clicked.connect(self._toggle_auto_manual)
        pi_layout.addWidget(self.auto_manual_btn, 1, 1)

        # Setpoint - FIX: Was incorrectly at (1,1) overwriting the auto_manual button!
        pi_layout.addWidget(make_ctrl_label("Уставка T (°C):"), 2, 0)
        self.spin_setpoint = QSpinBox()
        self.spin_setpoint.setRange(16, 30)
        self.spin_setpoint.setValue(22)
        self.spin_setpoint.setSuffix(" °C")
        self.spin_setpoint.setMinimumHeight(28)
        self.spin_setpoint.setStyleSheet("font-size: 14px; font-weight: bold; color: #2ecc71;")
        self.spin_setpoint.valueChanged.connect(self._on_setpoint_changed)
        pi_layout.addWidget(self.spin_setpoint, 2, 1)  # FIXED: Was (1,1), now (2,1)

        # Kp
        pi_layout.addWidget(make_ctrl_label("Kp (proportional):"), 3, 0)
        self.spin_kp = QDoubleSpinBox()
        self.spin_kp.setRange(0.0, 2.0)
        self.spin_kp.setSingleStep(0.01)
        self.spin_kp.setValue(0.05)
        self.spin_kp.setDecimals(3)
        self.spin_kp.setMinimumHeight(28)
        self.spin_kp.valueChanged.connect(lambda v: setattr(self.controller, 'Kp', v))
        pi_layout.addWidget(self.spin_kp, 3, 1)

        # Ki
        pi_layout.addWidget(make_ctrl_label("Ki (integral):"), 4, 0)
        self.spin_ki = QDoubleSpinBox()
        self.spin_ki.setRange(0.0, 0.1)
        self.spin_ki.setSingleStep(0.001)
        self.spin_ki.setValue(0.005)
        self.spin_ki.setDecimals(4)
        self.spin_ki.setMinimumHeight(28)
        self.spin_ki.valueChanged.connect(lambda v: setattr(self.controller, 'Ki', v))
        pi_layout.addWidget(self.spin_ki, 4, 1)

        # Kd (for PID mode)
        pi_layout.addWidget(make_ctrl_label("Kd (derivative):"), 5, 0)
        self.spin_kd = QDoubleSpinBox()
        self.spin_kd.setRange(0.0, 1.0)
        self.spin_kd.setSingleStep(0.001)
        self.spin_kd.setValue(0.0)
        self.spin_kd.setDecimals(4)
        self.spin_kd.setMinimumHeight(28)
        self.spin_kd.setEnabled(False)  # Disabled in PI mode
        self.spin_kd.valueChanged.connect(lambda v: setattr(self.controller, 'Kd', v))
        pi_layout.addWidget(self.spin_kd, 5, 1)

        # Controller Status display
        pi_layout.addWidget(make_ctrl_label("Error (SP-PV):"), 6, 0)
        self.pi_error_label = QLabel("--")
        self.pi_error_label.setStyleSheet("color: #3498db; font-weight: bold; padding: 2px 6px;")
        self.pi_error_label.setMinimumHeight(24)
        pi_layout.addWidget(self.pi_error_label, 6, 1)

        pi_layout.addWidget(make_ctrl_label("Integral:"), 7, 0)
        self.pi_integral_label = QLabel("--")
        self.pi_integral_label.setStyleSheet("color: #3498db; font-weight: bold; padding: 2px 6px;")
        self.pi_integral_label.setMinimumHeight(24)
        pi_layout.addWidget(self.pi_integral_label, 7, 1)

        pi_group.setLayout(pi_layout)
        layout.addWidget(pi_group)

        # Add spacing at bottom but don't use addStretch() which causes compression
        layout.addSpacing(20)
        layout.setSpacing(8)

        # Set the widget as scroll area content
        scroll_area.setWidget(widget)

        return scroll_area

    def _create_alarms_tab(self):
        """Create alarms tab with real setpoints"""
        widget = QWidget()
        widget.setStyleSheet("""
            QLabel { color: #ecf0f1; font-weight: bold; }
            QGroupBox {
                color: #ecf0f1;
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #e74c3c;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #e74c3c;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        layout = QVBoxLayout(widget)

        # Header
        header = QLabel("⚠️ ALARM LIMITS (Уставки)")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #e74c3c; padding: 10px; background: #2c3e50; border-radius: 5px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Standards info
        standards_group = QGroupBox("📋 Норми та Стандарти")
        standards_layout = QVBoxLayout()
        standards_layout.addWidget(QLabel("ДСТУ 2860-94: Теплиці. Загальні технічні умови"))
        standards_layout.addWidget(QLabel("СНиП 2.10.04-85: Теплиці та парники"))
        standards_layout.addWidget(QLabel("ГОСТ 12.1.005-88: Загальні санітарно-гігієнічні вимоги"))
        standards_layout.addWidget(QLabel(""))
        norm_label = QLabel("📌 НОРМА для овочевих теплиць: 18-25°C")
        norm_label.setStyleSheet("color: #3498db; font-weight: bold; font-size: 12px;")
        standards_layout.addWidget(norm_label)
        optimal_label = QLabel("✅ ОПТИМАЛЬНА температура: 20-24°C")
        optimal_label.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 12px;")
        standards_layout.addWidget(optimal_label)
        standards_group.setLayout(standards_layout)
        layout.addWidget(standards_group)

        # Temperature alarms
        temp_group = QGroupBox("🌡️ Уставки температури")
        temp_layout = QGridLayout()
        temp_layout.setColumnStretch(0, 1)
        temp_layout.setColumnStretch(1, 1)

        # Min alarm
        min_label = QLabel("⚠️ Нижня межа:")
        min_label.setStyleSheet("color: #f39c12;")
        temp_layout.addWidget(min_label, 0, 0)
        temp_layout.addWidget(QLabel("20.0 °C"), 0, 1)

        # Setpoint
        sp_label = QLabel("🎯 Уставка (Setpoint):")
        sp_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
        temp_layout.addWidget(sp_label, 1, 0)
        self.alarm_setpoint_label = QLabel("22.0 °C")
        self.alarm_setpoint_label.setStyleSheet("color: #2ecc71; font-size: 16px; font-weight: bold;")
        temp_layout.addWidget(self.alarm_setpoint_label, 1, 1)

        # Max alarm
        max_label = QLabel("⚠️ Верхня межа:")
        max_label.setStyleSheet("color: #f39c12;")
        temp_layout.addWidget(max_label, 2, 0)
        temp_layout.addWidget(QLabel("24.0 °C"), 2, 1)

        temp_group.setLayout(temp_layout)
        layout.addWidget(temp_group)

        # Flow alarms
        flow_group = QGroupBox("💧 Уставки потоку пари")
        flow_layout = QGridLayout()
        flow_layout.setColumnStretch(0, 1)
        flow_layout.setColumnStretch(1, 1)

        flow_layout.addWidget(QLabel("⚠️ Мінімум:"), 0, 0)
        flow_layout.addWidget(QLabel("0.70 кг/с"), 0, 1)

        flow_sp_label = QLabel("🎯 Уставка (розрахунок):")
        flow_sp_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
        flow_layout.addWidget(flow_sp_label, 1, 0)
        flow_sp_value = QLabel("0.86 кг/с")
        flow_sp_value.setStyleSheet("color: #2ecc71; font-size: 16px; font-weight: bold;")
        flow_layout.addWidget(flow_sp_value, 1, 1)

        flow_layout.addWidget(QLabel("⚠️ Максимум:"), 2, 0)
        flow_layout.addWidget(QLabel("1.00 кг/с"), 2, 1)

        flow_group.setLayout(flow_layout)
        layout.addWidget(flow_group)

        # Active alarms display - LARGER
        self.alarms_display = QLabel("✅ Система в нормі\nSystem OK\nВсі параметри в межах норми")
        self.alarms_display.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.alarms_display.setStyleSheet("color: white; padding: 20px; background: #27ae60; border-radius: 8px; border: 3px solid #2ecc71;")
        self.alarms_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.alarms_display.setMinimumHeight(100)
        layout.addWidget(self.alarms_display)

        # Current values display
        current_group = QGroupBox("📊 Поточні значення")
        current_layout = QGridLayout()
        current_layout.addWidget(QLabel("T теплиці:"), 0, 0)
        self.current_temp_label = QLabel("-- °C")
        self.current_temp_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #3498db;")
        current_layout.addWidget(self.current_temp_label, 0, 1)

        current_layout.addWidget(QLabel("Потік пари:"), 1, 0)
        self.current_flow_label = QLabel("-- кг/с")
        self.current_flow_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #3498db;")
        current_layout.addWidget(self.current_flow_label, 1, 1)

        current_group.setLayout(current_layout)
        layout.addWidget(current_group)

        # Parameters info
        info_group = QGroupBox("🏗️ Технічні параметри теплиці")
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel("Розміри: 15 м × 7 м × 2.5 м"))
        info_layout.addWidget(QLabel("Об'єм: 262.5 м³"))
        info_layout.addWidget(QLabel("Маса повітря: 315 кг"))
        info_layout.addWidget(QLabel("Необхідний підігрів: ΔT = 16°C → 22°C (6°C)"))
        info_layout.addWidget(QLabel("Потрібна теплота: Q = 1944.8 кДж"))
        info_layout.addWidget(QLabel("Площа теплообміну: 3890 м²"))
        info_layout.addWidget(QLabel("Кількість трубок HEX: 513 шт"))
        info_layout.addWidget(QLabel("Матеріал трубок: латунь (C_ct = 0.4 кДж/(кг·°C))"))
        info_layout.addWidget(QLabel("Коефіцієнт тепловіддачі: α = 13.7 кДж/(м²·с·°C)"))
        info_layout.addWidget(QLabel("Теплота пароутворення: r = 2095 кДж/кг"))
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        layout.addStretch()
        return widget

    def _create_toolbar(self):
        """Create main toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Run button
        self.action_run = QAction("▶ RUN", self)
        self.action_run.triggered.connect(self._on_run)
        toolbar.addAction(self.action_run)

        # Pause button
        self.action_pause = QAction("⏸ PAUSE", self)
        self.action_pause.triggered.connect(self._on_pause)
        self.action_pause.setEnabled(False)
        toolbar.addAction(self.action_pause)

        # Stop button
        self.action_stop = QAction("⏹ STOP", self)
        self.action_stop.triggered.connect(self._on_stop)
        toolbar.addAction(self.action_stop)

        toolbar.addSeparator()

        # Speed control
        toolbar.addWidget(QLabel(" Speed: "))
        self.combo_speed = QComboBox()
        self.combo_speed.addItems(["×1", "×5", "×10"])
        self.combo_speed.currentTextChanged.connect(self._on_speed_changed)
        toolbar.addWidget(self.combo_speed)

        toolbar.addSeparator()

        # Preset selector
        toolbar.addWidget(QLabel(" Preset: "))
        self.combo_preset = QComboBox()
        self.combo_preset.addItems(['default', 'winter', 'summer', 'fast', 'slow'])
        toolbar.addWidget(self.combo_preset)

        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self._on_load_preset)
        toolbar.addWidget(load_btn)

        toolbar.addSeparator()

        # Language toggle
        self.lang_btn = QPushButton("🌐 Українська")
        self.lang_btn.clicked.connect(self._toggle_language)
        toolbar.addWidget(self.lang_btn)

        toolbar.addSeparator()

        # Export
        export_btn = QPushButton("💾 Export CSV")
        export_btn.clicked.connect(self._on_save_csv)
        toolbar.addWidget(export_btn)

        toolbar.addSeparator()

        toolbar.addWidget(QLabel("   "))  # Spacer

    def _create_statusbar(self):
        """Create status bar"""
        self.status_sim_time = QLabel("Sim Time: 0.0 s")
        self.status_state = QLabel("State: STOPPED")
        self.status_clock = QLabel("")

        self.statusBar().addWidget(self.status_sim_time)
        self.statusBar().addPermanentWidget(self.status_state)
        self.statusBar().addPermanentWidget(self.status_clock)

    def _update_clock(self):
        """Update clock display"""
        current_time = QTime.currentTime().toString("HH:mm:ss")
        self.status_clock.setText(f"  {current_time}")

    # ========== Simulation Control ==========

    def _on_run(self):
        """Start simulation"""
        if not self.running:
            self.running = True
            self.last_wall_time = time.time()
            self.sim_timer.start(self.timer_interval_ms)

            self.action_run.setEnabled(False)
            self.action_pause.setEnabled(True)

            self.led_system.setState(True)
            self.led_heating.setState(True)
            self.pipe1.setActive(True)
            self.pipe2.setActive(True)
            self.pipe3.setActive(True)
            self.pipe_air_in.setActive(True)
            self.pipe_air_out.setActive(True)

            self.status_state.setText("State: RUNNING")

    def _on_pause(self):
        """Pause simulation"""
        if self.running:
            self.running = False
            self.sim_timer.stop()

            self.action_run.setEnabled(True)
            self.action_pause.setEnabled(False)

            self.led_heating.setState(False)

            self.status_state.setText("State: PAUSED")

    def _on_stop(self):
        """Stop and reset simulation"""
        was_running = self.running
        if self.running:
            self._on_pause()

        # Reset model
        from model import ModelState
        initial_state = ModelState(x1=20.0, x2=0.0, T_condensate=100.0)
        self.model.reset(initial_state)
        self.channels.reset()

        # Clear plots
        self.greenhouse_plot.clear()
        self.inputs_plot.clear()

        # Reset widgets
        self.pump_widget.setRunning(False)
        self.pipe1.setActive(False)
        self.pipe2.setActive(False)
        self.pipe3.setActive(False)
        self.led_system.setState(False)
        self.led_heating.setState(False)

        self.status_state.setText("State: STOPPED")
        self.status_sim_time.setText("Sim Time: 0.0 s")

        self._update_display()

    def _on_speed_changed(self, text: str):
        """Handle speed change"""
        self.speed_multiplier = float(text.replace('×', ''))

    def _on_timer_tick(self):
        """Handle simulation timer tick"""
        if not self.running:
            return

        current_wall_time = time.time()
        if self.last_wall_time is None:
            self.last_wall_time = current_wall_time
            return

        wall_dt = current_wall_time - self.last_wall_time
        self.last_wall_time = current_wall_time

        sim_dt = wall_dt * self.speed_multiplier
        dt_sec = self.channels.dt_sec
        accumulated_time = 0.0

        while accumulated_time < sim_dt:
            self._execute_step(dt_sec)
            accumulated_time += dt_sec

            if accumulated_time > 10.0:
                break

    def _execute_step(self, dt_sec: float):
        """Execute one model step with correct process variable mapping"""
        T_air_in = self.channels.T_air_in  # Inlet air temperature (ambient)

        # Use controller in auto mode, otherwise use manual Flow
        # Controller regulates outlet air temperature (measured by THK-0083)
        if self.auto_mode:
            PV = self.channels.data.T_air_out  # Process Variable: outlet air temp (THK-0083)
            Flow = self.controller.update(PV, dt_sec)
            self.channels.Flow = Flow  # Update channel with controller output
        else:
            Flow = self.channels.Flow  # Use manual Flow from spinbox

        outputs = self.model.step(T_air_in, Flow, dt_sec)

        new_sim_time = self.channels.sim_time + dt_sec
        self.channels.update_from_model(outputs, new_sim_time)

    def _on_channel_update(self, data):
        """Handle channel update"""
        self._update_display()

    def _update_display(self):
        """Update all displays with correct variable mapping"""
        data = self.channels.get_all()

        # Update process scene with correct physical values
        self.process_scene.updateValues(data.T_air_in, data.Flow, data.T_air_out, data.T_condensate)

        # Update gauges with correct labels
        self.gauge_tgh.setValue(data.T_air_out)  # Outlet air temp (THK-0083)
        self.gauge_tw.setValue(data.T_condensate)  # Condensate temp
        self.gauge_flow.setValue(data.Flow)

        # Update digital displays
        self.display_tgh.setValue(data.T_air_out)  # Outlet air
        self.display_tw.setValue(data.T_condensate)  # Condensate
        self.display_tout.setValue(data.T_air_in)  # Inlet air

        # Update plots with T_air_in and T_air_out as primary pair
        self.greenhouse_plot.update(data.sim_time, data.T_air_out, data.T_condensate)
        self.inputs_plot.update(data.sim_time, data.T_air_in, data.Flow)

        # Update status bar
        self.status_sim_time.setText(f"Sim Time: {data.sim_time:.1f} s")

        # Update controller status display
        if self.auto_mode:
            status = self.controller.get_status()
            self.pi_error_label.setText(f"{status['error']:.2f} °C")
            self.pi_integral_label.setText(f"{status['integral']:.2f}")
            # Update Flow spinbox to show controller output (convert 0-1 to 0-100%)
            self.spin_flow.setValue(int(data.Flow * 100))
        else:
            self.pi_error_label.setText("--")
            self.pi_integral_label.setText("--")

        # Update VERIFICATION PANEL
        # Mode display
        mode_text = f"AUTO-{self.controller_type_combo.currentText()}" if self.auto_mode else "MANUAL"
        self.verify_mode_label.setText(mode_text)
        if self.auto_mode:
            self.verify_mode_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 12px;")
        else:
            self.verify_mode_label.setStyleSheet("color: #95a5a6; font-weight: bold; font-size: 12px;")

        # Always show PV and SP
        self.verify_pv_label.setText(f"{data.T_air_out:.2f} °C")
        self.verify_sp_label.setText(f"{self.controller.setpoint:.2f} °C")

        if self.auto_mode:
            status = self.controller.get_status()
            error = status['error']
            self.verify_error_label.setText(f"{error:.2f} °C")

            # Display individual P, I, D terms
            ctrl_type = self.controller_type_combo.currentText()
            P_term = status['P_term']
            I_term = status['I_term']
            D_term = status['D_term']

            # P term (always active)
            self.verify_p_label.setText(f"{P_term:.4f}")
            self.verify_p_label.setStyleSheet("color: #3498db; font-weight: bold; font-size: 11px;")

            # I term (active in PI/PID)
            if ctrl_type in ["PI", "PID"]:
                self.verify_i_label.setText(f"{I_term:.4f}")
                self.verify_i_label.setStyleSheet("color: #9b59b6; font-weight: bold; font-size: 11px;")
            else:
                self.verify_i_label.setText("--")
                self.verify_i_label.setStyleSheet("color: #95a5a6; font-weight: normal; font-size: 11px;")

            # D term (active only in PID)
            if ctrl_type == "PID":
                self.verify_d_label.setText(f"{D_term:.4f}")
                self.verify_d_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 11px;")
            else:
                self.verify_d_label.setText("--")
                self.verify_d_label.setStyleSheet("color: #95a5a6; font-weight: normal; font-size: 11px;")

            self.verify_output_label.setText(f"{data.Flow:.3f} ({data.Flow*100:.1f}%)")

            # Check saturation
            if data.Flow >= 0.99:
                self.verify_saturation_label.setText("MAX (100%)")
                self.verify_saturation_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 12px;")
            elif data.Flow <= 0.01:
                self.verify_saturation_label.setText("MIN (0%)")
                self.verify_saturation_label.setStyleSheet("color: #3498db; font-weight: bold; font-size: 12px;")
            else:
                self.verify_saturation_label.setText("Normal")
                self.verify_saturation_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 12px;")
        else:
            # In manual mode, show manual Flow value
            self.verify_error_label.setText("--")
            self.verify_p_label.setText("--")
            self.verify_p_label.setStyleSheet("color: #95a5a6; font-weight: normal; font-size: 11px;")
            self.verify_i_label.setText("--")
            self.verify_i_label.setStyleSheet("color: #95a5a6; font-weight: normal; font-size: 11px;")
            self.verify_d_label.setText("--")
            self.verify_d_label.setStyleSheet("color: #95a5a6; font-weight: normal; font-size: 11px;")
            self.verify_output_label.setText(f"{data.Flow:.3f} ({data.Flow*100:.1f}%)")
            self.verify_saturation_label.setText("--")

        # Check alarms
        self._check_alarms(data)

    def _check_alarms(self, data):
        """Check alarm conditions using configurable AlarmManager with hysteresis"""

        # Update current value displays (T_air_out is the measured PV from THK-0083)
        self.current_temp_label.setText(f"{data.T_air_out:.1f} °C")
        # Flow is valve opening (0-1), display as percentage
        self.current_flow_label.setText(f"{data.Flow * 100:.0f} %")

        # Check all alarms using alarm manager
        active_alarms = self.alarm_manager.check_all_alarms(data)

        # Build alarm message list
        alarm_messages = []
        has_critical = False

        for alarm in active_alarms:
            severity = alarm['severity']
            tag = alarm['tag']
            message = alarm['message']

            # Translate to Ukrainian (handle both new and old tag names)
            if tag in ['T_air_out', 'T_greenhouse']:
                if severity in ['LOW_LOW', 'LOW']:
                    alarm_messages.append(f"⚠️ НИЗЬКА T повітря (THK-0083): {alarm['value']:.1f}°C")
                    alarm_messages.append(f"   (межа: {alarm['limit']:.1f}°C)")
                else:
                    alarm_messages.append(f"⚠️ ВИСОКА T повітря (THK-0083): {alarm['value']:.1f}°C")
                    alarm_messages.append(f"   (межа: {alarm['limit']:.1f}°C)")

                # Color code current value display
                if severity in ['HIGH_HIGH', 'LOW_LOW']:
                    self.current_temp_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c;")
                    has_critical = True
                else:
                    self.current_temp_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f39c12;")

            elif tag == 'Flow':
                # FIXED: Flow is valve opening (0-1), display as percentage
                if severity in ['LOW_LOW', 'LOW']:
                    alarm_messages.append(f"⚠️ НИЗЬКЕ відкриття клапана: {alarm['value']*100:.0f}%")
                else:
                    alarm_messages.append(f"⚠️ ВИСОКЕ відкриття клапана: {alarm['value']*100:.0f}%")
                alarm_messages.append(f"   (межа: {alarm['limit']*100:.0f}%)")

                # Color code current value display
                if severity in ['HIGH_HIGH', 'LOW_LOW']:
                    self.current_flow_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c;")
                    has_critical = True
                else:
                    self.current_flow_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f39c12;")

        # If no alarms on temperature, set to green
        if not any(a['tag'] in ['T_air_out', 'T_greenhouse'] for a in active_alarms):
            self.current_temp_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2ecc71;")

        # If no alarms on flow, set to green
        if not any(a['tag'] == 'Flow' for a in active_alarms):
            self.current_flow_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2ecc71;")

        # Update alarm display panel
        if alarm_messages:
            alarm_text = "🚨 ALARM / ТРИВОГА 🚨\n\n" + "\n".join(alarm_messages)
            self.alarms_display.setText(alarm_text)
            self.alarms_display.setStyleSheet("color: white; padding: 20px; background: #c0392b; border-radius: 8px; border: 3px solid #e74c3c;")
            self.led_alarm.setState(True)

            # Update verification panel alarm count
            alarm_count = len(active_alarms)
            self.verify_alarms_label.setText(f"{alarm_count} ACTIVE")
            self.verify_alarms_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 12px;")
        else:
            self.alarms_display.setText("✅ Система в нормі\nSystem OK\n\nВсі параметри в межах норми\nДСТУ 2860-94")
            self.alarms_display.setStyleSheet("color: white; padding: 20px; background: #27ae60; border-radius: 8px; border: 3px solid #2ecc71;")
            self.led_alarm.setState(False)

            # Update verification panel alarm count
            self.verify_alarms_label.setText("None")
            self.verify_alarms_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 12px;")

    def _toggle_auto_manual(self):
        """Toggle between AUTO/MANUAL with bumpless transfer"""
        self.auto_mode = self.auto_manual_btn.isChecked()
        if self.auto_mode:
            # Switching to AUTO mode - perform bumpless transfer
            self.auto_manual_btn.setText("AUTO ✓")
            self.auto_manual_btn.setStyleSheet("background: #27ae60; color: white; font-weight: bold;")
            self.spin_flow.setEnabled(False)  # Disable manual flow

            # Bumpless transfer: initialize controller to match current manual output
            # PV is outlet air temperature measured by THK-0083
            current_data = self.channels.get_all()
            self.controller.initialize_bumpless(
                current_output=current_data.Flow,  # Current manual Flow (0-1)
                measured_value=current_data.T_air_out  # Current outlet air temp (THK-0083 PV)
            )
            ctrl_type = self.controller_type_combo.currentText()
            self.statusBar().showMessage(f"AUTO-{ctrl_type} mode - Regulating T_air_out (THK-0083) [bumpless]", 3000)
        else:
            # Switching to MANUAL mode
            self.auto_manual_btn.setText("MANUAL")
            self.auto_manual_btn.setStyleSheet("")
            self.spin_flow.setEnabled(True)  # Enable manual flow
            self.statusBar().showMessage("MANUAL mode - operator control", 3000)

    def _on_controller_type_changed(self, type_str: str):
        """Handle controller type change (P/PI/PID)"""
        type_map = {"P": ControllerType.P, "PI": ControllerType.PI, "PID": ControllerType.PID}
        self.controller.set_type(type_map[type_str])

        # Enable/disable Kd based on type
        self.spin_kd.setEnabled(type_str == "PID")

        # Update UI labels
        if type_str == "P":
            self.statusBar().showMessage("Controller mode: P (Proportional only)", 2000)
        elif type_str == "PI":
            self.statusBar().showMessage("Controller mode: PI (Proportional-Integral)", 2000)
        else:
            self.statusBar().showMessage("Controller mode: PID (Proportional-Integral-Derivative)", 2000)

    def _on_setpoint_changed(self, value):
        """Update controller setpoint"""
        self.controller.set_setpoint(float(value))

    def _on_param_changed(self, name: str, value: float):
        """Handle parameter change"""
        self.model.set_params(dt_sec=self.channels.dt_sec, **{name: value})

        # Update analysis plots
        self._update_analysis_plots()

    def _on_dt_changed(self, value: float):
        """Handle dt change"""
        self.channels.dt_sec = value
        self.model.set_params(dt_sec=value)

    def _on_load_preset(self):
        """Load preset"""
        preset_name = self.combo_preset.currentText()
        preset = self.presets.get_preset(preset_name)

        # Apply parameters
        for name, value in preset['params'].items():
            if name in self.param_spinboxes:
                scaled_value = int(value * 100) if name in ['K', 'Kz', 'KUW'] else int(value)
                self.param_spinboxes[name].setValue(scaled_value)

        # Apply inputs
        self.spin_tout.setValue(int(preset['inputs']['T_out']))
        self.spin_flow.setValue(int(preset['inputs']['Flow'] * 100))
        self.spin_dt.setValue(preset['inputs']['dt_sec'])  # FIXED: Direct value in seconds

        self.statusBar().showMessage(f"Loaded preset: {preset_name}", 3000)

    def _on_save_csv(self):
        """Save CSV"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if filename:
            try:
                self.channels.save_csv(filename)
                self.statusBar().showMessage(f"Exported to {filename}", 3000)
            except Exception as e:
                QMessageBox.warning(self, "Export Error", f"Failed: {e}")

    def set_param_value(self, name: str, value: float):
        """Set parameter value (for config loading compatibility)"""
        if name in self.param_spinboxes:
            if name in ['K', 'Kz', 'KUW']:
                self.param_spinboxes[name].setValue(int(value * 100))
            else:
                self.param_spinboxes[name].setValue(int(value))

    def set_input_value(self, name: str, value: float):
        """Set input value (for config loading compatibility)"""
        if name == 'T_out' and hasattr(self, 'spin_tout'):
            self.spin_tout.setValue(int(value))
        elif name == 'Flow' and hasattr(self, 'spin_flow'):
            self.spin_flow.setValue(int(value * 100))
        elif name == 'dt_sec' and hasattr(self, 'spin_dt'):
            self.spin_dt.setValue(value)  # FIXED: Direct value in seconds

    def _update_analysis_plots(self):
        """Update frequency response analysis plots"""
        if hasattr(self, 'analysis_widget'):
            params = {
                'K': self.model.params.K,
                'T1': self.model.params.T1,
                'T2': self.model.params.T2,
                'L': self.model.params.L,
                'Kz': self.model.params.Kz,
                'TambRef': self.model.params.TambRef
            }
            self.analysis_widget.update_analysis(params)

    def _toggle_language(self):
        """Toggle between English and Ukrainian"""
        if self.language == 'en':
            self.language = 'uk'
            self.lang_btn.setText("🌐 English")
        else:
            self.language = 'en'
            self.lang_btn.setText("🌐 Українська")

        # Update UI text
        self._update_ui_language()

        # Update Formula tab language
        self.formula_tab.set_language(self.language)

        # Update Calculations tab language
        self.calculations_tab.set_language(self.language)

        self.statusBar().showMessage(
            "Language changed to Ukrainian" if self.language == 'uk' else "Мову змінено на англійську",
            3000
        )

    def _update_ui_language(self):
        """Update all UI text based on current language"""
        if self.language == 'uk':
            self.setWindowTitle("Система керування теплицею - SCADA")
            self.right_tabs.setTabText(0, "Тренди")
            self.right_tabs.setTabText(1, "Аналіз (АЧХ/ФЧХ)")
            self.right_tabs.setTabText(2, "Формула")
            self.right_tabs.setTabText(3, "Розрахунки")
            self.right_tabs.setTabText(4, "Керування")
            self.right_tabs.setTabText(5, "Тривоги")
            self.action_run.setText("▶ ПУСК")
            self.action_pause.setText("⏸ ПАУЗА")
            self.action_stop.setText("⏹ СТОП")
        else:
            self.setWindowTitle("Greenhouse Control System - SCADA")
            self.right_tabs.setTabText(0, "Trends")
            self.right_tabs.setTabText(1, "Analysis (AChKh/FChKh)")
            self.right_tabs.setTabText(2, "Formula")
            self.right_tabs.setTabText(3, "Calculations")
            self.right_tabs.setTabText(4, "Controls")
            self.right_tabs.setTabText(5, "Alarms")
            self.action_run.setText("▶ RUN")
            self.action_pause.setText("⏸ PAUSE")
            self.action_stop.setText("⏹ STOP")

    def _on_tag_clicked(self, tag_name):
        """Handle tag click - focus on corresponding control"""
        # Switch to Controls tab and focus on relevant control
        self.right_tabs.setCurrentIndex(4)  # Controls tab index

        # Map tag names to controls
        if "AIR IN" in tag_name or "T_OUT" in tag_name:
            self.spin_tout.setFocus()
        elif "GREENHOUSE" in tag_name or "AIR OUT" in tag_name:
            # Focus on temperature display
            pass

        self.statusBar().showMessage(f"Clicked: {tag_name}", 2000)

    def _on_valve_clicked(self):
        """Handle valve click - focus on Flow control"""
        self.right_tabs.setCurrentIndex(4)  # Controls tab
        if not self.auto_mode:
            self.spin_flow.setFocus()
        else:
            # Focus on setpoint in auto mode
            self.spin_setpoint.setFocus()

        self.statusBar().showMessage("Valve control", 2000)

    def _on_hex_clicked(self):
        """Handle heat exchanger click - show info"""
        self.statusBar().showMessage("Heat Exchanger - Steam/Air heat transfer", 2000)

    def _on_sensor_clicked(self, sensor_id):
        """Handle sensor click - focus on temperature"""
        self.right_tabs.setCurrentIndex(0)  # Trends tab
        self.statusBar().showMessage(f"Sensor: {sensor_id}", 2000)

    def closeEvent(self, event):
        """Handle window close"""
        self._on_pause()
        self.closed.emit()
        event.accept()
