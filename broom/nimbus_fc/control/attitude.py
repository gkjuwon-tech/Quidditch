"""Attitude loop: where we want to point -> body-rate setpoint.

Plain quaternion P-controller, PX4-flavoured. Take the attitude error as a
body-frame rotation vector, scale per axis, bolt on the rider's yaw-rate
feedforward. The result gets clamped so the inner loop can never be handed a
lunatic rate demand.
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
        att_err = m.quat_error_angle_axis(q_cur, q_des)   # body-frame rot vector
        rate_sp = self.kp * att_err
        rate_sp[2] += yaw_rate_ff
        return np.clip(rate_sp, -self.rate_limit, self.rate_limit)
