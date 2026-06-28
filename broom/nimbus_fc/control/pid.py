"""A vectorised PID. Anti-windup + derivative-on-measurement.

A few deliberate choices, same ones Betaflight and PX4 land on:
  * D is on the measurement, not the error, so a setpoint step doesn't
    produce a derivative kick.
  * the integrator clamps, and the caller freezes it (freeze_i) whenever the
    output saturates -- cheap back-calculation.
  * everything is element-wise on arrays, so the one class does scalar, xy
    and full 3-axis without fuss.
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
        # we don't know the signal width until the first update(), so the
        # integrator allocates itself lazily. lets scalar gains drive a 2- or
        # 3-vector interchangeably.
        self._i = None
        self._prev_meas = None

    def reset(self) -> None:
        self._i = None
        self._prev_meas = None

    def update(self, setpoint, measurement, dt: float, freeze_i: bool = False):
        sp = np.atleast_1d(np.asarray(setpoint, dtype=float))
        meas = np.atleast_1d(np.asarray(measurement, dtype=float))
        err = sp - meas
        if self._i is None:
            self._i = np.zeros_like(err)

        if not freeze_i:
            self._i += self.ki * err * dt
            self._i = np.clip(self._i, -self.i_limit, self.i_limit)

        # first call has no previous sample, so D contributes nothing
        if self._prev_meas is None:
            d_meas = np.zeros_like(meas)
        else:
            d_meas = (meas - self._prev_meas) / dt
        self._prev_meas = meas.copy()

        out = self.kp * err + self._i - self.kd * d_meas
        if self.out_limit is not None:
            out = np.clip(out, -self.out_limit, self.out_limit)
        return out

    @property
    def integral(self) -> np.ndarray:
        return np.zeros(1) if self._i is None else self._i.copy()
