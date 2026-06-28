"""The 6-DOF rigid-body plant the broom flies against in SITL.

This is "ground truth". It's kept independent of the controller's own mixer on
purpose: the plant carries the real fan->wrench allocation and the real
actuator lag, so any mismatch between the two would show up honestly. They
happen to line up today, which is exactly the knob we'd detune for robustness
testing later.

Semi-implicit Euler at the inner-loop rate. 400 Hz is stable and cheap, and
the quaternion gets first-order integration plus a renormalise each step.
"""

from __future__ import annotations

import numpy as np

from ..core import math3d as m
from ..core.params import Params
from ..core.types import State


def build_allocation(params: Params) -> np.ndarray:
    """Fan geometry -> 4xN matrix from fan thrusts to [T, tau_x, tau_y, tau_z]."""
    layout = params.fan_layout
    rx, ry = layout[:, 0], layout[:, 1]
    spin = layout[:, 3]
    return np.vstack([
        np.ones_like(rx),
        ry,
        -rx,
        spin * params.fan_yaw_coeff,
    ])


class Dynamics:
    def __init__(self, params: Params, state: State | None = None, wind=None):
        self.p = params
        self.A = build_allocation(params)
        self.I = params.inertia_diag.copy()
        self.I_inv = 1.0 / self.I
        self.state = state.copy() if state is not None else State()
        self.wind = wind
        self.wind_world = np.zeros(3)
        # real fan thrust trails the command through a first-order lag
        self.fan_thrust = np.zeros(params.num_fans)
        # keep the last world-frame accel around so the sensors can fake an IMU
        self.accel_world = np.zeros(3)

    def step(self, fan_cmd: np.ndarray, dt: float) -> State:
        p = self.p
        s = self.state

        # first-order actuator lag, exact step toward the command
        alpha = 1.0 - np.exp(-dt / max(p.fan_tau, 1e-6))
        self.fan_thrust += (np.clip(fan_cmd, p.fan_thrust_min, p.fan_thrust_max)
                            - self.fan_thrust) * alpha
        f = self.fan_thrust

        # wrench produced by the *actual* fan thrusts
        wrench = self.A @ f
        T = float(wrench[0])
        torque_fans = wrench[1:]

        # world-frame forces
        thrust_world = m.quat_rotate(s.quat, np.array([0.0, 0.0, T]))
        gravity = np.array([0.0, 0.0, -p.mass * m.GRAVITY])
        # drag bites on airspeed (ground velocity minus wind), not ground speed
        if self.wind is not None:
            self.wind_world = self.wind.sample(dt)
        airspeed_vec = s.vel - self.wind_world
        airspeed = float(np.linalg.norm(airspeed_vec))
        drag = -p.drag_lin * airspeed * airspeed_vec
        accel = (thrust_world + gravity + drag) / p.mass
        self.accel_world = accel

        # body-frame torques (note the gyroscopic term)
        gyro = np.cross(s.omega, self.I * s.omega)
        rot_damp = -p.drag_rot * s.omega
        torque = torque_fans + rot_damp - gyro
        omega_dot = self.I_inv * torque

        # semi-implicit Euler: vel before pos so it stays stable
        s.vel = s.vel + accel * dt
        s.pos = s.pos + s.vel * dt
        s.omega = s.omega + omega_dot * dt
        s.quat = m.quat_integrate(s.quat, s.omega, dt)
        s.t += dt

        self._ground_contact()
        return s

    def _ground_contact(self) -> None:
        """Cheap non-penetrating floor at z=0, with friction once it's resting."""
        s = self.state
        if s.pos[2] < 0.0:
            s.pos[2] = 0.0
            if s.vel[2] < 0.0:
                s.vel[2] = 0.0
            # rub off horizontal speed and help it settle flat
            s.vel[0] *= 0.85
            s.vel[1] *= 0.85
            s.omega *= 0.5

    @property
    def total_thrust(self) -> float:
        return float(np.sum(self.fan_thrust))
