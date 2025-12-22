"""
Channel Bus for I/O and Data Logging
=====================================

This module implements a thin communication layer between the model and UI,
supporting live updates via subscribers and historical data logging.
"""

import time
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
import pandas as pd
import numpy as np


@dataclass
class ChannelData:
    """Data container for all channel values"""
    # Inputs
    T_air_in: float = 10.0  # Inlet air temperature (ambient) - a.k.a. T_out
    Flow: float = 0.6
    dt_sec: float = 0.5

    # Outputs
    T_air_out: float = 20.0  # Outlet air temperature (measured by THK-0083)
    T_condensate: float = 100.0  # Steam condensate temperature
    u_dead: float = 0.0
    x1: float = 20.0
    x2: float = 0.0

    # Metadata
    sim_time: float = 0.0
    wall_time: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for logging"""
        return {
            'sim_time': self.sim_time,
            'wall_time': self.wall_time,
            'T_air_in': self.T_air_in,
            'Flow': self.Flow,
            'dt_sec': self.dt_sec,
            'T_air_out': self.T_air_out,
            'T_condensate': self.T_condensate,
            'u_dead': self.u_dead,
            'x1': self.x1,
            'x2': self.x2
        }


class Channels:
    """
    Channel bus for model I/O with subscriber notifications and data logging.

    This class acts as the communication hub between the simulation model
    and the user interface, providing:
    - Getter/setter for all input and output channels
    - Subscriber pattern for live UI updates
    - Timestamped data logging in pandas DataFrame
    - CSV export capability
    """

    def __init__(self):
        """Initialize channel bus"""
        self.data = ChannelData()
        self._subscribers: List[Callable[[ChannelData], None]] = []
        self._log_buffer: List[Dict[str, float]] = []
        self._log_enabled = True
        self._log_max_size = 100000  # Prevent memory overflow

    # ========== Input Channels ==========

    @property
    def T_air_in(self) -> float:
        """Inlet air temperature (°C) - ambient/outside"""
        return self.data.T_air_in

    @T_air_in.setter
    def T_air_in(self, value: float):
        self.data.T_air_in = value

    # Backward compatibility alias
    @property
    def T_out(self) -> float:
        """DEPRECATED: Use T_air_in instead"""
        return self.data.T_air_in

    @T_out.setter
    def T_out(self, value: float):
        self.data.T_air_in = value

    @property
    def Flow(self) -> float:
        """Steam valve flow control signal (0-1)"""
        return self.data.Flow

    @Flow.setter
    def Flow(self, value: float):
        self.data.Flow = value

    @property
    def dt_sec(self) -> float:
        """Integration time step (seconds)"""
        return self.data.dt_sec

    @dt_sec.setter
    def dt_sec(self, value: float):
        self.data.dt_sec = value

    # ========== Output Channels ==========

    @property
    def T_air_out(self) -> float:
        """Outlet air temperature (°C) - measured by THK-0083"""
        return self.data.T_air_out

    @T_air_out.setter
    def T_air_out(self, value: float):
        self.data.T_air_out = value

    # Backward compatibility alias
    @property
    def T_greenhouse(self) -> float:
        """DEPRECATED: Use T_air_out instead (same physical quantity)"""
        return self.data.T_air_out

    @T_greenhouse.setter
    def T_greenhouse(self, value: float):
        self.data.T_air_out = value

    @property
    def T_condensate(self) -> float:
        """Steam condensate temperature (°C)"""
        return self.data.T_condensate

    @T_condensate.setter
    def T_condensate(self, value: float):
        self.data.T_condensate = value

    # Backward compatibility alias
    @property
    def T_water(self) -> float:
        """DEPRECATED: Use T_condensate instead"""
        return self.data.T_condensate

    @T_water.setter
    def T_water(self, value: float):
        self.data.T_condensate = value

    @property
    def u_dead(self) -> float:
        """Delayed flow signal"""
        return self.data.u_dead

    @u_dead.setter
    def u_dead(self, value: float):
        self.data.u_dead = value

    @property
    def x1(self) -> float:
        """First state variable"""
        return self.data.x1

    @x1.setter
    def x1(self, value: float):
        self.data.x1 = value

    @property
    def x2(self) -> float:
        """Second state variable"""
        return self.data.x2

    @x2.setter
    def x2(self, value: float):
        self.data.x2 = value

    @property
    def sim_time(self) -> float:
        """Simulated time (seconds)"""
        return self.data.sim_time

    @sim_time.setter
    def sim_time(self, value: float):
        self.data.sim_time = value

    # ========== Subscriber Management ==========

    def subscribe(self, callback: Callable[[ChannelData], None]):
        """
        Subscribe to channel updates.

        Args:
            callback: Function to call on updates, receives ChannelData
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[ChannelData], None]):
        """
        Unsubscribe from channel updates.

        Args:
            callback: Previously subscribed callback
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def notify(self):
        """Notify all subscribers of current channel values"""
        for callback in self._subscribers:
            try:
                callback(self.data)
            except Exception as e:
                print(f"Error in subscriber callback: {e}")

    # ========== Data Logging ==========

    def update_from_model(self, outputs: Dict[str, float], sim_time: float):
        """
        Update channels from model outputs and log sample.

        Args:
            outputs: Dictionary from model.step()
            sim_time: Current simulation time
        """
        self.data.T_air_out = outputs['T_air_out']
        self.data.T_condensate = outputs['T_condensate']
        self.data.u_dead = outputs['u_dead']
        self.data.x1 = outputs['x1']
        self.data.x2 = outputs['x2']
        self.data.sim_time = sim_time
        self.data.wall_time = time.time()

        # Log sample
        if self._log_enabled and len(self._log_buffer) < self._log_max_size:
            self._log_buffer.append(self.data.to_dict())

        # Notify subscribers
        self.notify()

    def get_log_dataframe(self) -> pd.DataFrame:
        """
        Get logged data as pandas DataFrame.

        Returns:
            DataFrame with columns for all channels and timestamps
        """
        if not self._log_buffer:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=[
                'sim_time', 'wall_time', 'T_air_in', 'Flow', 'dt_sec',
                'T_air_out', 'T_condensate', 'u_dead', 'x1', 'x2'
            ])

        return pd.DataFrame(self._log_buffer)

    def save_csv(self, filename: str):
        """
        Export logged data to CSV file.

        Args:
            filename: Output CSV file path
        """
        df = self.get_log_dataframe()
        df.to_csv(filename, index=False, float_format='%.6f')
        print(f"Exported {len(df)} samples to {filename}")

    def clear_log(self):
        """Clear logged data"""
        self._log_buffer.clear()

    def enable_logging(self, enabled: bool = True):
        """Enable or disable data logging"""
        self._log_enabled = enabled

    def set_log_max_size(self, max_size: int):
        """Set maximum number of logged samples"""
        self._log_max_size = max_size

    # ========== Convenience Methods ==========

    def get_inputs(self) -> Dict[str, float]:
        """Get all input channel values"""
        return {
            'T_air_in': self.T_air_in,
            'Flow': self.Flow,
            'dt_sec': self.dt_sec
        }

    def get_outputs(self) -> Dict[str, float]:
        """Get all output channel values"""
        return {
            'T_air_out': self.T_air_out,
            'T_condensate': self.T_condensate,
            'u_dead': self.u_dead,
            'x1': self.x1,
            'x2': self.x2
        }

    def get_all(self) -> ChannelData:
        """Get complete channel data snapshot"""
        return self.data

    def reset(self):
        """Reset channels to default values and clear log"""
        self.data = ChannelData()
        self.clear_log()
