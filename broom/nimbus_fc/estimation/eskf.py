"""15-state Error-State Kalman Filter (ESKF) for the broom.

Nominal state : position(3), velocity(3), attitude quaternion(4),
                gyro bias(3), accel bias(3).
Error state   : dp(3), dv(3), dtheta(3), dbg(3), dba(3)   -> 15-dim.

Global (world-frame) attitude error convention (Sola, "Quaternion kinematics
for the error-state Kalman filter"). High-rate IMU prediction, GNSS/RTK
position+velocity update. This is the upgrade over the complementary filter:
it carries a covariance, estimates accelerometer bias, and stays tight enough
that the controller can fly on the estimate through hard maneuvers AND wind.

Indices: p=0:3, v=3:6, th=6:9, bg=9:12, ba=12:15.
"""

from __future__ import annotations

import numpy as np

from ..core import math3d as m
from ..core.params import Params
from ..core.types import State

P_, V_, TH_, BG_, BA_ = slice(0, 3), slice(3, 6), slice(6, 9), slice(9, 12), slice(12, 15)
_I3 = np.eye(3)


class EKF:
    def __init__(self, params: Params, init: State | None = None):
        self.p = params
        s = init if init is not None else State()
        self.pos = s.pos.copy()
        self.vel = s.vel.copy()
        self.q = s.quat.copy()
        self.bg = np.zeros(3)
        self.ba = np.zeros(3)

        # Covariance and noise (tuned to the synthetic sensor suite).
        self.P = np.diag(np.concatenate([
            0.10 * np.ones(3),   # pos
            0.10 * np.ones(3),   # vel
            np.deg2rad(5.0) ** 2 * np.ones(3),  # attitude
            (0.02 ** 2) * np.ones(3),           # gyro bias
            (0.10 ** 2) * np.ones(3),           # accel bias
        ]))
        self.sigma_a = 0.25       # accel white noise (m/s^2)
        self.sigma_g = 0.03       # gyro white noise (rad/s)
        self.sigma_bg = 1e-4      # gyro bias random walk
        self.sigma_ba = 1e-3      # accel bias random walk
        self.gps_pos_std = 0.10
        self.gps_vel_std = 0.07
        self.accel_dir_std = 0.06   # accelerometer-as-tilt measurement (unit vec)
        self.mag_std = 0.05         # magnetometer direction noise (yaw reference)
        self.mag_world = np.array([0.0, 0.96, -0.28])  # reference field (world ENU)

    @property
    def gyro_bias(self) -> np.ndarray:
        return self.bg.copy()

    @property
    def state(self) -> State:
        return State(self.pos.copy(), self.vel.copy(), self.q.copy(), np.zeros(3))

    def predict(self, gyro: np.ndarray, accel_body: np.ndarray, dt: float) -> None:
        R = m.quat_to_rotmat(self.q)
        a_b = accel_body - self.ba           # corrected specific force (body)
        w_b = gyro - self.bg                 # corrected angular rate (body)
        a_world = R @ a_b + np.array([0.0, 0.0, -m.GRAVITY])

        # Nominal propagation
        self.pos = self.pos + self.vel * dt + 0.5 * a_world * dt * dt
        self.vel = self.vel + a_world * dt
        self.q = m.quat_mul(self.q, m.quat_from_rotvec(w_b * dt))
        self.q = m.quat_normalize(self.q)
        # biases are random-walk: nominal unchanged

        # Error-state transition f = i + a dt
        Ra = R @ a_b
        F = np.eye(15)
        F[P_, V_] = _I3 * dt
        F[V_, TH_] = -m.skew(Ra) * dt
        F[V_, BA_] = -R * dt
        F[TH_, BG_] = -R * dt

        # Process noise q (discrete, diagonal-ish)
        Q = np.zeros((15, 15))
        Q[V_, V_] = (self.sigma_a * dt) ** 2 * _I3
        Q[TH_, TH_] = (self.sigma_g * dt) ** 2 * _I3
        Q[BG_, BG_] = (self.sigma_bg ** 2 * dt) * _I3
        Q[BA_, BA_] = (self.sigma_ba ** 2 * dt) * _I3

        self.P = F @ self.P @ F.T + Q

        # High-rate gravity/tilt fusion keeps attitude observable between GNSS
        # fixes (GNSS pos+vel alone observe tilt only weakly -> drift -> blow-up
        # under gusts). Gated to low specific-force deviation from g, like a
        # real EKF's accelerometer tilt aiding.
        self._fuse_accel_tilt(accel_body - self.ba)

    def _fuse_accel_tilt(self, a_b: np.ndarray) -> None:
        a_norm = float(np.linalg.norm(a_b))
        if a_norm < 1.0:
            return
        trust = np.exp(-abs(a_norm - m.GRAVITY) / 1.5)  # 1 near g, ->0 in maneuvers
        if trust < 0.05:
            return
        R = m.quat_to_rotmat(self.q)
        ez = np.array([0.0, 0.0, 1.0])
        z = a_b / a_norm                     # measured gravity-up (body)
        h = R.T @ ez                         # predicted gravity-up (body)
        H = np.zeros((3, 15))
        H[:, TH_] = R.T @ m.skew(ez)
        Rm = (self.accel_dir_std ** 2 / trust) * _I3
        y = z - h
        S = H @ self.P @ H.T + Rm
        K = self.P @ H.T @ np.linalg.inv(S)
        dx = K @ y
        self.pos += dx[P_]
        self.vel += dx[V_]
        self.q = m.quat_normalize(m.quat_mul(m.quat_from_rotvec(dx[TH_]), self.q))
        self.bg += dx[BG_]
        self.ba += dx[BA_]
        IKH = np.eye(15) - K @ H
        self.P = IKH @ self.P @ IKH.T + K @ Rm @ K.T
        self.P = 0.5 * (self.P + self.P.T)

    def fuse_mag(self, mag_body: np.ndarray) -> None:
        """Magnetometer direction update -> observes yaw (unobservable otherwise)."""
        R = m.quat_to_rotmat(self.q)
        n = float(np.linalg.norm(mag_body))
        if n < 1e-6:
            return
        z = mag_body / n
        h = R.T @ self.mag_world
        H = np.zeros((3, 15))
        H[:, TH_] = R.T @ m.skew(self.mag_world)
        Rm = (self.mag_std ** 2) * _I3
        y = z - h
        S = H @ self.P @ H.T + Rm
        K = self.P @ H.T @ np.linalg.inv(S)
        dx = K @ y
        self.pos += dx[P_]
        self.vel += dx[V_]
        self.q = m.quat_normalize(m.quat_mul(m.quat_from_rotvec(dx[TH_]), self.q))
        self.bg += dx[BG_]
        self.ba += dx[BA_]
        IKH = np.eye(15) - K @ H
        self.P = IKH @ self.P @ IKH.T + K @ Rm @ K.T
        self.P = 0.5 * (self.P + self.P.T)

    def fuse_gnss(self, pos_meas: np.ndarray, vel_meas: np.ndarray, dt: float = 0.0) -> None:
        # Measurement: position + velocity (6-dim).
        H = np.zeros((6, 15))
        H[0:3, P_] = _I3
        H[3:6, V_] = _I3
        Rm = np.diag(np.concatenate([
            self.gps_pos_std ** 2 * np.ones(3),
            self.gps_vel_std ** 2 * np.ones(3),
        ]))
        y = np.concatenate([pos_meas - self.pos, vel_meas - self.vel])
        S = H @ self.P @ H.T + Rm
        K = self.P @ H.T @ np.linalg.inv(S)
        dx = K @ y

        # Inject error into nominal
        self.pos += dx[P_]
        self.vel += dx[V_]
        self.q = m.quat_normalize(m.quat_mul(m.quat_from_rotvec(dx[TH_]), self.q))
        self.bg += dx[BG_]
        self.ba += dx[BA_]

        # Covariance update (joseph form for symmetry/stability)
        IKH = np.eye(15) - K @ H
        self.P = IKH @ self.P @ IKH.T + K @ Rm @ K.T
        self.P = 0.5 * (self.P + self.P.T)
