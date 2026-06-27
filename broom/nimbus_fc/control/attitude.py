"""Attitude loop: desired orientation -> body-rate setpoint.

Quaternion P-controller, PX4-style. The attitude error comes out as a
body-frame rotation vector; scale it by per-axis P gains to get the rate
setpoint, add any yaw-rate feedforward, then clamp so the inner loop never
sees a ridiculous demand.
"""

from __future__ import annotations

import numpy as np

from ..core import math3d as m
from ..core.params import Params


class AttitudeController:
    def __init__(self, params: Params):
        self.p = params
        self.kp = np.array([params.kp_att_rp, params.kp_att_rp, params.kp_att_yaw])
        self.rate_limit = np.array([
            params.att_rate_limit_rp, params.att_rate_limit_rp, params.max_yaw_rate,
        ])

    def update(self, q_cur: np.ndarray, q_des: np.ndarray,
               yaw_rate_ff: float = 0.0) -> np.ndarray:
        err = m.quat_error_angle_axis(q_cur, q_des)  # body-frame rotation vector
        rate_sp = self.kp * err
        rate_sp[2] += yaw_rate_ff
        return np.clip(rate_sp, -self.rate_limit, self.rate_limit)
