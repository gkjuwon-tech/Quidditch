"""Control allocation: [collective thrust, body torque] -> per-fan thrust.

Standard multirotor allocation generalized to the broom's arbitrary fan layout.
The allocation matrix A (4 x N) maps fan thrusts f to the wrench
[T, tau_x, tau_y, tau_z]:

    fan i at body pos r=(rx,ry,rz), thrust along +z_body, spin sign k:
        T     += f_i
        tau_x += ry * f_i          (lever arm, roll)
        tau_y += -rx * f_i         (lever arm, pitch)
        tau_z += k * c_yaw * f_i   (reaction torque, yaw)

Invert with a pseudo-inverse (least squares), saturate to the fans' physical
thrust band, and re-report the *actual* wrench so the sim sees the real
post-saturation forces. Saturation biases toward keeping attitude torque over
collective thrust -- losing height is recoverable, losing attitude is how
people die.
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
        # A rows = [T, tau_x, tau_y, tau_z]
        self.A = np.vstack([
            np.ones_like(rx),
            ry,
            -rx,
            spin * params.fan_yaw_coeff,
        ])
        self.A_pinv = np.linalg.pinv(self.A)
        self.n = params.num_fans

    def allocate(self, collective: float, torque: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """-> (fan_thrusts, actual_wrench) with fan_thrusts saturated.

        actual_wrench = [T, tau_x, tau_y, tau_z] rebuilt from the clamped fan
        thrusts -- i.e. what the vehicle really produces.
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
        """Honor torque first, spend what's left on collective.

        Cheap and robust: solve for torque-only so the attitude command is
        respected, then add as much uniform collective as the remaining
        headroom allows. Same idea as Betaflight's "airmode" -- protect
        attitude authority under saturation.
        """
        fmin, fmax = self.p.fan_thrust_min, self.p.fan_thrust_max
        torque_wrench = wrench.copy()
        torque_wrench[0] = 0.0
        f_tau = self.A_pinv @ torque_wrench

        # headroom for a uniform collective offset on top of the torque solution
        f_tau_c = np.clip(f_tau, fmin, fmax)
        up = float(np.min(fmax - f_tau_c))    # how much we can add everywhere
        down = float(np.min(f_tau_c - fmin))  # how much we can subtract
        desired_c = wrench[0] / self.n         # per-fan collective share
        offset = float(np.clip(desired_c, -down, up))
        return f_tau + offset
