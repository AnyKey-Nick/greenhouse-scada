"""
Alarm Configuration System for SCADA
======================================

Proper configurable alarm limits with hysteresis and enable/disable.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class AlarmLimit:
    """Single alarm limit configuration"""
    tag_name: str
    description: str
    low_low: Optional[float] = None
    low: Optional[float] = None
    high: Optional[float] = None
    high_high: Optional[float] = None
    hysteresis: float = 0.5
    enabled: bool = True
    units: str = ""

    def __post_init__(self):
        # State tracking for hysteresis
        self.low_low_active = False
        self.low_active = False
        self.high_active = False
        self.high_high_active = False


class AlarmManager:
    """
    Manages all alarm limits and checking logic.
    Implements proper hysteresis to avoid alarm chattering.
    """

    def __init__(self):
        self.limits: Dict[str, AlarmLimit] = {}
        self._init_default_limits()

    def _init_default_limits(self):
        """Initialize default alarm limits based on Ukrainian standards (ДСТУ 2860-94)"""

        # Outlet air temperature alarms (measured by THK-0083) - PRIMARY CONTROLLED VARIABLE
        self.limits['T_air_out'] = AlarmLimit(
            tag_name='T_air_out',
            description='Outlet Air Temperature (THK-0083)',
            low_low=18.0,      # Absolute minimum (ДСТУ 2860-94)
            low=20.0,          # Warning low
            high=24.0,         # Warning high
            high_high=25.0,    # Absolute maximum
            hysteresis=0.5,
            enabled=True,
            units='°C'
        )

        # Backward compatibility
        self.limits['T_greenhouse'] = self.limits['T_air_out']

        # Steam condensate temperature alarms
        self.limits['T_condensate'] = AlarmLimit(
            tag_name='T_condensate',
            description='Steam Condensate Temperature',
            low=70.0,          # Too cold - heat exchanger issue
            high=110.0,        # Too hot - safety issue
            hysteresis=2.0,
            enabled=True,
            units='°C'
        )

        # Backward compatibility
        self.limits['T_water'] = self.limits['T_condensate']

        # Flow alarms (Flow is normalized valve opening 0.0-1.0, NOT kg/s!)
        self.limits['Flow'] = AlarmLimit(
            tag_name='Flow',
            description='Valve Opening',
            low_low=0.0,       # Complete closure
            low=0.10,          # Too closed (10%)
            high=0.95,         # Almost fully open (95%)
            high_high=1.00,    # Fully open (100%)
            hysteresis=0.02,
            enabled=True,
            units='(0-1)'      # Normalized valve opening
        )

    def check_alarms(self, tag_name: str, value: float) -> List[Dict]:
        """
        Check value against alarm limits with hysteresis.

        Args:
            tag_name: Name of the tag to check
            value: Current value

        Returns:
            List of active alarms with severity and messages
        """
        if tag_name not in self.limits:
            return []

        limit = self.limits[tag_name]

        if not limit.enabled:
            return []

        alarms = []

        # Check HIGH-HIGH alarm
        if limit.high_high is not None:
            if value >= limit.high_high:
                limit.high_high_active = True
            elif value < (limit.high_high - limit.hysteresis):
                limit.high_high_active = False

            if limit.high_high_active:
                alarms.append({
                    'severity': 'HIGH_HIGH',
                    'tag': tag_name,
                    'message': f"{limit.description}: {value:.2f} {limit.units} (limit: {limit.high_high:.2f})",
                    'value': value,
                    'limit': limit.high_high
                })

        # Check HIGH alarm (only if HIGH-HIGH not active)
        if limit.high is not None and not limit.high_high_active:
            if value >= limit.high:
                limit.high_active = True
            elif value < (limit.high - limit.hysteresis):
                limit.high_active = False

            if limit.high_active:
                alarms.append({
                    'severity': 'HIGH',
                    'tag': tag_name,
                    'message': f"{limit.description}: {value:.2f} {limit.units} (limit: {limit.high:.2f})",
                    'value': value,
                    'limit': limit.high
                })

        # Check LOW alarm (only if LOW-LOW not active)
        if limit.low is not None and not limit.low_low_active:
            if value <= limit.low:
                limit.low_active = True
            elif value > (limit.low + limit.hysteresis):
                limit.low_active = False

            if limit.low_active:
                alarms.append({
                    'severity': 'LOW',
                    'tag': tag_name,
                    'message': f"{limit.description}: {value:.2f} {limit.units} (limit: {limit.low:.2f})",
                    'value': value,
                    'limit': limit.low
                })

        # Check LOW-LOW alarm
        if limit.low_low is not None:
            if value <= limit.low_low:
                limit.low_low_active = True
            elif value > (limit.low_low + limit.hysteresis):
                limit.low_low_active = False

            if limit.low_low_active:
                alarms.append({
                    'severity': 'LOW_LOW',
                    'tag': tag_name,
                    'message': f"{limit.description}: {value:.2f} {limit.units} (limit: {limit.low_low:.2f})",
                    'value': value,
                    'limit': limit.low_low
                })

        return alarms

    def check_all_alarms(self, data_snapshot) -> List[Dict]:
        """Check all configured alarms against current data"""
        all_alarms = []

        # Check outlet air temperature alarms (PRIMARY - measured by THK-0083)
        if hasattr(data_snapshot, 'T_air_out'):
            all_alarms.extend(self.check_alarms('T_air_out', data_snapshot.T_air_out))
        elif hasattr(data_snapshot, 'T_greenhouse'):  # Backward compatibility
            all_alarms.extend(self.check_alarms('T_air_out', data_snapshot.T_greenhouse))

        # Check condensate temperature alarms
        if hasattr(data_snapshot, 'T_condensate'):
            all_alarms.extend(self.check_alarms('T_condensate', data_snapshot.T_condensate))
        elif hasattr(data_snapshot, 'T_water'):  # Backward compatibility
            all_alarms.extend(self.check_alarms('T_condensate', data_snapshot.T_water))

        # Check valve opening alarms
        if hasattr(data_snapshot, 'Flow'):
            all_alarms.extend(self.check_alarms('Flow', data_snapshot.Flow))

        return all_alarms

    def set_limit(self, tag_name: str, limit_type: str, value: Optional[float]):
        """
        Set a specific alarm limit.

        Args:
            tag_name: Tag to configure
            limit_type: 'low_low', 'low', 'high', 'high_high'
            value: Limit value (None to disable that limit)
        """
        if tag_name in self.limits:
            setattr(self.limits[tag_name], limit_type, value)

    def set_enabled(self, tag_name: str, enabled: bool):
        """Enable or disable alarms for a tag"""
        if tag_name in self.limits:
            self.limits[tag_name].enabled = enabled

    def get_limit(self, tag_name: str) -> Optional[AlarmLimit]:
        """Get alarm limit configuration for a tag"""
        return self.limits.get(tag_name)

    def get_all_limits(self) -> Dict[str, AlarmLimit]:
        """Get all alarm limit configurations"""
        return self.limits.copy()
