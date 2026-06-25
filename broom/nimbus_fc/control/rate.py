"""Innermost loop: body-rate -> torque (the thing that actually keeps you alive).

Runs at the full inner-loop rate. PID per body axis [roll, pitch, yaw] with
derivative on the gyro signal. This is the loop Betaflight obsesses over; for
a 120 kg manned vehicle we trade raw bandwidth for smoothness.
"""

from __future__ import annotations

import numpy as np

from ..core.params import Params
from .pid import PID


class RateController:
    def __init__(self, params: Params):
        self.p = params
        self.pid = PID(params.kp_rate, params.ki_rate, params.kd_rate,
                       params.rate_i_limit)

    def reset(self) -> None:
        self.pid.reset()

    def update(self, rate_sp: np.ndarray, omega: np.ndarray, dt: float,
               freeze_i: bool = False) -> np.ndarray:
        """Return body torque command [tau_x, tau_y, tau_z] (Nm)."""
        return self.pid.update(rate_sp, omega, dt, freeze_i=freeze_i)
