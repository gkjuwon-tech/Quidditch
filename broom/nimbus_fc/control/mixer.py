"""Allocation: turn [collective, body torque] into a thrust per fan.

Garden-variety multirotor allocation, just generalised to whatever fan
layout the broom happens to carry. The 4xN matrix A maps fan thrusts f onto
the wrench [T, tau_x, tau_y, tau_z]. For fan i at body pos r=(rx,ry,rz),
thrust along +z_body, spin sign k:

    T     += f_i
    tau_x += ry * f_i          # roll, from the lateral lever arm
    tau_y += -rx * f_i         # pitch, from the longitudinal lever arm
    tau_z += k * c_yaw * f_i   # yaw, from reaction torque

Invert with a least-squares pseudo-inverse, clamp to the fans' real thrust
band, then hand back the wrench we *actually* get out so the sim never sees
forces the hardware couldn't make. When we saturate we protect torque over
collective on purpose: dropping a bit of height is survivable, losing
attitude authority is not.
"""

from __future__ import annotations

import numpy as np

from ..core.params import Params


class Mixer:
    def __init__(self, params: Params):
        self.p = params
        layout = params.fan_layout
        rx, ry = layout[:, 0], layout[:, 1]
        spin = layout[:, 3]
        # rows of A are [T, tau_x, tau_y, tau_z]
        self.A = np.vstack([
            np.ones_like(rx),
            ry,
            -rx,
            spin * params.fan_yaw_coeff,
        ])
        self.A_pinv = np.linalg.pinv(self.A)
        self.n = params.num_fans

    def allocate(self, collective: float, torque: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """(fan_thrusts, actual_wrench); the thrusts come back saturated.

        actual_wrench is [T, tau_x, tau_y, tau_z] rebuilt from the clamped
        thrusts, i.e. what the vehicle genuinely puts out this tick.
        """
        wrench = np.array([collective, torque[0], torque[1], torque[2]], dtype=float)
        f = self.A_pinv @ wrench

        fmin, fmax = self.p.fan_thrust_min, self.p.fan_thrust_max
        if f.min() < fmin or f.max() > fmax:
            f = self._desaturate(wrench, f)

        f = np.clip(f, fmin, fmax)
        actual = self.A @ f
        return f, actual

    def _desaturate(self, wrench: np.ndarray, f0: np.ndarray) -> np.ndarray:
        """Keep the torque, give up collective when the fans can't do both.

        Cheap and robust: solve the torque-only problem first so we know the
        attitude command survives, then dump on as much uniform collective as
        the leftover headroom allows. Same instinct as Betaflight airmode --
        protect attitude authority when things saturate.
        """
        fmin, fmax = self.p.fan_thrust_min, self.p.fan_thrust_max
        torque_wrench = wrench.copy()
        torque_wrench[0] = 0.0
        f_tau = self.A_pinv @ torque_wrench

        # how much uniform collective we can stack on the torque solution
        f_tau_c = np.clip(f_tau, fmin, fmax)
        up = float(np.min(fmax - f_tau_c))      # room to push up everywhere
        down = float(np.min(f_tau_c - fmin))    # room to pull down
        desired_c = wrench[0] / self.n          # each fan's share of collective
        offset = float(np.clip(desired_c, -down, up))
        return f_tau + offset
