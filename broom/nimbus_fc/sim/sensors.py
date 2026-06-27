"""Synthetic sensor suite: generate sensor measurements from truth state.

So the estimator (and therefore the controller) never sees the truth directly
-- exactly like the real vehicle. Models a 6-axis IMU (accel + gyro with bias
and white noise) and a fused GNSS/RTK + barometer giving position & velocity
at a lower rate.
"""

from __future__ import annotations

import numpy as np

from ..core import math3d as m
from ..core.params import Params
from ..core.types import State


class SensorSuite:
    def __init__(self, params: Params, seed: int = 0):
        self.p = params
        self.rng = np.random.default_rng(seed)
        # Fixed biases drawn once (turn-on bias).
        self.gyro_bias = self.rng.normal(0, 0.01, 3)
        self.accel_bias = self.rng.normal(0, 0.05, 3)
        self.gyro_noise = 0.02      # rad/s
        self.accel_noise = 0.15     # m/s^2
        self.gps_pos_noise = 0.08   # m (RTK-class)
        self.gps_vel_noise = 0.05   # m/s

    def imu(self, state: State, accel_world: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Return (gyro_meas [body rad/s], accel_meas [body m/s^2, specific force]).

        Specific force = (a_world - gravity) rotated into the body frame; this is
        what a real accelerometer reads (it feels thrust, not free-fall).
        """
        specific_force_world = accel_world - np.array([0.0, 0.0, -m.GRAVITY])
        accel_body = m.quat_rotate_inv(state.quat, specific_force_world)
        gyro = state.omega + self.gyro_bias + self.rng.normal(0, self.gyro_noise, 3)
        accel = accel_body + self.accel_bias + self.rng.normal(0, self.accel_noise, 3)
        return gyro, accel

    def gnss(self, state: State) -> tuple[np.ndarray, np.ndarray]:
        """Return (pos_meas, vel_meas) in world frame."""
        pos = state.pos + self.rng.normal(0, self.gps_pos_noise, 3)
        vel = state.vel + self.rng.normal(0, self.gps_vel_noise, 3)
        return pos, vel

    # Reference field direction in world ENU (unit). Mostly north (+y) with a
    # bit of inclination; only the direction matters for a yaw reference.
    mag_world = np.array([0.0, 0.96, -0.28])
    mag_noise = 0.02

    def mag(self, state: State) -> np.ndarray:
        """Return the magnetic field direction in the BODY frame (unit-ish)."""
        body = m.quat_rotate_inv(state.quat, self.mag_world)
        return body + self.rng.normal(0, self.mag_noise, 3)
