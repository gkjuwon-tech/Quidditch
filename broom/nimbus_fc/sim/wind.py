"""Wind plus turbulence.

A steady component plus band-limited gusts. The gusts are an
Ornstein-Uhlenbeck process per axis -- basically the budget version of a
Dryden spectrum. Because the plant drags on airspeed (vel - wind), this shows
up as a genuine force disturbance, which is exactly what leans on position
hold and the estimator.
"""

from __future__ import annotations

import numpy as np


class Wind:
    def __init__(self, steady=(0.0, 0.0, 0.0), gust_sigma: float = 0.0,
                 gust_tau: float = 1.5, seed: int = 0):
        self.steady = np.asarray(steady, dtype=float)
        self.gust_sigma = gust_sigma      # turbulence intensity, m/s (1-sigma)
        self.gust_tau = gust_tau          # gust correlation time, s
        self.rng = np.random.default_rng(seed)
        self._gust = np.zeros(3)

    def sample(self, dt: float) -> np.ndarray:
        if self.gust_sigma > 0.0:
            # one OU step; mean-reverting, steady-state std works out to gust_sigma
            a = dt / max(self.gust_tau, 1e-3)
            noise = self.rng.normal(0.0, 1.0, 3)
            self._gust += -a * self._gust + self.gust_sigma * np.sqrt(2.0 * a) * noise
        return self.steady + self._gust

    @property
    def current(self) -> np.ndarray:
        return self.steady + self._gust
