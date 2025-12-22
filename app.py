"""
Greenhouse Heating System Application
======================================

Main entry point for the greenhouse heating system emulator.

Usage:
    GUI mode:
        python app.py

    Headless batch mode:
        python app.py --headless --minutes 60 --csv output.csv --preset winter

    With custom configuration:
        python app.py --config myconfig.toml
"""

import sys
import argparse
import time
from pathlib import Path

# Model and simulation
from model import GreenhouseHEXModel, ModelParams, ModelState
from io_channels import Channels
import presets

# GUI mode
try:
    from PyQt6.QtWidgets import QApplication
    from hmi import MainWindow
    from hmi.scada_main_window import SCADAMainWindow
    from hmi.modern_scada import ModernSCADAWindow
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("Warning: PyQt6 not available. GUI mode disabled.")


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Greenhouse Heating System - TRACE-MODE Compatible Emulator"
    )

    # Mode selection
    parser.add_argument('--headless', action='store_true',
                        help="Run in headless batch mode (no GUI)")
    parser.add_argument('--scada', action='store_true',
                        help="Use professional SCADA-style interface")
    parser.add_argument('--modern', action='store_true',
                        help="Use modern Material Design interface (RECOMMENDED)")

    # Headless mode parameters
    parser.add_argument('--minutes', type=float, default=10.0,
                        help="Simulation duration in minutes (headless mode)")
    parser.add_argument('--csv', type=str, default=None,
                        help="Output CSV file path (headless mode)")
    parser.add_argument('--preset', type=str, default='default',
                        help="Preset name to use (default, fast, slow, winter, summer)")
    parser.add_argument('--scenario', type=str, default=None,
                        help="Scenario to run (step_tout, ramp_flow, pulse_flow, etc.)")

    # Configuration
    parser.add_argument('--config', type=str, default=None,
                        help="TOML configuration file path")

    # Model parameters (override preset)
    parser.add_argument('--K', type=float, default=None)
    parser.add_argument('--T1', type=float, default=None)
    parser.add_argument('--T2', type=float, default=None)
    parser.add_argument('--L', type=float, default=None)
    parser.add_argument('--dt', type=float, default=None, help="Time step (seconds)")

    # Inputs
    parser.add_argument('--T-out', type=float, default=None, dest='T_out',
                        help="Outside temperature (°C)")
    parser.add_argument('--Flow', type=float, default=None,
                        help="Steam flow control signal (0-1)")

    return parser.parse_args()


def load_config(config_path: str):
    """Load configuration from TOML file"""
    try:
        import toml
        with open(config_path, 'r') as f:
            return toml.load(f)
    except ImportError:
        print("Warning: toml package not installed. Cannot load config file.")
        return {}
    except Exception as e:
        print(f"Warning: Failed to load config file: {e}")
        return {}


def run_gui(args):
    """Run GUI mode"""
    if not GUI_AVAILABLE:
        print("Error: PyQt6 not available. Cannot run GUI mode.")
        sys.exit(1)

    # Load preset
    preset = presets.get_preset(args.preset)

    # Apply CLI overrides
    if args.K is not None:
        preset['params']['K'] = args.K
    if args.T1 is not None:
        preset['params']['T1'] = args.T1
    if args.T2 is not None:
        preset['params']['T2'] = args.T2
    if args.L is not None:
        preset['params']['L'] = args.L
    if args.T_out is not None:
        preset['inputs']['T_out'] = args.T_out
    if args.Flow is not None:
        preset['inputs']['Flow'] = args.Flow
    if args.dt is not None:
        preset['inputs']['dt_sec'] = args.dt

    # Create model
    model_params = ModelParams(**preset['params'])
    initial_state = ModelState(**preset['initial_state'])
    model = GreenhouseHEXModel(params=model_params, initial_state=initial_state)

    # Create channels
    channels = Channels()
    channels.T_out = preset['inputs']['T_out']
    channels.Flow = preset['inputs']['Flow']
    channels.dt_sec = preset['inputs']['dt_sec']

    # Create Qt application
    app = QApplication(sys.argv)

    # Create main window (choose interface style)
    if args.modern:
        # Modern Material Design interface (RECOMMENDED)
        window = ModernSCADAWindow(model, channels, presets)
    elif args.scada:
        # Professional SCADA interface
        window = SCADAMainWindow(model, channels, presets)
    else:
        # Simple interface
        window = MainWindow(model, channels, presets)
    window.show()

    # Load config if specified
    if args.config:
        config = load_config(args.config)
        # Apply config (works for both window types)
        if 'params' in config:
            for name, value in config['params'].items():
                if hasattr(window, 'control_panel'):
                    # Simple interface
                    window.control_panel.set_param_value(name, value)
                else:
                    # SCADA interface
                    window.set_param_value(name, value)
        if 'inputs' in config:
            for name, value in config['inputs'].items():
                if hasattr(window, 'control_panel'):
                    window.control_panel.set_input_value(name, value)
                else:
                    window.set_input_value(name, value)

    # Run application
    sys.exit(app.exec())


def run_headless(args):
    """Run headless batch mode"""
    print("=" * 60)
    print("Greenhouse Heating System - Headless Batch Mode")
    print("=" * 60)

    # Load preset
    preset = presets.get_preset(args.preset)
    print(f"Loaded preset: {args.preset}")

    # Apply CLI overrides
    if args.K is not None:
        preset['params']['K'] = args.K
    if args.T1 is not None:
        preset['params']['T1'] = args.T1
    if args.T2 is not None:
        preset['params']['T2'] = args.T2
    if args.L is not None:
        preset['params']['L'] = args.L
    if args.T_out is not None:
        preset['inputs']['T_out'] = args.T_out
    if args.Flow is not None:
        preset['inputs']['Flow'] = args.Flow
    if args.dt is not None:
        preset['inputs']['dt_sec'] = args.dt

    # Create model
    model_params = ModelParams(**preset['params'])
    initial_state = ModelState(**preset['initial_state'])
    model = GreenhouseHEXModel(params=model_params, initial_state=initial_state)

    print(f"\nModel Parameters:")
    for key, value in preset['params'].items():
        print(f"  {key:10s} = {value}")

    # Create channels
    channels = Channels()
    channels.T_out = preset['inputs']['T_out']
    channels.Flow = preset['inputs']['Flow']
    channels.dt_sec = preset['inputs']['dt_sec']

    print(f"\nInputs:")
    print(f"  T_out      = {channels.T_out} °C")
    print(f"  Flow       = {channels.Flow}")
    print(f"  dt_sec     = {channels.dt_sec} s")

    # Simulation parameters
    duration_sec = args.minutes * 60.0
    dt_sec = channels.dt_sec
    num_steps = int(duration_sec / dt_sec)

    print(f"\nSimulation:")
    print(f"  Duration   = {args.minutes} min ({duration_sec} s)")
    print(f"  Time step  = {dt_sec} s")
    print(f"  Steps      = {num_steps}")

    # Setup scenario if specified
    if args.scenario:
        print(f"\nScenario: {args.scenario}")
        # Note: Scenario execution in headless mode would require manual implementation
        # For simplicity, we'll skip async scenario execution in headless mode
        print("  (Scenario execution not fully implemented in headless mode)")

    # Run simulation
    print("\nRunning simulation...")
    start_time = time.time()

    for step in range(num_steps):
        # Get inputs
        T_out = channels.T_out
        Flow = channels.Flow

        # Execute model step
        outputs = model.step(T_out, Flow, dt_sec)

        # Update channels
        sim_time = step * dt_sec
        channels.update_from_model(outputs, sim_time)

        # Progress update every 10%
        if step % (num_steps // 10) == 0:
            progress = 100.0 * step / num_steps
            print(f"  {progress:5.1f}% | t={sim_time:8.1f}s | "
                  f"T_gh={outputs['T_greenhouse']:6.2f}°C | "
                  f"T_w={outputs['T_water']:6.2f}°C")

    elapsed_time = time.time() - start_time
    print(f"\nSimulation completed in {elapsed_time:.2f} s")
    print(f"  Real-time factor: {duration_sec / elapsed_time:.1f}×")

    # Final state
    print(f"\nFinal State:")
    print(f"  T_greenhouse = {channels.T_greenhouse:.2f} °C")
    print(f"  T_water      = {channels.T_water:.2f} °C")
    print(f"  x1           = {channels.x1:.4f}")
    print(f"  x2           = {channels.x2:.4f}")

    # Save CSV if requested
    if args.csv:
        csv_path = Path(args.csv)
        channels.save_csv(str(csv_path))
        print(f"\nData exported to: {csv_path.absolute()}")

    print("\n" + "=" * 60)


def main():
    """Main entry point"""
    args = parse_args()

    if args.headless:
        run_headless(args)
    else:
        run_gui(args)


if __name__ == '__main__':
    main()
