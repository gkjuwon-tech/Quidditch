"""State estimator: Mahony attitude filter + alpha-beta position/velocity INS.

Two loosely-coupled estimators -- plenty for a low-dynamics manned vehicle and
a lot easier to trust than a hand-rolled EKF:

  attitude (Mahony complementary filter):
    - integrate bias-corrected gyro for the fast component
    - correct tilt from the accelerometer as a gravity reference (slow)
    - estimate gyro bias online via the integral term

  position/velocity (INS + GNSS complementary, "alpha-beta"):
    - dead-reckon with the accelerometer (rotated to world, gravity removed)
    - pull pos/vel back toward GNSS/RTK with fixed gains

Kept dependency-free; conceptually close to the Crazyflie complementary
estimator and PX4's `Q` attitude estimator.
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
        self._a_kin = np.zeros(3)   # low-passed world kinematic acceleration

        # Mahony gains
        self.kp_mahony = 2.0
        self.ki_mahony = 0.08
        # GNSS fusion gains (per second); applied as 1-exp on update. strong
        # velocity fusion keeps the velocity estimate tight, which the position
        # controller's damping term leans on (loose velocity => lagged damping
        # => overshoot when flying on the estimate).
        self.k_pos = 8.0
        self.k_vel = 10.0

    def predict(self, gyro: np.ndarray, accel_body: np.ndarray, dt: float) -> None:
        """high-rate prediction from IMU (call every inner loop)."""
        # attitude: mahony correction with maneuver-compensated gravity.
        # the accel reads specific force = a_world - g. to get a clean gravity
        # reference even while accelerating, subtract the known kinematic accel
        # (from the velocity estimate, low-passed):
        #     gravity_body = accel_body - R^T * a_kin_world
        # this kills the dominant Mahony failure mode (attitude corrupted by
        # hard maneuvers) without throwing the accel away.
        grav_ref_body = accel_body - m.quat_rotate_inv(self.q, self._a_kin)
        g_est_body = m.quat_rotate_inv(self.q, np.array([0.0, 0.0, 1.0]))
        n = float(np.linalg.norm(grav_ref_body))
        corr = np.zeros(3)
        if n > 1e-3:
            # down-weight if the recovered gravity magnitude is implausible
            trust = np.exp(-abs(n - m.GRAVITY) / 3.0)
            corr = trust * np.cross(grav_ref_body / n, g_est_body)
            self.gyro_bias += -self.ki_mahony * corr * dt
        omega = gyro - self.gyro_bias + self.kp_mahony * corr
        self.q = m.quat_integrate(self.q, omega, dt)

        # position/velocity: dead-reckon with specific force
        accel_world = m.quat_rotate(self.q, accel_body) + np.array([0, 0, -m.GRAVITY])
        # track kinematic accel (low-pass) for next step's gravity comp
        beta = 1.0 - np.exp(-dt / 0.15)
        self._a_kin += beta * (accel_world - self._a_kin)
        self.vel = self.vel + accel_world * dt
        self.pos = self.pos + self.vel * dt

    def fuse_gnss(self, pos_meas: np.ndarray, vel_meas: np.ndarray, dt: float) -> None:
        """lower-rate correction from GNSS/RTK (call when a fix arrives)."""
        ap = 1.0 - np.exp(-self.k_pos * dt)
        av = 1.0 - np.exp(-self.k_vel * dt)
        self.pos += ap * (pos_meas - self.pos)
        self.vel += av * (vel_meas - self.vel)

    @property
    def state(self) -> State:
        return State(self.pos.copy(), self.vel.copy(), self.q.copy(),
                     np.zeros(3))  # omega filled by caller from gyro if needed
