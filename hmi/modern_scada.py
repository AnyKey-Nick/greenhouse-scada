"""
Modern SCADA Interface - Material Design Style
================================================

Modern, clean interface with:
- Material Design colors and shadows
- Drag-and-drop visual editor
- Save/load layouts
- Formula tab
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QToolBar, QPushButton, QLabel, QComboBox, QSpinBox,
                              QStatusBar, QFrame, QTabWidget, QGroupBox, QGridLayout,
                              QFileDialog, QMessageBox, QSplitter, QSlider, QDockWidget)
from PyQt6.QtCore import Qt, QTimer, QTime, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QFont, QPalette, QColor, QIcon
import time
import json
import os

from .scada_widgets import (StatusLED, AnalogGauge, DigitalDisplay)
from .scada_widgets_improved import (Pipe, Valve, HeatExchanger, Pump, ProcessTag)
from .plots import GreenhousePlot, InputsPlot
from .analysis_plots import AnalysisWidget
from .formula_tab import FormulaTab
from .calculations_tab import CalculationsTab


class ModernSCADAWindow(QMainWindow):
    """Modern Material Design SCADA interface"""

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

        # Layout storage
        self.layout_file = "scada_layout.json"

        # Language state (default: English)
        self.language = 'en'  # 'en' or 'uk'

        # Setup modern theme
        self._setup_modern_theme()

        # Setup UI
        self._setup_ui()
        self._create_toolbar()
        self._create_statusbar()

        # Simulation timer
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self._on_timer_tick)
        self.timer_interval_ms = 50

        # Subscribe to channel updates
        self.channels.subscribe(self._on_channel_update)

        # Initial update
        self._update_display()
        self._update_analysis_plots()

        # Start clock
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)

    def _setup_modern_theme(self):
        """Setup modern Material Design theme"""
        palette = QPalette()

        # Material Design colors - LIGHT THEME
        palette.setColor(QPalette.ColorRole.Window, QColor(250, 250, 250))  # Almost white
        palette.setColor(QPalette.ColorRole.WindowText, QColor(33, 33, 33))  # Almost black
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))  # White
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(33, 33, 33))
        palette.setColor(QPalette.ColorRole.Text, QColor(33, 33, 33))
        palette.setColor(QPalette.ColorRole.Button, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(33, 33, 33))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(244, 67, 54))  # Red
        palette.setColor(QPalette.ColorRole.Highlight, QColor(25, 118, 210))  # Blue
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

        self.setPalette(palette)

        # Modern flat stylesheet with Material Design
        self.setStyleSheet("""
            QMainWindow {
                background-color: #fafafa;
            }
            QToolBar {
                background-color: white;
                border: none;
                border-bottom: 1px solid #e0e0e0;
                spacing: 10px;
                padding: 8px;
            }
            QToolButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 8px;
                color: #424242;
            }
            QToolButton:hover {
                background-color: #f5f5f5;
            }
            QToolButton:pressed {
                background-color: #eeeeee;
            }
            QPushButton {
                background-color: #1976d2;
                border: none;
                border-radius: 4px;
                padding: 10px 24px;
                color: white;
                font-size: 14px;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #9e9e9e;
            }
            QGroupBox {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 20px;
                padding: 15px;
                font-weight: 500;
                color: #424242;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background-color: white;
                color: #1976d2;
            }
            QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: white;
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                padding: 8px;
                color: #212121;
                min-height: 20px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border: 2px solid #1976d2;
            }
            QStatusBar {
                background-color: white;
                border-top: 1px solid #e0e0e0;
                color: #616161;
            }
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                background-color: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: transparent;
                border: none;
                border-bottom: 2px solid transparent;
                padding: 12px 24px;
                color: #757575;
                font-size: 14px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                color: #1976d2;
                border-bottom: 2px solid #1976d2;
            }
            QTabBar::tab:hover {
                color: #424242;
            }
            QSlider::groove:horizontal {
                border: 1px solid #bdbdbd;
                height: 4px;
                background: #eeeeee;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #1976d2;
                border: none;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #1565c0;
            }
        """)

    def _setup_ui(self):
        """Setup main user interface"""
        self.setWindowTitle("Greenhouse Control System - Modern UI")
        self.setGeometry(50, 50, 1600, 900)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main tabs
        self.main_tabs = QTabWidget()
        self.main_tabs.setDocumentMode(True)

        # Tab 1: Process View
        process_tab = self._create_process_tab()
        self.main_tabs.addTab(process_tab, "🏭 Process")

        # Tab 2: Formula (НОВА ВКЛАДКА!)
        self.formula_tab = FormulaTab(language=self.language)
        self.main_tabs.addTab(self.formula_tab, "📐 Formula")

        # Tab 3: Analysis
        self.analysis_widget = AnalysisWidget()
        self.main_tabs.addTab(self.analysis_widget, "📊 Analysis")

        # Tab 4: Calculations (НОВА ВКЛАДКА!)
        self.calculations_tab = CalculationsTab(language=self.language)
        self.main_tabs.addTab(self.calculations_tab, "🧮 Calculations")

        # Tab 5: Controls
        controls_tab = self._create_controls_tab()
        self.main_tabs.addTab(controls_tab, "⚙️ Controls")

        # Tab 5: Visual Designer (НОВИЙ!)
        designer_tab = self._create_designer_tab()
        self.main_tabs.addTab(designer_tab, "🎨 Designer")

        main_layout.addWidget(self.main_tabs)

    def _create_process_tab(self):
        """Create modern process view tab"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Left: Process visualization
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.Shape.StyledPanel)
        left_layout = QVBoxLayout(left_panel)

        # Header - Modern card style
        header = QLabel("Process Overview")
        header.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        header.setStyleSheet("""
            QLabel {
                color: #1976d2;
                padding: 20px;
                background-color: white;
                border-radius: 8px;
            }
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(header)

        # Process graphics - DARK background so elements are VISIBLE
        process_widget = QWidget()
        process_widget.setMinimumHeight(500)
        process_widget.setStyleSheet("""
            background-color: #2c3e50;
            border-radius: 8px;
            border: 2px solid #34495e;
        """)

        # Create widgets
        self.steam_source = ProcessTag("STEAM", 100.0, "°C")
        self.valve_widget = Valve()
        self.hex_widget = HeatExchanger()
        self.pump_widget = Pump()
        self.greenhouse_tag = ProcessTag("T_GH", 20.0, "°C")

        self.pipe1 = Pipe(150, 40, horizontal=True)
        self.pipe2 = Pipe(40, 100, horizontal=False)
        self.pipe3 = Pipe(200, 40, horizontal=True)

        # Position widgets
        self.steam_source.setParent(process_widget)
        self.steam_source.move(20, 200)

        self.pipe1.setParent(process_widget)
        self.pipe1.move(190, 215)

        self.valve_widget.setParent(process_widget)
        self.valve_widget.move(350, 195)

        self.pipe2.setParent(process_widget)
        self.pipe2.move(385, 305)

        self.hex_widget.setParent(process_widget)
        self.hex_widget.move(340, 405)

        self.pipe3.setParent(process_widget)
        self.pipe3.move(470, 455)

        self.pump_widget.setParent(process_widget)
        self.pump_widget.move(680, 445)

        self.greenhouse_tag.setParent(process_widget)
        self.greenhouse_tag.move(780, 455)

        left_layout.addWidget(process_widget)
        layout.addWidget(left_panel, 2)

        # Right: Trends
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        right_layout = QVBoxLayout(right_panel)

        trends_label = QLabel("Real-time Trends")
        trends_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        trends_label.setStyleSheet("color: #1976d2; padding: 10px;")
        right_layout.addWidget(trends_label)

        # Plots
        self.greenhouse_plot = GreenhousePlot()
        self.inputs_plot = InputsPlot()

        right_layout.addWidget(self.greenhouse_plot)
        right_layout.addWidget(self.inputs_plot)

        layout.addWidget(right_panel, 1)

        return widget

    def _create_controls_tab(self):
        """Create modern controls tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Parameters card
        params_card = QGroupBox("Model Parameters")
        params_card.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #1976d2;
                border: 2px solid #1976d2;
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background-color: white;
            }
            QLabel {
                color: #424242;
                font-size: 13px;
                font-weight: normal;
            }
            QSpinBox {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
                color: #212121;
                font-size: 13px;
            }
            QSpinBox:focus {
                border: 2px solid #1976d2;
            }
        """)
        params_layout = QGridLayout()
        params_layout.setSpacing(15)

        param_names = ['K', 'T1', 'T2', 'L', 'Kz', 'TambRef', 'KUW', 'TW']
        self.param_spinboxes = {}

        for i, name in enumerate(param_names):
            label = QLabel(f"{name}:")
            label.setFont(QFont("Segoe UI", 11))

            spinbox = QSpinBox()
            spinbox.setMinimumWidth(150)

            # Configure ranges
            if name in ['K', 'Kz', 'KUW']:
                spinbox.setRange(0, 500)
                spinbox.setSingleStep(1)
                spinbox.setSuffix(" %")
            elif name == 'TambRef':
                spinbox.setRange(-50, 50)
                spinbox.setSingleStep(1)
            else:
                spinbox.setRange(1, 500)
                spinbox.setSingleStep(1)

            # Set defaults
            default_values = {'K': 4167, 'T1': 120, 'T2': 60, 'L': 10,
                            'Kz': 100, 'TambRef': 0, 'KUW': 50, 'TW': 90}
            spinbox.setValue(default_values.get(name, 10))

            # Connect
            if name in ['K', 'Kz', 'KUW']:
                spinbox.valueChanged.connect(lambda v, n=name: self._on_param_changed(n, v/100.0))
            else:
                spinbox.valueChanged.connect(lambda v, n=name: self._on_param_changed(n, float(v)))

            params_layout.addWidget(label, i, 0)
            params_layout.addWidget(spinbox, i, 1)

            self.param_spinboxes[name] = spinbox

        params_card.setLayout(params_layout)
        layout.addWidget(params_card)

        # Inputs card
        inputs_card = QGroupBox("Input Signals")
        inputs_card.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #388e3c;
                border: 2px solid #388e3c;
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background-color: white;
            }
            QLabel {
                color: #424242;
                font-size: 13px;
                font-weight: normal;
            }
            QSpinBox {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
                color: #212121;
                font-size: 13px;
            }
            QSpinBox:focus {
                border: 2px solid #388e3c;
            }
        """)
        inputs_layout = QGridLayout()
        inputs_layout.setSpacing(15)

        # T_out
        tout_label = QLabel("Outside Temp (T_out):")
        tout_label.setFont(QFont("Segoe UI", 11))
        self.spin_tout = QSpinBox()
        self.spin_tout.setRange(-50, 50)
        self.spin_tout.setValue(10)
        self.spin_tout.setSuffix(" °C")
        self.spin_tout.setMinimumWidth(150)
        self.spin_tout.valueChanged.connect(lambda v: self._on_input_changed('T_out', float(v)))
        inputs_layout.addWidget(tout_label, 0, 0)
        inputs_layout.addWidget(self.spin_tout, 0, 1)

        # Flow
        flow_label = QLabel("Steam Flow:")
        flow_label.setFont(QFont("Segoe UI", 11))
        self.spin_flow = QSpinBox()
        self.spin_flow.setRange(0, 100)
        self.spin_flow.setValue(60)
        self.spin_flow.setSuffix(" %")
        self.spin_flow.setMinimumWidth(150)
        self.spin_flow.valueChanged.connect(lambda v: self._on_input_changed('Flow', v / 100.0))
        inputs_layout.addWidget(flow_label, 1, 0)
        inputs_layout.addWidget(self.spin_flow, 1, 1)

        # dt
        dt_label = QLabel("Time Step (dt):")
        dt_label.setFont(QFont("Segoe UI", 11))
        self.spin_dt = QSpinBox()
        self.spin_dt.setRange(10, 200)
        self.spin_dt.setValue(50)
        self.spin_dt.setSuffix(" x0.01s")
        self.spin_dt.setMinimumWidth(150)
        self.spin_dt.valueChanged.connect(lambda v: self._on_dt_changed(v / 100.0))
        inputs_layout.addWidget(dt_label, 2, 0)
        inputs_layout.addWidget(self.spin_dt, 2, 1)

        inputs_card.setLayout(inputs_layout)
        layout.addWidget(inputs_card)

        # Presets card
        presets_card = QGroupBox("Presets")
        presets_card.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #f57c00;
                border: 2px solid #f57c00;
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background-color: white;
            }
            QComboBox {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
                color: #212121;
                font-size: 13px;
            }
            QComboBox:focus {
                border: 2px solid #f57c00;
            }
            QPushButton {
                padding: 10px 20px;
                background-color: #f57c00;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ef6c00;
            }
            QPushButton:pressed {
                background-color: #e65100;
            }
        """)
        presets_layout = QHBoxLayout()

        self.combo_preset = QComboBox()
        self.combo_preset.addItems(['default', 'fast', 'slow', 'winter', 'summer'])
        self.combo_preset.setMinimumWidth(200)

        load_btn = QPushButton("Load Preset")
        load_btn.clicked.connect(self._on_load_preset)

        presets_layout.addWidget(self.combo_preset)
        presets_layout.addWidget(load_btn)
        presets_layout.addStretch()

        presets_card.setLayout(presets_layout)
        layout.addWidget(presets_card)

        layout.addStretch()

        return widget

    def _create_designer_tab(self):
        """Create visual designer tab - НОВА ВКЛАДКА!"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Visual Designer - Конструктор візуалізації")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #1976d2; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Buttons
        btn_layout = QHBoxLayout()

        save_layout_btn = QPushButton("💾 Save Layout")
        save_layout_btn.clicked.connect(self._save_layout)
        btn_layout.addWidget(save_layout_btn)

        load_layout_btn = QPushButton("📂 Load Layout")
        load_layout_btn.clicked.connect(self._load_layout)
        btn_layout.addWidget(load_layout_btn)

        reset_layout_btn = QPushButton("🔄 Reset Layout")
        reset_layout_btn.clicked.connect(self._reset_layout)
        btn_layout.addWidget(reset_layout_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Instructions
        instructions = QLabel("""
<div style='padding: 20px; background-color: #e3f2fd; border-radius: 8px; margin: 10px 0;'>
<h3 style='color: #1976d2;'>Інструкції / Instructions:</h3>
<ul>
<li><b>Save Layout</b> - зберегти поточне розташування елементів</li>
<li><b>Load Layout</b> - завантажити збережене розташування</li>
<li><b>Reset Layout</b> - повернути до типового розташування</li>
</ul>
<p><i>Файл зберігається як: scada_layout.json</i></p>
</div>
        """)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        layout.addStretch()

        return widget

    def _create_toolbar(self):
        """Create modern toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Start/Pause button
        self.btn_start = QPushButton("▶ Start")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_start.clicked.connect(self._on_start_pause)
        toolbar.addWidget(self.btn_start)

        toolbar.addSeparator()

        # Speed control
        toolbar.addWidget(QLabel("  Speed:  "))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 100)
        self.speed_slider.setValue(10)
        self.speed_slider.setMaximumWidth(200)
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        toolbar.addWidget(self.speed_slider)

        self.speed_label = QLabel("1.0x")
        self.speed_label.setMinimumWidth(50)
        toolbar.addWidget(self.speed_label)

        toolbar.addSeparator()

        # Language toggle button
        self.lang_btn = QPushButton("🌐 Українська")
        self.lang_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        self.lang_btn.clicked.connect(self._toggle_language)
        toolbar.addWidget(self.lang_btn)

        toolbar.addSeparator()

        # Save CSV
        save_btn = QPushButton("💾 Save CSV")
        save_btn.clicked.connect(self._on_save_csv)
        toolbar.addWidget(save_btn)

    def _create_statusbar(self):
        """Create modern status bar"""
        self.statusBar().setStyleSheet("padding: 5px;")

        # Time label
        self.time_label = QLabel("Sim Time: 0.0s")
        self.time_label.setFont(QFont("Segoe UI", 10))
        self.statusBar().addPermanentWidget(self.time_label)

        # Clock
        self.clock_label = QLabel()
        self.clock_label.setFont(QFont("Segoe UI", 10))
        self.statusBar().addPermanentWidget(self.clock_label)

        self.statusBar().showMessage("Ready")

    def _save_layout(self):
        """Save current layout to JSON"""
        layout_data = {
            'steam_source': {'x': self.steam_source.x(), 'y': self.steam_source.y()},
            'valve': {'x': self.valve_widget.x(), 'y': self.valve_widget.y()},
            'hex': {'x': self.hex_widget.x(), 'y': self.hex_widget.y()},
            'pump': {'x': self.pump_widget.x(), 'y': self.pump_widget.y()},
            'greenhouse_tag': {'x': self.greenhouse_tag.x(), 'y': self.greenhouse_tag.y()},
            'pipe1': {'x': self.pipe1.x(), 'y': self.pipe1.y()},
            'pipe2': {'x': self.pipe2.x(), 'y': self.pipe2.y()},
            'pipe3': {'x': self.pipe3.x(), 'y': self.pipe3.y()}
        }

        try:
            with open(self.layout_file, 'w') as f:
                json.dump(layout_data, f, indent=2)
            self.statusBar().showMessage(f"Layout saved to {self.layout_file}", 3000)
            QMessageBox.information(self, "Success", f"Layout saved to {self.layout_file}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save layout: {e}")

    def _load_layout(self):
        """Load layout from JSON"""
        if not os.path.exists(self.layout_file):
            QMessageBox.warning(self, "Warning", f"Layout file {self.layout_file} not found")
            return

        try:
            with open(self.layout_file, 'r') as f:
                layout_data = json.load(f)

            self.steam_source.move(layout_data['steam_source']['x'], layout_data['steam_source']['y'])
            self.valve_widget.move(layout_data['valve']['x'], layout_data['valve']['y'])
            self.hex_widget.move(layout_data['hex']['x'], layout_data['hex']['y'])
            self.pump_widget.move(layout_data['pump']['x'], layout_data['pump']['y'])
            self.greenhouse_tag.move(layout_data['greenhouse_tag']['x'], layout_data['greenhouse_tag']['y'])
            self.pipe1.move(layout_data['pipe1']['x'], layout_data['pipe1']['y'])
            self.pipe2.move(layout_data['pipe2']['x'], layout_data['pipe2']['y'])
            self.pipe3.move(layout_data['pipe3']['x'], layout_data['pipe3']['y'])

            self.statusBar().showMessage(f"Layout loaded from {self.layout_file}", 3000)
            QMessageBox.information(self, "Success", "Layout loaded successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load layout: {e}")

    def _reset_layout(self):
        """Reset to default layout"""
        self.steam_source.move(20, 200)
        self.pipe1.move(190, 215)
        self.valve_widget.move(350, 195)
        self.pipe2.move(385, 305)
        self.hex_widget.move(340, 405)
        self.pipe3.move(470, 455)
        self.pump_widget.move(680, 445)
        self.greenhouse_tag.move(780, 455)

        self.statusBar().showMessage("Layout reset to default", 3000)

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
            self.setWindowTitle("Система керування теплицею - Сучасний інтерфейс")
            self.main_tabs.setTabText(0, "🏭 Процес")
            self.main_tabs.setTabText(1, "📐 Формула")
            self.main_tabs.setTabText(2, "📊 Аналіз")
            self.main_tabs.setTabText(3, "🧮 Розрахунки")
            self.main_tabs.setTabText(4, "⚙️ Керування")
            self.main_tabs.setTabText(5, "🎨 Конструктор")
            self.btn_start.setText("▶ Пуск" if not self.running else "⏸ Пауза")
        else:
            self.setWindowTitle("Greenhouse Control System - Modern UI")
            self.main_tabs.setTabText(0, "🏭 Process")
            self.main_tabs.setTabText(1, "📐 Formula")
            self.main_tabs.setTabText(2, "📊 Analysis")
            self.main_tabs.setTabText(3, "🧮 Calculations")
            self.main_tabs.setTabText(4, "⚙️ Controls")
            self.main_tabs.setTabText(5, "🎨 Designer")
            self.btn_start.setText("▶ Start" if not self.running else "⏸ Pause")

    def _on_start_pause(self):
        """Toggle simulation"""
        if self.running:
            self._on_pause()
        else:
            self._on_start()

    def _on_start(self):
        """Start simulation"""
        self.running = True
        self.last_wall_time = time.time()
        self.sim_timer.start(self.timer_interval_ms)
        self.btn_start.setText("⏸ Pause")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        self.statusBar().showMessage("Simulation running")

    def _on_pause(self):
        """Pause simulation"""
        self.running = False
        self.sim_timer.stop()
        self.btn_start.setText("▶ Start")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.statusBar().showMessage("Simulation paused")

    def _on_speed_changed(self, value):
        """Handle speed slider change"""
        self.speed_multiplier = value / 10.0
        self.speed_label.setText(f"{self.speed_multiplier:.1f}x")

    def _on_timer_tick(self):
        """Simulation timer tick"""
        if not self.running:
            return

        current_wall_time = time.time()
        if self.last_wall_time is not None:
            wall_dt = current_wall_time - self.last_wall_time
            sim_dt = wall_dt * self.speed_multiplier

            # Run simulation steps
            steps = int(sim_dt / self.channels.dt_sec)
            for _ in range(max(1, steps)):
                self.channels.step_simulation(self.model)

        self.last_wall_time = current_wall_time
        self._update_display()

    def _update_display(self):
        """Update all displays"""
        # Get complete channel data snapshot (same as SCADA version)
        data = self.channels.get_all()

        # Update process widgets
        self.steam_source.setValue(100.0)
        self.valve_widget.setPosition(data.Flow)
        self.hex_widget.setTemperatures(data.T_water, data.T_greenhouse)
        self.hex_widget.setActive(data.Flow > 0.1)
        self.pump_widget.setRunning(data.Flow > 0.1)
        self.greenhouse_tag.setValue(data.T_greenhouse)

        self.pipe1.setActive(data.Flow > 0.1)
        self.pipe2.setActive(data.Flow > 0.1)
        self.pipe3.setActive(data.Flow > 0.1)

        # Update plots with sim_time (same as SCADA version!)
        if hasattr(self, 'greenhouse_plot') and hasattr(self, 'inputs_plot'):
            self.greenhouse_plot.update(data.sim_time, data.T_greenhouse, data.T_water)
            self.inputs_plot.update(data.sim_time, data.T_out, data.Flow)

        # Update status bar with sim_time
        if hasattr(self, 'time_label'):
            self.time_label.setText(f"Sim Time: {data.sim_time:.1f}s")

    def _update_clock(self):
        """Update clock display"""
        current_time = QTime.currentTime()
        self.clock_label.setText(current_time.toString("hh:mm:ss"))

    def _on_channel_update(self, data):
        """Handle channel update"""
        pass  # Real-time updates handled in _update_display

    def _on_param_changed(self, name: str, value: float):
        """Handle parameter change"""
        self.model.set_params(dt_sec=self.channels.dt_sec, **{name: value})
        self._update_analysis_plots()

    def _on_input_changed(self, name: str, value: float):
        """Handle input change"""
        setattr(self.channels, name, value)

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
                if name in ['K', 'Kz', 'KUW']:
                    scaled_value = int(value * 100)
                else:
                    scaled_value = int(value)
                self.param_spinboxes[name].setValue(scaled_value)

        # Apply inputs
        self.spin_tout.setValue(int(preset['inputs']['T_out']))
        self.spin_flow.setValue(int(preset['inputs']['Flow'] * 100))
        self.spin_dt.setValue(int(preset['inputs']['dt_sec'] * 100))

        self.statusBar().showMessage(f"Loaded preset: {preset_name}", 3000)

    def _on_save_csv(self):
        """Save CSV"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Data", "", "CSV Files (*.csv)")

        if filename:
            try:
                self.channels.save_to_csv(filename)
                self.statusBar().showMessage(f"Data saved to {filename}", 3000)
                QMessageBox.information(self, "Success", f"Data saved to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {e}")

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
            self.spin_dt.setValue(int(value * 100))

    def closeEvent(self, event):
        """Handle window close"""
        self._on_pause()
        self.closed.emit()
        event.accept()
