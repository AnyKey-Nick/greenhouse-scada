"""
Presets and Disturbance Scenarios
==================================

This module provides predefined parameter presets and disturbance scenarios
for testing the greenhouse heating system.
"""

import asyncio
from typing import Dict, Any, Callable
import numpy as np


# ========== Parameter Presets ==========

DEFAULT_PRESET = {
    'name': 'Default',
    'description': 'Реальна теплиця 15x7x2.5м, T=22°C (262.5 м³)',
    'params': {
        'K': 10.0,  # Підібрано для T_greenhouse = 22°C
        'T1': 120.0,  # Інерція теплиці
        'T2': 60.0,   # Інерція води
        'L': 10.0,    # Запізнення
        'Kz': 1.0,    # Зв'язок з зовнішнім середовищем
        'TambRef': 0.0,
        'KUW': 0.5,   # Коефіцієнт теплообміну води
        'TW': 90.0    # Постійна часу води
    },
    'inputs': {
        'T_out': 16.0,    # Початкова температура повітря 16°C
        'Flow': 0.86,     # Масовий потік F_po = 0.86 кг/с
        'dt_sec': 0.5
    },
    'initial_state': {
        'x1': 16.0,   # Початкова T в теплиці 16°C
        'x2': 0.0,
        'T_condensate': 100.0  # Температура конденсату ~100°C
    }
}

FAST_RESPONSE_PRESET = {
    'name': 'Fast Response',
    'description': 'Faster thermal dynamics for testing',
    'params': {
        'K': 41.67,
        'T1': 60.0,   # Halved time constants for faster response
        'T2': 30.0,
        'L': 5.0,     # Reduced delay
        'Kz': 1.0,
        'TambRef': 0.0,
        'KUW': 0.7,
        'TW': 45.0    # Faster water response
    },
    'inputs': {
        'T_out': 10.0,
        'Flow': 0.6,
        'dt_sec': 0.5
    },
    'initial_state': {
        'x1': 20.0,
        'x2': 0.0,
        'T_condensate': 100.0
    }
}

SLOW_RESPONSE_PRESET = {
    'name': 'Slow Response',
    'description': 'Sluggish thermal dynamics (large thermal mass)',
    'params': {
        'K': 41.67,
        'T1': 240.0,   # Doubled time constants for slower response
        'T2': 120.0,
        'L': 20.0,     # Increased delay
        'Kz': 1.0,
        'TambRef': 0.0,
        'KUW': 0.3,
        'TW': 180.0    # Slower condensate response
    },
    'inputs': {
        'T_out': 10.0,
        'Flow': 0.6,
        'dt_sec': 0.5
    },
    'initial_state': {
        'x1': 20.0,
        'x2': 0.0,
        'T_condensate': 100.0
    }
}

WINTER_PRESET = {
    'name': 'Winter Conditions',
    'description': 'Cold outside temperature, high flow demand',
    'params': {
        'K': 27.78,  # Lower gain for high flow (gives ~25C with Flow=0.9)
        'T1': 120.0,
        'T2': 60.0,
        'L': 10.0,
        'Kz': 1.0,
        'TambRef': 0.0,
        'KUW': 0.5,
        'TW': 90.0
    },
    'inputs': {
        'T_out': -10.0,  # Cold
        'Flow': 0.9,      # High flow
        'dt_sec': 0.5
    },
    'initial_state': {
        'x1': 20.0,
        'x2': 0.0,
        'T_condensate': 100.0
    }
}

SUMMER_PRESET = {
    'name': 'Summer Conditions',
    'description': 'Warm outside temperature, minimal heating',
    'params': {
        'K': 125.0,  # Higher gain for low flow (gives ~25C with Flow=0.2)
        'T1': 120.0,
        'T2': 60.0,
        'L': 10.0,
        'Kz': 1.0,
        'TambRef': 0.0,
        'KUW': 0.5,
        'TW': 90.0
    },
    'inputs': {
        'T_out': 25.0,   # Warm
        'Flow': 0.2,      # Low flow
        'dt_sec': 0.5
    },
    'initial_state': {
        'x1': 20.0,
        'x2': 0.0,
        'T_condensate': 100.0
    }
}

PRESETS = {
    'default': DEFAULT_PRESET,
    'fast': FAST_RESPONSE_PRESET,
    'slow': SLOW_RESPONSE_PRESET,
    'winter': WINTER_PRESET,
    'summer': SUMMER_PRESET
}


# ========== Disturbance Scenarios ==========

class DisturbanceScenario:
    """Base class for disturbance scenarios"""

    def __init__(self, channels):
        """
        Initialize scenario.

        Args:
            channels: Channels object to manipulate
        """
        self.channels = channels
        self.running = False

    async def execute(self):
        """Execute the scenario (override in subclasses)"""
        raise NotImplementedError

    def stop(self):
        """Stop the scenario"""
        self.running = False


class StepToutScenario(DisturbanceScenario):
    """Step change in outside temperature"""

    def __init__(self, channels, initial: float = 10.0, final: float = -5.0,
                 step_time: float = 30.0, duration: float = 300.0):
        """
        Args:
            channels: Channels object
            initial: Initial T_out value (°C)
            final: Final T_out value after step (°C)
            step_time: Time of step change (seconds)
            duration: Total scenario duration (seconds)
        """
        super().__init__(channels)
        self.initial = initial
        self.final = final
        self.step_time = step_time
        self.duration = duration

    async def execute(self):
        """Execute step in T_out"""
        self.running = True
        start_sim_time = self.channels.sim_time

        while self.running and (self.channels.sim_time - start_sim_time) < self.duration:
            elapsed = self.channels.sim_time - start_sim_time

            if elapsed < self.step_time:
                self.channels.T_out = self.initial
            else:
                self.channels.T_out = self.final

            await asyncio.sleep(0.1)  # Check every 100ms


class RampFlowScenario(DisturbanceScenario):
    """Ramp change in flow"""

    def __init__(self, channels, initial: float = 0.3, final: float = 0.9,
                 ramp_start: float = 10.0, ramp_duration: float = 60.0,
                 total_duration: float = 300.0):
        """
        Args:
            channels: Channels object
            initial: Initial Flow value
            final: Final Flow value
            ramp_start: Time to start ramp (seconds)
            ramp_duration: Duration of ramp (seconds)
            total_duration: Total scenario duration (seconds)
        """
        super().__init__(channels)
        self.initial = initial
        self.final = final
        self.ramp_start = ramp_start
        self.ramp_duration = ramp_duration
        self.total_duration = total_duration

    async def execute(self):
        """Execute ramp in Flow"""
        self.running = True
        start_sim_time = self.channels.sim_time

        while self.running and (self.channels.sim_time - start_sim_time) < self.total_duration:
            elapsed = self.channels.sim_time - start_sim_time

            if elapsed < self.ramp_start:
                flow = self.initial
            elif elapsed < self.ramp_start + self.ramp_duration:
                # Linear ramp
                progress = (elapsed - self.ramp_start) / self.ramp_duration
                flow = self.initial + progress * (self.final - self.initial)
            else:
                flow = self.final

            self.channels.Flow = flow
            await asyncio.sleep(0.1)


class PulseFlowScenario(DisturbanceScenario):
    """Pulse train on flow"""

    def __init__(self, channels, baseline: float = 0.5, amplitude: float = 0.3,
                 period: float = 30.0, duty_cycle: float = 0.5,
                 duration: float = 300.0):
        """
        Args:
            channels: Channels object
            baseline: Baseline Flow value
            amplitude: Pulse amplitude (added to baseline)
            period: Pulse period (seconds)
            duty_cycle: Fraction of period at high level (0-1)
            duration: Total scenario duration (seconds)
        """
        super().__init__(channels)
        self.baseline = baseline
        self.amplitude = amplitude
        self.period = period
        self.duty_cycle = duty_cycle
        self.duration = duration

    async def execute(self):
        """Execute pulse train on Flow"""
        self.running = True
        start_sim_time = self.channels.sim_time

        while self.running and (self.channels.sim_time - start_sim_time) < self.duration:
            elapsed = self.channels.sim_time - start_sim_time

            # Calculate position in current period
            phase = (elapsed % self.period) / self.period

            if phase < self.duty_cycle:
                flow = self.baseline + self.amplitude
            else:
                flow = self.baseline

            self.channels.Flow = flow
            await asyncio.sleep(0.1)


class SinusoidalToutScenario(DisturbanceScenario):
    """Sinusoidal variation in outside temperature (day/night cycle)"""

    def __init__(self, channels, mean: float = 10.0, amplitude: float = 8.0,
                 period: float = 120.0, duration: float = 600.0):
        """
        Args:
            channels: Channels object
            mean: Mean T_out value (°C)
            amplitude: Oscillation amplitude (°C)
            period: Oscillation period (seconds)
            duration: Total scenario duration (seconds)
        """
        super().__init__(channels)
        self.mean = mean
        self.amplitude = amplitude
        self.period = period
        self.duration = duration

    async def execute(self):
        """Execute sinusoidal T_out"""
        self.running = True
        start_sim_time = self.channels.sim_time

        while self.running and (self.channels.sim_time - start_sim_time) < self.duration:
            elapsed = self.channels.sim_time - start_sim_time

            # Sinusoidal oscillation
            T_out = self.mean + self.amplitude * np.sin(2 * np.pi * elapsed / self.period)

            self.channels.T_out = T_out
            await asyncio.sleep(0.1)


class WarmupScenario(DisturbanceScenario):
    """Greenhouse warmup from cold start"""

    def __init__(self, channels, duration: float = 600.0):
        """
        Args:
            channels: Channels object
            duration: Total scenario duration (seconds)
        """
        super().__init__(channels)
        self.duration = duration

    async def execute(self):
        """Execute warmup scenario"""
        self.running = True
        start_sim_time = self.channels.sim_time

        # Cold start conditions
        self.channels.T_out = 5.0
        self.channels.Flow = 0.0

        while self.running and (self.channels.sim_time - start_sim_time) < self.duration:
            elapsed = self.channels.sim_time - start_sim_time

            # Gradual flow increase over first 60 seconds
            if elapsed < 60.0:
                self.channels.Flow = 0.8 * (elapsed / 60.0)
            else:
                self.channels.Flow = 0.8

            await asyncio.sleep(0.1)


SCENARIOS = {
    'step_tout': StepToutScenario,
    'ramp_flow': RampFlowScenario,
    'pulse_flow': PulseFlowScenario,
    'sinusoidal_tout': SinusoidalToutScenario,
    'warmup': WarmupScenario
}


def get_preset(name: str) -> Dict[str, Any]:
    """
    Get parameter preset by name.

    Args:
        name: Preset name

    Returns:
        Preset dictionary (deep copy)
    """
    import copy
    return copy.deepcopy(PRESETS.get(name, DEFAULT_PRESET))


def get_scenario(name: str, channels, **kwargs) -> DisturbanceScenario:
    """
    Get disturbance scenario by name.

    Args:
        name: Scenario name
        channels: Channels object
        **kwargs: Scenario-specific parameters

    Returns:
        Scenario instance
    """
    scenario_class = SCENARIOS.get(name)
    if scenario_class is None:
        raise ValueError(f"Unknown scenario: {name}")

    return scenario_class(channels, **kwargs)
