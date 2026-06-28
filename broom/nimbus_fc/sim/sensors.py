"""Fake sensors: turn the truth state into noisy measurements.

The whole point is that the estimator (and so the controller) never touches
ground truth, just like the real airframe. We model a 6-axis IMU (accel +
gyro, both with a turn-on bias and white noise) and a fused GNSS/RTK + baro
that reports position and velocity at a slower rate.
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
        # turn-on biases: drawn once and frozen for the whole run
        self.gyro_bias = self.rng.normal(0, 0.01, 3)
        self.accel_bias = self.rng.normal(0, 0.05, 3)
        self.gyro_noise = 0.02      # rad/s
        self.accel_noise = 0.15     # m/s^2
        self.gps_pos_noise = 0.08   # m (RTK-class)
        self.gps_vel_noise = 0.05   # m/s

    def imu(self, state: State, accel_world: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """(gyro [body rad/s], accel [body m/s^2, specific force]).

        Specific force is (a_world - gravity) rotated into the body. That's what
        an accelerometer actually senses -- it feels the thrust, not free-fall.
        """
        specific_force_world = accel_world - np.array([0.0, 0.0, -m.GRAVITY])
        accel_body = m.quat_rotate_inv(state.quat, specific_force_world)
        gyro = state.omega + self.gyro_bias + self.rng.normal(0, self.gyro_noise, 3)
        accel = accel_body + self.accel_bias + self.rng.normal(0, self.accel_noise, 3)
        return gyro, accel

    def gnss(self, state: State) -> tuple[np.ndarray, np.ndarray]:
        """(pos_meas, vel_meas), world frame."""
        pos = state.pos + self.rng.normal(0, self.gps_pos_noise, 3)
        vel = state.vel + self.rng.normal(0, self.gps_vel_noise, 3)
        return pos, vel

    # reference field direction, world ENU, unit-ish. mostly north (+y) with a
    # little dip. only its direction matters as a yaw reference.
    mag_world = np.array([0.0, 0.96, -0.28])
    mag_noise = 0.02

    def mag(self, state: State) -> np.ndarray:
        """Field direction in the body frame (roughly unit)."""
        body = m.quat_rotate_inv(state.quat, self.mag_world)
        return body + self.rng.normal(0, self.mag_noise, 3)
