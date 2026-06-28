"""Innermost loop: body rate -> torque. The one that keeps you alive.

Full-rate PID, one per body axis [roll, pitch, yaw], D taken off the gyro.
Betaflight lives and dies on this loop; on a 120 kg manned thing we
deliberately give up some bandwidth to get smoothness back.
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
        """Body torque command [tau_x, tau_y, tau_z], Nm."""
        return self.pid.update(rate_sp, omega, dt, freeze_i=freeze_i)
