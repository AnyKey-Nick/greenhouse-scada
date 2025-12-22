"""
Controllers Module - P, PI, PID with Anti-Windup
=================================================

Provides standard industrial controllers with proper anti-windup,
bumpless transfer, and mode switching for SCADA HMI.
"""

from enum import Enum
from typing import Optional


class ControllerType(Enum):
    """Controller type enumeration"""
    P = "P"
    PI = "PI"
    PID = "PID"


class AntiWindupMode(Enum):
    """Anti-windup strategy"""
    CLAMPING = "clamping"  # Stop integrating when saturated
    BACK_CALCULATION = "back_calculation"  # Back-calculate integral


class Controller:
    """
    Universal PID controller with selectable P/PI/PID modes.

    Features:
    - P, PI, or PID control
    - Anti-windup (clamping or back-calculation)
    - Bumpless transfer between manual and auto
    - Output limiting
    - Derivative filtering (optional)
    """

    def __init__(
        self,
        controller_type: ControllerType = ControllerType.PI,
        Kp: float = 0.1,
        Ki: float = 0.01,
        Kd: float = 0.0,
        setpoint: float = 22.0,
        output_min: float = 0.0,
        output_max: float = 1.0,
        anti_windup: AntiWindupMode = AntiWindupMode.BACK_CALCULATION,
        derivative_filter_tau: float = 0.1
    ):
        """
        Initialize controller.

        Args:
            controller_type: P, PI, or PID
            Kp: Proportional gain
            Ki: Integral gain (used only in PI/PID)
            Kd: Derivative gain (used only in PID)
            setpoint: Target value
            output_min: Minimum output limit
            output_max: Maximum output limit
            anti_windup: Anti-windup strategy
            derivative_filter_tau: Derivative filter time constant (seconds)
        """
        self.controller_type = controller_type
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.output_min = output_min
        self.output_max = output_max
        self.anti_windup = anti_windup
        self.derivative_filter_tau = derivative_filter_tau

        # Internal state
        self.integral = 0.0
        self.last_error = 0.0
        self.last_pv = 0.0
        self.filtered_derivative = 0.0

        # Individual term values (for display)
        self.P_term = 0.0
        self.I_term = 0.0
        self.D_term = 0.0

        # Anti-windup limits
        self.integral_max = 100.0  # Maximum integral value

        # Tracking for back-calculation
        self.tracking_gain = 1.0 / max(self.Ki, 1e-6) if self.Ki > 0 else 0.0

    def reset(self):
        """Reset controller state"""
        self.integral = 0.0
        self.last_error = 0.0
        self.last_pv = 0.0
        self.filtered_derivative = 0.0

    def set_setpoint(self, setpoint: float):
        """
        Change setpoint.

        Args:
            setpoint: New target value
        """
        self.setpoint = setpoint
        # Optionally reset integral to avoid transient
        # self.integral = 0.0

    def set_type(self, controller_type: ControllerType):
        """
        Change controller type.

        Args:
            controller_type: New controller type (P/PI/PID)
        """
        self.controller_type = controller_type
        # Reset states that may not be used in new mode
        if controller_type == ControllerType.P:
            self.integral = 0.0
            self.filtered_derivative = 0.0
        elif controller_type == ControllerType.PI:
            self.filtered_derivative = 0.0

    def initialize_bumpless(self, current_output: float, measured_value: float):
        """
        Initialize controller for bumpless transfer to AUTO mode.

        Sets integral so controller output matches current manual output.

        Args:
            current_output: Current manual output (e.g., Flow 0-1)
            measured_value: Current process value (e.g., temperature)
        """
        error = self.setpoint - measured_value
        P = self.Kp * error

        # For PI/PID: solve for integral term
        # current_output = P + Ki * integral [+ Kd * derivative]
        # We ignore D term for bumpless transfer
        if self.controller_type in [ControllerType.PI, ControllerType.PID]:
            if abs(self.Ki) > 1e-6:
                self.integral = (current_output - P) / self.Ki
                # Clamp integral
                self.integral = max(-self.integral_max, min(self.integral_max, self.integral))
            else:
                self.integral = 0.0
        else:
            self.integral = 0.0

        self.last_error = error
        self.last_pv = measured_value
        self.filtered_derivative = 0.0

    def update(self, measured_value: float, dt: float) -> float:
        """
        Calculate control output.

        Args:
            measured_value: Current process variable (PV)
            dt: Time step (seconds) - MUST be in seconds!

        Returns:
            Control output (clamped to output_min..output_max)
        """
        # Calculate error (SP - PV)
        error = self.setpoint - measured_value

        # === PROPORTIONAL TERM ===
        P = self.Kp * error
        self.P_term = P

        # === INTEGRAL TERM ===
        I = 0.0
        if self.controller_type in [ControllerType.PI, ControllerType.PID]:
            I = self.Ki * self.integral
        self.I_term = I

        # === DERIVATIVE TERM ===
        D = 0.0
        if self.controller_type == ControllerType.PID:
            # Derivative on PV (not error) to avoid derivative kick on setpoint change
            raw_derivative = -(measured_value - self.last_pv) / dt if dt > 0 else 0.0

            # Apply first-order filter to derivative
            alpha = dt / (self.derivative_filter_tau + dt)
            self.filtered_derivative = (1 - alpha) * self.filtered_derivative + alpha * raw_derivative

            D = self.Kd * self.filtered_derivative
        self.D_term = D

        # === CALCULATE OUTPUT ===
        output_unclamped = P + I + D
        output = max(self.output_min, min(self.output_max, output_unclamped))

        # === ANTI-WINDUP ===
        if self.controller_type in [ControllerType.PI, ControllerType.PID]:
            if self.anti_windup == AntiWindupMode.CLAMPING:
                # Clamping: only integrate when not saturated or integrating away from saturation
                if (output == output_unclamped) or \
                   (output >= self.output_max and error < 0) or \
                   (output <= self.output_min and error > 0):
                    # Not saturated OR integration reduces saturation
                    self.integral += error * dt
                    # Limit integral magnitude
                    self.integral = max(-self.integral_max, min(self.integral_max, self.integral))

            elif self.anti_windup == AntiWindupMode.BACK_CALCULATION:
                # Back-calculation: track saturation error
                saturation_error = output - output_unclamped
                self.integral += error * dt + self.tracking_gain * saturation_error * dt
                # Limit integral magnitude
                self.integral = max(-self.integral_max, min(self.integral_max, self.integral))

        # === UPDATE STATE ===
        self.last_error = error
        self.last_pv = measured_value

        return output

    def get_status(self) -> dict:
        """
        Get controller status for display.

        Returns:
            Dictionary with controller state
        """
        return {
            'type': self.controller_type.value,
            'setpoint': self.setpoint,
            'error': self.last_error,
            'integral': self.integral,
            'derivative': self.filtered_derivative if self.controller_type == ControllerType.PID else 0.0,
            'Kp': self.Kp,
            'Ki': self.Ki if self.controller_type in [ControllerType.PI, ControllerType.PID] else 0.0,
            'Kd': self.Kd if self.controller_type == ControllerType.PID else 0.0,
            'P_term': self.P_term,
            'I_term': self.I_term,
            'D_term': self.D_term
        }
