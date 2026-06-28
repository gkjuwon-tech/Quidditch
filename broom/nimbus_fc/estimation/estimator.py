"""The simple estimator: Mahony attitude + an alpha-beta INS for pos/vel.

Two loosely coupled filters. For a slow-moving manned vehicle that's plenty,
and it's a lot easier to trust than a hand-rolled EKF.

Attitude is a Mahony complementary filter: integrate bias-corrected gyro for
the fast part, nudge tilt toward the accelerometer's gravity reading for the
slow part, and back out the gyro bias through the integral term.

Pos/vel is INS dead-reckoning (accel rotated to world, gravity removed) pulled
back toward GNSS/RTK with a couple of fixed gains.

Same ideas as the Crazyflie complementary estimator and PX4's Q attitude
estimator, minus any dependencies.
"""

from __future__ import annotations

import numpy as np

from ..core import math3d as m
from ..core.params import Params
from ..core.types import State


class Estimator:
    def __init__(self, params: Params, init: State | None = None):
        self.p = params
        s = init if init is not None else State()
        self.q = s.quat.copy()
        self.pos = s.pos.copy()
        self.vel = s.vel.copy()
        self.gyro_bias = np.zeros(3)
        self._a_kin = np.zeros(3)   # low-passed world-frame kinematic accel

        # mahony gains
        self.kp_mahony = 2.0
        self.ki_mahony = 0.08
        # GNSS fusion gains (per second), applied as 1-exp each update. We fuse
        # velocity hard on purpose: the position controller's damping term
        # rides on a tight velocity estimate. a loose one lags the damping and
        # the thing overshoots once you're flying on the estimate.
        self.k_pos = 8.0
        self.k_vel = 10.0

    def predict(self, gyro: np.ndarray, accel_body: np.ndarray, dt: float) -> None:
        """High-rate IMU prediction. Runs every inner loop."""
        # mahony tilt correction, but with the maneuver acceleration backed out.
        # the accelerometer reads specific force (a_world - g); to get a clean
        # gravity reference even mid-maneuver we subtract the known kinematic
        # accel (low-passed velocity estimate):
        #     gravity_body = accel_body - R^T * a_kin_world
        # that kills the classic Mahony failure (attitude wrecked by hard
        # maneuvers) without throwing the accelerometer out entirely.
        grav_ref_body = accel_body - m.quat_rotate_inv(self.q, self._a_kin)
        g_est_body = m.quat_rotate_inv(self.q, np.array([0.0, 0.0, 1.0]))
        n = float(np.linalg.norm(grav_ref_body))
        corr = np.zeros(3)
        if n > 1e-3:
            # trust it less the further the recovered |g| is from the real one
            trust = np.exp(-abs(n - m.GRAVITY) / 3.0)
            corr = trust * np.cross(grav_ref_body / n, g_est_body)
            self.gyro_bias += -self.ki_mahony * corr * dt
        omega = gyro - self.gyro_bias + self.kp_mahony * corr
        self.q = m.quat_integrate(self.q, omega, dt)

        # pos/vel: plain specific-force dead reckoning
        accel_world = m.quat_rotate(self.q, accel_body) + np.array([0, 0, -m.GRAVITY])
        # stash the low-passed kinematic accel for next step's gravity comp
        beta = 1.0 - np.exp(-dt / 0.15)
        self._a_kin += beta * (accel_world - self._a_kin)
        self.vel = self.vel + accel_world * dt
        self.pos = self.pos + self.vel * dt

    def fuse_gnss(self, pos_meas: np.ndarray, vel_meas: np.ndarray, dt: float) -> None:
        """Slower GNSS/RTK correction. Call it whenever a fix lands."""
        ap = 1.0 - np.exp(-self.k_pos * dt)
        av = 1.0 - np.exp(-self.k_vel * dt)
        self.pos += ap * (pos_meas - self.pos)
        self.vel += av * (vel_meas - self.vel)

    @property
    def state(self) -> State:
        return State(self.pos.copy(), self.vel.copy(), self.q.copy(),
                     np.zeros(3))  # caller backfills omega from the gyro if it cares
