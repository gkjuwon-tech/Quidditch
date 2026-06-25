"""Vector PID with anti-windup and derivative-on-measurement.

Design notes (benchmarked against Betaflight's rate PID and PX4's control
library):
  - Derivative is taken on the *measurement*, not the error, to avoid
    "derivative kick" when the setpoint steps.
  - Integral uses clamping anti-windup, and is frozen when the output is
    saturated (back-calculation handled by the caller via `freeze_i`).
  - Operates element-wise on numpy arrays so one class covers 1- and 3-axis.
"""

from __future__ import annotations

import numpy as np


class PID:
    def __init__(self, kp, ki, kd, i_limit, out_limit=None):
        self.kp = np.atleast_1d(np.asarray(kp, dtype=float))
        self.ki = np.atleast_1d(np.asarray(ki, dtype=float))
        self.kd = np.atleast_1d(np.asarray(kd, dtype=float))
        self.i_limit = np.atleast_1d(np.asarray(i_limit, dtype=float))
        self.out_limit = (None if out_limit is None
                          else np.atleast_1d(np.asarray(out_limit, dtype=float)))
        # Integral is sized lazily to the signal width on first update, so the
        # same class works with scalar gains over a 2-vector (xy) or 3-vector.
        self._i = None
        self._prev_meas = None

    def reset(self) -> None:
        self._i = None
        self._prev_meas = None

    def update(self, setpoint, measurement, dt: float, freeze_i: bool = False):
        sp = np.atleast_1d(np.asarray(setpoint, dtype=float))
        meas = np.atleast_1d(np.asarray(measurement, dtype=float))
        error = sp - meas
        if self._i is None:
            self._i = np.zeros_like(error)

        if not freeze_i:
            self._i += self.ki * error * dt
            self._i = np.clip(self._i, -self.i_limit, self.i_limit)

        if self._prev_meas is None:
            d_meas = np.zeros_like(meas)
        else:
            d_meas = (meas - self._prev_meas) / dt
        self._prev_meas = meas.copy()

        out = self.kp * error + self._i - self.kd * d_meas
        if self.out_limit is not None:
            out = np.clip(out, -self.out_limit, self.out_limit)
        return out

    @property
    def integral(self) -> np.ndarray:
        return np.zeros(1) if self._i is None else self._i.copy()
