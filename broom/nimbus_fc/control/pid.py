"""Vector PID: anti-windup + derivative-on-measurement.

- derivative taken on the measurement, not the error, so a setpoint step
  doesn't kick the D term.
- integral uses clamping anti-windup; the caller freezes it (`freeze_i`) when
  the output is saturated (back-calc is handled upstream).
- operates element-wise on ndarrays so one class covers 1- and 3-axis loops.
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
        # integral / prev-measurement sized lazily on first update, so the same
        # class works for scalar gains over a 2-vector (xy) or a 3-vector.
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
