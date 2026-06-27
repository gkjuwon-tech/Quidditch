"""Wind & turbulence model.

Steady wind plus band-limited gusts (an Ornstein-Uhlenbeck process per axis --
the cheap cousin of the Dryden turbulence spectrum). the plant applies drag to
AIRSPEED (vel - wind), so wind is a real force disturbance the controller has to
reject -- exactly what stresses position hold and the estimator.
"""

from __future__ import annotations

import numpy as np


class Wind:
    def __init__(self, steady=(0.0, 0.0, 0.0), gust_sigma: float = 0.0,
                 gust_tau: float = 1.5, seed: int = 0):
        self.steady = np.asarray(steady, dtype=float)
        self.gust_sigma = gust_sigma      # m/s, turbulence intensity (std)
        self.gust_tau = gust_tau          # s, gust correlation time
        self.rng = np.random.default_rng(seed)
        self._gust = np.zeros(3)

    def sample(self, dt: float) -> np.ndarray:
        if self.gust_sigma > 0.0:
            # OU update: mean-reverting, stationary std = gust_sigma
            a = dt / max(self.gust_tau, 1e-3)
            noise = self.rng.normal(0.0, 1.0, 3)
            self._gust += -a * self._gust + self.gust_sigma * np.sqrt(2.0 * a) * noise
        return self.steady + self._gust

    @property
    def current(self) -> np.ndarray:
        return self.steady + self._gust
