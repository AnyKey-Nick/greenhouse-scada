"""
Greenhouse Heat Exchanger Model - TRACE-MODE Compatible
========================================================

This module implements the exact mathematical model of the steam → shell-and-tube
heat exchanger → water/air greenhouse heating line, preserving bit-for-bit
compatibility with the Structured Text logic used in TRACE MODE.

Physical Process (per diploma):
- Secondary steam (~100°C) flows through control valve (with transport delay L)
- Shell-and-tube heat exchanger: steam in tubes, air on shell side
- Air enters from bottom (~16-22°C), exits at top (heated)
- Second-order aperiodic link models air heating dynamics
- First-order lag models steam condensate temperature
- Controlled variable: outlet air temperature (measured by THK-0083)
"""

import numpy as np
from typing import Dict, Tuple, Any
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, ConfigDict


class ModelParams(BaseModel):
    """Parameter validation using pydantic"""
    model_config = ConfigDict(validate_assignment=True)

    K: float = Field(0.8, description="Gain coefficient")
    T1: float = Field(120.0, gt=0, description="First time constant (s)")
    T2: float = Field(60.0, gt=0, description="Second time constant (s)")
    L: float = Field(10.0, ge=0, description="Transport delay (s)")
    Kz: float = Field(0.02, description="Ambient temperature coefficient")
    TambRef: float = Field(0.0, description="Reference ambient temperature (°C)")
    KUW: float = Field(0.5, description="Condensate heating coefficient")
    TW: float = Field(90.0, gt=0, description="Condensate time constant (s)")


@dataclass
class ModelState:
    """Internal state of the greenhouse HEX model"""
    x1: float = 20.0  # First state variable (outlet air temperature)
    x2: float = 0.0   # Second state variable (derivative)
    T_condensate: float = 100.0  # Steam condensate temperature
    delay_buffer: np.ndarray = field(default_factory=lambda: np.array([]))
    delay_idx: int = 0

    def copy(self):
        """Deep copy of state"""
        return ModelState(
            x1=self.x1,
            x2=self.x2,
            T_condensate=self.T_condensate,
            delay_buffer=self.delay_buffer.copy() if len(self.delay_buffer) > 0 else np.array([]),
            delay_idx=self.delay_idx
        )


class DelayLine:
    """Ring buffer implementing transport delay with exact TRACE-MODE behavior"""

    def __init__(self, delay_sec: float, dt_sec: float):
        """
        Initialize delay line.

        Args:
            delay_sec: Delay time in seconds (L parameter)
            dt_sec: Time step in seconds
        """
        self.delay_sec = delay_sec
        self.dt_sec = dt_sec
        self.N = max(1, int(np.round(delay_sec / dt_sec)))
        self.buffer = np.zeros(self.N)
        self.idx = 0

    def push(self, value: float) -> float:
        """
        Push new value and return delayed value.

        Args:
            value: Input value to delay

        Returns:
            Delayed output (value from L seconds ago)
        """
        # Read delayed value before overwriting
        delayed = self.buffer[self.idx]

        # Write new value
        self.buffer[self.idx] = value

        # Advance circular index
        self.idx = (self.idx + 1) % self.N

        return delayed

    def resize(self, new_delay_sec: float):
        """
        Resize delay line without artifacts.

        Args:
            new_delay_sec: New delay time in seconds
        """
        old_N = self.N
        new_N = max(1, int(np.round(new_delay_sec / self.dt_sec)))

        if new_N == old_N:
            self.delay_sec = new_delay_sec
            return

        # Create new buffer
        new_buffer = np.zeros(new_N)

        # Copy as much history as possible
        if new_N < old_N:
            # Shrinking: keep most recent samples
            for i in range(new_N):
                old_idx = (self.idx - new_N + i) % old_N
                new_buffer[i] = self.buffer[old_idx]
        else:
            # Growing: pad with oldest value
            oldest_val = self.buffer[(self.idx) % old_N]
            new_buffer[:] = oldest_val
            # Copy existing history
            for i in range(old_N):
                old_idx = (self.idx + i) % old_N
                new_buffer[i] = self.buffer[old_idx]

        self.buffer = new_buffer
        self.N = new_N
        self.delay_sec = new_delay_sec
        self.idx = 0


class GreenhouseHEXModel:
    """
    Greenhouse Heat Exchanger Model - TRACE-MODE Compatible

    This class implements the exact equations from the TRACE MODE Structured Text:

    1. Transport delay: u_dead = Delay(Flow, L)
    2. Second-order aperiodic link:
       ydd = -(1/T1 + 1/T2)*x2 - (1/(T1*T2))*x1 + K*u_dead + Kz*(T_out - TambRef)
       x2 += dt * ydd
       x1 += dt * x2
       y_out = x1
    3. Condensate temperature dynamics:
       T_condensate += dt * ((KUW * y_out - T_condensate) / TW)
    4. Outlet air temperature (measured by THK-0083):
       T_air_out = y_out

    Public API:
    - reset(): Reset to initial conditions
    - set_params(**kwargs): Update model parameters
    - step(T_air_in, Flow, dt_sec): Execute one simulation step
    """

    def __init__(self, params: ModelParams = None, initial_state: ModelState = None):
        """
        Initialize the greenhouse HEX model.

        Args:
            params: Model parameters (defaults to ModelParams())
            initial_state: Initial state (defaults to ModelState())
        """
        self.params = params or ModelParams()
        self.initial_state = initial_state or ModelState()
        self.state = self.initial_state.copy()

        # Initialize delay line
        self._init_delay_line()

    def _init_delay_line(self, dt_sec: float = 0.5):
        """Initialize the transport delay line"""
        self.delay_line = DelayLine(self.params.L, dt_sec)

    def reset(self, initial_state: ModelState = None):
        """
        Reset model to initial conditions.

        Args:
            initial_state: New initial state (optional)
        """
        if initial_state is not None:
            self.initial_state = initial_state
        self.state = self.initial_state.copy()
        self._init_delay_line()

    def set_params(self, dt_sec: float = None, **kwargs):
        """
        Update model parameters.

        Args:
            dt_sec: Time step (used for delay line resize)
            **kwargs: Parameter updates (K, T1, T2, L, Kz, TambRef, KUW, TW)
        """
        # Update parameters
        for key, value in kwargs.items():
            if hasattr(self.params, key):
                setattr(self.params, key, value)

        # Handle delay line resize if L changed
        if 'L' in kwargs and dt_sec is not None:
            self.delay_line.resize(self.params.L)
        elif dt_sec is not None:
            self.delay_line.dt_sec = dt_sec
            self.delay_line.resize(self.params.L)

    def step(self, T_air_in: float, Flow: float, dt_sec: float) -> Dict[str, float]:
        """
        Execute one simulation step with TRACE-MODE equations.

        Args:
            T_air_in: Inlet air temperature (°C) - a.k.a. T_out/ambient
            Flow: Steam valve flow control signal (0-1 normalized)
            dt_sec: Integration time step (seconds)

        Returns:
            Dictionary with outputs:
            - T_air_out: Outlet air temperature (°C) - measured by THK-0083
            - T_condensate: Steam condensate temperature (°C)
            - x1: First state variable
            - x2: Second state variable
            - u_dead: Delayed flow signal
        """
        # Update delay line dt if changed
        if abs(self.delay_line.dt_sec - dt_sec) > 1e-9:
            self.delay_line.dt_sec = dt_sec
            self.delay_line.resize(self.params.L)

        # === TRACE-MODE Equation Implementation ===

        # 1. Transport delay
        u_dead = self.delay_line.push(Flow)

        # 2. Compute intermediate coefficients
        sumInvT = (1.0 / self.params.T1) + (1.0 / self.params.T2)
        invT1T2 = 1.0 / (self.params.T1 * self.params.T2)

        # 3. Second-order aperiodic link differential equation
        # Standard form: T1*T2*ydd + (T1+T2)*yd + (y - y_target) = 0
        # Where: y_target = K*u + Kz*(T_air_in - Tref)
        # This provides a restoring force toward the setpoint
        y_target = self.params.K * u_dead + self.params.Kz * (T_air_in - self.params.TambRef)
        ydd = (-sumInvT * self.state.x2
               - invT1T2 * (self.state.x1 - y_target))  # Restore toward target

        # 4. Integrate using Euler method (matching TRACE MODE)
        # IMPORTANT: Update x1 using OLD x2, then update x2
        x2_old = self.state.x2
        self.state.x2 = x2_old + dt_sec * ydd
        self.state.x1 = self.state.x1 + dt_sec * x2_old

        # 5. Output is first state variable (outlet air temperature)
        y_out = self.state.x1

        # 6. Condensate temperature dynamics (first-order lag)
        dT_condensate = (self.params.KUW * y_out - self.state.T_condensate) / self.params.TW
        self.state.T_condensate += dt_sec * dT_condensate

        # 7. Outlet air temperature (measured by THK-0083)
        T_air_out = y_out

        return {
            'T_air_out': T_air_out,
            'T_condensate': self.state.T_condensate,
            'x1': self.state.x1,
            'x2': self.state.x2,
            'u_dead': u_dead
        }


def tracemode_step(
    T_air_in: float,
    Flow: float,
    dt_sec: float,
    state: Dict[str, Any],
    params: Dict[str, float]
) -> Tuple[Dict[str, float], Dict[str, Any]]:
    """
    Functional wrapper matching TRACE-MODE ST code naming conventions.

    This function provides a stateless interface for model parity testing,
    where state and parameters are passed explicitly as dictionaries.

    Args:
        T_air_in: Inlet air temperature (°C) - ambient/T_out
        Flow: Steam valve flow control signal (0-1)
        dt_sec: Integration time step (seconds)
        state: Dictionary with 'x1', 'x2', 'T_condensate', 'delay_buffer', 'delay_idx'
        params: Dictionary with 'K', 'T1', 'T2', 'L', 'Kz', 'TambRef', 'KUW', 'TW'

    Returns:
        Tuple of (outputs, new_state) where:
        - outputs: Dict with 'T_air_out', 'T_condensate', 'x1', 'x2', 'u_dead'
        - new_state: Updated state dictionary
    """
    # Extract state
    x1 = state['x1']
    x2 = state['x2']
    T_condensate = state['T_condensate']
    delay_buffer = np.array(state['delay_buffer'])
    delay_idx = state['delay_idx']

    # Extract parameters
    K = params['K']
    T1 = params['T1']
    T2 = params['T2']
    L = params['L']
    Kz = params['Kz']
    TambRef = params['TambRef']
    KUW = params['KUW']
    TW = params['TW']

    # Delay line operations
    N = max(1, int(np.round(L / dt_sec)))
    if len(delay_buffer) != N:
        # Resize buffer
        new_buffer = np.zeros(N)
        if len(delay_buffer) > 0:
            if N < len(delay_buffer):
                for i in range(N):
                    old_idx = (delay_idx - N + i) % len(delay_buffer)
                    new_buffer[i] = delay_buffer[old_idx]
            else:
                oldest_val = delay_buffer[delay_idx % len(delay_buffer)]
                new_buffer[:] = oldest_val
                for i in range(len(delay_buffer)):
                    old_idx = (delay_idx + i) % len(delay_buffer)
                    new_buffer[i] = delay_buffer[old_idx]
        delay_buffer = new_buffer
        delay_idx = 0

    # Read delayed value
    u_dead = delay_buffer[delay_idx]

    # Write new value
    delay_buffer[delay_idx] = Flow

    # Advance index
    delay_idx = (delay_idx + 1) % N

    # Second-order aperiodic dynamics
    # Standard form: T1*T2*ydd + (T1+T2)*yd + (y - y_target) = 0
    sumInvT = (1.0 / T1) + (1.0 / T2)
    invT1T2 = 1.0 / (T1 * T2)

    y_target = K * u_dead + Kz * (T_air_in - TambRef)
    ydd = -sumInvT * x2 - invT1T2 * (x1 - y_target)

    # IMPORTANT: Use OLD x2 for x1 update (Euler method)
    x2_new = x2 + dt_sec * ydd
    x1_new = x1 + dt_sec * x2

    y_out = x1_new

    # Condensate temperature dynamics
    dT_condensate = (KUW * y_out - T_condensate) / TW
    T_condensate_new = T_condensate + dt_sec * dT_condensate

    T_air_out = y_out

    # Outputs
    outputs = {
        'T_air_out': T_air_out,
        'T_condensate': T_condensate_new,
        'x1': x1_new,
        'x2': x2_new,
        'u_dead': u_dead
    }

    # New state
    new_state = {
        'x1': x1_new,
        'x2': x2_new,
        'T_condensate': T_condensate_new,
        'delay_buffer': delay_buffer.tolist(),
        'delay_idx': delay_idx
    }

    return outputs, new_state
