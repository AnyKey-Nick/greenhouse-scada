"""
Main Window - Greenhouse Heating HMI
=====================================

This module provides the main application window with P&ID visualization,
real-time plots, and control panels.
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QSplitter, QPushButton, QFileDialog, QComboBox,
                              QLabel, QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
import time

from .widgets import ControlPanel, PIDWidget, SimulationControls
from .plots import GreenhousePlot, InputsPlot


class MainWindow(QMainWindow):
    """
    Main application window for greenhouse heating HMI.
    """

    # Signals
    closed = pyqtSignal()

    def __init__(self, model, channels, presets_module):
        """
        Initialize main window.

        Args:
            model: GreenhouseHEXModel instance
            channels: Channels instance
            presets_module: presets module (for scenarios)
        """
        super().__init__()
        self.model = model
        self.channels = channels
        self.presets = presets_module

        # Simulation state
        self.running = False
        self.speed_multiplier = 1.0
        self.last_wall_time = None
        self.current_scenario = None

        # Timer for simulation updates
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self._on_timer_tick)
        self.timer_interval_ms = 50  # 50ms = 20 Hz UI update rate

        self._setup_ui()
        self._connect_signals()

        # Subscribe to channel updates
        self.channels.subscribe(self._on_channel_update)

        # Initial update
        self._update_display()

    def _setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("Greenhouse Heating System - TRACE-MODE Compatible")
        self.setGeometry(100, 100, 1400, 900)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        # Top: P&ID visualization
        self.pid_widget = PIDWidget()
        self.pid_widget.badgeClicked.connect(self._on_badge_clicked)
        main_layout.addWidget(self.pid_widget, stretch=0)

        # Middle: Plots and controls
        middle_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Plots
        plots_widget = QWidget()
        plots_layout = QVBoxLayout(plots_widget)

        self.greenhouse_plot = GreenhousePlot()
        plots_layout.addWidget(self.greenhouse_plot)

        self.inputs_plot = InputsPlot()
        plots_layout.addWidget(self.inputs_plot)

        middle_splitter.addWidget(plots_widget)

        # Right: Control panel
        self.control_panel = ControlPanel()
        middle_splitter.addWidget(self.control_panel)

        middle_splitter.setStretchFactor(0, 3)
        middle_splitter.setStretchFactor(1, 1)

        main_layout.addWidget(middle_splitter, stretch=1)

        # Bottom: Simulation controls and utilities
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)

        # Simulation controls
        self.sim_controls = SimulationControls()
        bottom_layout.addWidget(self.sim_controls)

        bottom_layout.addSpacing(20)

        # Scenario controls
        scenario_group = QGroupBox("Scenarios")
        scenario_layout = QHBoxLayout()

        self.scenario_combo = QComboBox()
        self.scenario_combo.addItems(['None', 'step_tout', 'ramp_flow', 'pulse_flow',
                                      'sinusoidal_tout', 'warmup'])
        scenario_layout.addWidget(QLabel("Scenario:"))
        scenario_layout.addWidget(self.scenario_combo)

        self.scenario_btn = QPushButton("Start")
        self.scenario_btn.clicked.connect(self._on_scenario_start)
        scenario_layout.addWidget(self.scenario_btn)

        scenario_group.setLayout(scenario_layout)
        bottom_layout.addWidget(scenario_group)

        bottom_layout.addSpacing(20)

        # File operations
        file_group = QGroupBox("Data")
        file_layout = QHBoxLayout()

        save_csv_btn = QPushButton("Save CSV")
        save_csv_btn.clicked.connect(self._on_save_csv)
        file_layout.addWidget(save_csv_btn)

        load_preset_btn = QPushButton("Load Preset")
        load_preset_btn.clicked.connect(self._on_load_preset)
        file_layout.addWidget(load_preset_btn)

        save_preset_btn = QPushButton("Save Preset")
        save_preset_btn.clicked.connect(self._on_save_preset)
        file_layout.addWidget(save_preset_btn)

        file_group.setLayout(file_layout)
        bottom_layout.addWidget(file_group)

        bottom_layout.addStretch()

        main_layout.addWidget(bottom_widget)

        # Status bar
        self.statusBar().showMessage("Ready")

    def _connect_signals(self):
        """Connect signals and slots"""
        # Simulation controls
        self.sim_controls.runClicked.connect(self._on_run)
        self.sim_controls.pauseClicked.connect(self._on_pause)
        self.sim_controls.stepClicked.connect(self._on_step)
        self.sim_controls.resetClicked.connect(self._on_reset)
        self.sim_controls.speedChanged.connect(self._on_speed_changed)

        # Parameter changes
        self.control_panel.paramChanged.connect(self._on_param_changed)
        self.control_panel.inputChanged.connect(self._on_input_changed)

    # ===== Simulation Control =====

    def _on_run(self):
        """Start simulation"""
        if not self.running:
            self.running = True
            self.last_wall_time = time.time()
            self.sim_timer.start(self.timer_interval_ms)
            self.sim_controls.set_running(True)
            self.statusBar().showMessage("Running")

    def _on_pause(self):
        """Pause simulation"""
        if self.running:
            self.running = False
            self.sim_timer.stop()
            self.sim_controls.set_running(False)
            self.statusBar().showMessage("Paused")

    def _on_step(self):
        """Execute single simulation step"""
        self._execute_step(self.channels.dt_sec)
        self.statusBar().showMessage(f"Stepped: t={self.channels.sim_time:.1f}s")

    def _on_reset(self):
        """Reset simulation"""
        # Stop if running
        was_running = self.running
        if self.running:
            self._on_pause()

        # Stop scenario
        if self.current_scenario is not None:
            self.current_scenario.stop()
            self.current_scenario = None

        # Reset model and channels
        from model import ModelState
        initial_state = ModelState(x1=20.0, x2=0.0, T_water=20.0)
        self.model.reset(initial_state)
        self.channels.reset()

        # Clear plots
        self.greenhouse_plot.clear()
        self.inputs_plot.clear()

        # Update display
        self._update_display()

        self.statusBar().showMessage("Reset")

        # Resume if was running
        if was_running:
            self._on_run()

    def _on_speed_changed(self, multiplier: float):
        """Handle speed multiplier change"""
        self.speed_multiplier = multiplier
        self.statusBar().showMessage(f"Speed: ×{multiplier}")

    def _on_timer_tick(self):
        """Handle simulation timer tick"""
        if not self.running:
            return

        # Calculate elapsed wall time
        current_wall_time = time.time()
        if self.last_wall_time is None:
            self.last_wall_time = current_wall_time
            return

        wall_dt = current_wall_time - self.last_wall_time
        self.last_wall_time = current_wall_time

        # Calculate simulated time to advance (with speed multiplier)
        sim_dt = wall_dt * self.speed_multiplier

        # Execute steps to cover sim_dt
        dt_sec = self.channels.dt_sec
        accumulated_time = 0.0

        while accumulated_time < sim_dt:
            self._execute_step(dt_sec)
            accumulated_time += dt_sec

            # Prevent runaway
            if accumulated_time > 10.0:  # Safety limit
                break

    def _execute_step(self, dt_sec: float):
        """Execute one model step"""
        # Get inputs from channels
        T_out = self.channels.T_out
        Flow = self.channels.Flow

        # Execute model step
        outputs = self.model.step(T_out, Flow, dt_sec)

        # Update channels
        new_sim_time = self.channels.sim_time + dt_sec
        self.channels.update_from_model(outputs, new_sim_time)

    def _on_channel_update(self, data):
        """Handle channel update notification"""
        self._update_display()

    def _update_display(self):
        """Update all display elements"""
        data = self.channels.get_all()

        # Update P&ID
        self.pid_widget.update_values(
            T_out=data.T_out,
            Flow=data.Flow,
            T_greenhouse=data.T_greenhouse,
            T_water=data.T_water,
            u_dead=data.u_dead
        )

        # Update plots
        self.greenhouse_plot.update(data.sim_time, data.T_greenhouse, data.T_water)
        self.inputs_plot.update(data.sim_time, data.T_out, data.Flow)

    # ===== Parameter/Input Changes =====

    def _on_param_changed(self, name: str, value: float):
        """Handle parameter change"""
        self.model.set_params(dt_sec=self.channels.dt_sec, **{name: value})
        self.statusBar().showMessage(f"Changed {name} = {value}")

    def _on_input_changed(self, name: str, value: float):
        """Handle input change"""
        setattr(self.channels, name, value)

        # If dt_sec changed, update model
        if name == 'dt_sec':
            self.model.set_params(dt_sec=value)

    # ===== Badge Interaction =====

    def _on_badge_clicked(self, label: str):
        """Handle P&ID badge click"""
        # Map badge labels to controls (optional feature)
        self.statusBar().showMessage(f"Clicked: {label}")

    # ===== Scenario Management =====

    def _on_scenario_start(self):
        """Start selected scenario"""
        scenario_name = self.scenario_combo.currentText()

        if scenario_name == 'None':
            # Stop current scenario
            if self.current_scenario is not None:
                self.current_scenario.stop()
                self.current_scenario = None
            self.statusBar().showMessage("Scenario stopped")
            return

        # Stop previous scenario
        if self.current_scenario is not None:
            self.current_scenario.stop()

        # Create and start new scenario
        try:
            import asyncio
            self.current_scenario = self.presets.get_scenario(scenario_name, self.channels)

            # Run scenario in background (simplified - not true async integration)
            # For production, would use QThread or proper async loop
            self.statusBar().showMessage(f"Scenario '{scenario_name}' started (manual mode)")
            QMessageBox.information(self, "Scenario",
                                    f"Scenario '{scenario_name}' configured.\n"
                                    f"Note: Full async scenario execution requires QThread integration.")

        except Exception as e:
            QMessageBox.warning(self, "Scenario Error", f"Failed to start scenario: {e}")

    # ===== File Operations =====

    def _on_save_csv(self):
        """Save logged data to CSV"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if filename:
            try:
                self.channels.save_csv(filename)
                self.statusBar().showMessage(f"Saved to {filename}")
                QMessageBox.information(self, "Export", f"Data exported to:\n{filename}")
            except Exception as e:
                QMessageBox.warning(self, "Export Error", f"Failed to save CSV: {e}")

    def _on_load_preset(self):
        """Load parameter preset"""
        # For now, use built-in presets
        from PyQt6.QtWidgets import QInputDialog

        presets = list(self.presets.PRESETS.keys())
        preset_name, ok = QInputDialog.getItem(
            self, "Load Preset", "Select preset:", presets, 0, False
        )

        if ok and preset_name:
            preset = self.presets.get_preset(preset_name)

            # Apply parameters
            for name, value in preset['params'].items():
                self.control_panel.set_param_value(name, value)
                self.model.set_params(dt_sec=self.channels.dt_sec, **{name: value})

            # Apply inputs
            for name, value in preset['inputs'].items():
                self.control_panel.set_input_value(name, value)
                setattr(self.channels, name, value)

            self.statusBar().showMessage(f"Loaded preset: {preset_name}")

    def _on_save_preset(self):
        """Save current parameters as preset (to TOML)"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Preset", "", "TOML Files (*.toml);;All Files (*)"
        )
        if filename:
            try:
                import toml

                preset_data = {
                    'params': self.control_panel.get_param_values(),
                    'inputs': self.control_panel.get_input_values(),
                }

                with open(filename, 'w') as f:
                    toml.dump(preset_data, f)

                self.statusBar().showMessage(f"Saved preset to {filename}")
            except Exception as e:
                QMessageBox.warning(self, "Save Error", f"Failed to save preset: {e}")

    def closeEvent(self, event):
        """Handle window close"""
        self._on_pause()
        self.closed.emit()
        event.accept()
