"""
PI Controller for Temperature Control
======================================

Proportional-Integral (PI) controller for automatic temperature regulation.
"""


class PIController:
    """
    PI Controller for temperature regulation

    The controller adjusts the steam flow to maintain the desired temperature.

    PI Algorithm:
        u(t) = Kp * e(t) + Ki * ∫e(t)dt

    where:
        e(t) = setpoint - measured_value (error)
        Kp = proportional gain
        Ki = integral gain
        u(t) = control output (Flow)
    """

    def __init__(self, Kp: float = 0.1, Ki: float = 0.01,
                 setpoint: float = 22.0,
                 output_min: float = 0.0, output_max: float = 1.0):
        """
        Initialize PI controller

        Args:
            Kp: Proportional gain (default: 0.1)
            Ki: Integral gain (default: 0.01)
            setpoint: Target temperature (default: 22.0°C)
            output_min: Minimum output (Flow min)
            output_max: Maximum output (Flow max)
        """
        self.Kp = Kp
        self.Ki = Ki
        self.setpoint = setpoint
        self.output_min = output_min
        self.output_max = output_max

        # Internal state
        self.integral = 0.0
        self.last_error = 0.0

        # Anti-windup
        self.integral_max = 100.0

    def reset(self):
        """Reset controller state"""
        self.integral = 0.0
        self.last_error = 0.0

    def set_setpoint(self, setpoint: float):
        """Change setpoint"""
        self.setpoint = setpoint
        # Reset integral to avoid windup on setpoint change
        self.integral = 0.0

    def initialize_bumpless(self, current_output: float, measured_value: float):
        """
        Initialize controller for bumpless transfer to AUTO mode.

        Sets integral so PI output matches current manual output.

        Args:
            current_output: Current manual output (Flow 0-1)
            measured_value: Current process value (temperature)
        """
        error = self.setpoint - measured_value
        P = self.Kp * error

        # Solve for integral: current_output = P + Ki * integral
        # integral = (current_output - P) / Ki
        if abs(self.Ki) > 1e-6:  # Avoid division by zero
            self.integral = (current_output - P) / self.Ki
            # Clamp to prevent excessive values
            self.integral = max(-self.integral_max, min(self.integral_max, self.integral))
        else:
            self.integral = 0.0

        self.last_error = error

    def update(self, measured_value: float, dt: float) -> float:
        """
        Calculate control output with proper back-calculation anti-windup

        Args:
            measured_value: Current temperature (°C)
            dt: Time step (seconds) - MUST be in seconds!

        Returns:
            Control output (Flow: 0.0 - 1.0)
        """
        # Calculate error (SP - PV)
        error = self.setpoint - measured_value

        # Proportional term
        P = self.Kp * error

        # Integral term
        I = self.Ki * self.integral

        # Calculate unclamped output
        output_unclamped = P + I

        # Clamp output to actuator limits
        output = max(self.output_min, min(self.output_max, output_unclamped))

        # Back-calculation anti-windup: only integrate when not saturated
        # or when integration would reduce saturation
        if (output == output_unclamped) or \
           (output >= self.output_max and error < 0) or \
           (output <= self.output_min and error > 0):
            # Not saturated OR integration helps move away from saturation
            self.integral += error * dt

            # Limit integral to prevent excessive windup
            self.integral = max(-self.integral_max, min(self.integral_max, self.integral))

        # Store for status display
        self.last_error = error

        return output

    def get_status(self) -> dict:
        """Get controller status for display"""
        return {
            'setpoint': self.setpoint,
            'error': self.last_error,
            'integral': self.integral,
            'Kp': self.Kp,
            'Ki': self.Ki
        }
