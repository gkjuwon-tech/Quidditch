"""Control allocation: map [collective thrust, body torque] -> per-fan thrust.

Standard multirotor allocation, generalized to the broom's arbitrary fan
layout. The allocation matrix A (4 x N) maps fan thrusts f to the wrench
[T, tau_x, tau_y, tau_z]:

    fan i at body position r=(rx,ry,rz), thrust along +z_body, spin sign k:
        T      += f_i
        tau_x  += ry * f_i          (offset lever arm, roll)
        tau_y  += -rx * f_i         (offset lever arm, pitch)
        tau_z  += k * c_yaw * f_i   (reaction torque, yaw)

We invert with a pseudo-inverse (least-squares), then saturate to the fans'
physical thrust band and re-report the *actual* wrench so the rest of the
sim sees the real, post-saturation forces. Saturation handling biases toward
preserving attitude torque over collective thrust -- losing height is
recoverable, losing attitude is how people die.
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
        # Allocation matrix A: rows = [T, tau_x, tau_y, tau_z]
        self.A = np.vstack([
            np.ones_like(rx),
            ry,
            -rx,
            spin * params.fan_yaw_coeff,
        ])
        self.A_pinv = np.linalg.pinv(self.A)
        self.n = params.num_fans

    def allocate(self, collective: float, torque: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Return (fan_thrusts, actual_wrench) with fan_thrusts saturated.

        actual_wrench = [T, tau_x, tau_y, tau_z] reconstructed from the
        clamped fan thrusts -- this is what the vehicle truly produces.
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
        """Prioritize torque, sacrifice collective if the fans can't do both.

        Strategy (cheap, robust): solve for torque-only first to know the
        attitude command is honored, then add as much uniform collective as
        the remaining headroom allows. Mirrors Betaflight's "airmode" idea
        of protecting attitude authority under saturation.
        """
        fmin, fmax = self.p.fan_thrust_min, self.p.fan_thrust_max
        torque_wrench = wrench.copy()
        torque_wrench[0] = 0.0
        f_tau = self.A_pinv @ torque_wrench

        # Headroom for a uniform collective offset on top of the torque solution.
        f_tau_c = np.clip(f_tau, fmin, fmax)
        up = float(np.min(fmax - f_tau_c))      # how much we can add everywhere
        down = float(np.min(f_tau_c - fmin))    # how much we can subtract
        desired_c = wrench[0] / self.n          # per-fan collective share
        offset = float(np.clip(desired_c, -down, up))
        return f_tau + offset
