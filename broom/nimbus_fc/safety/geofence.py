"""The 3D geofence: a keep-in box and what to do at its edges.

It works at the setpoint level, which keeps it cleanly separate from the
controller. The pitch is an axis-aligned box, so the fence is per world axis,
which is both dead simple and very hard to fool:

  * any position-hold target gets clamped into the keep-in box.
  * per axis, predict where we'd coast to a stop using the brake-accel the
    position controller can actually deliver. if that stop point is outside
    the box, swap the rider's velocity command on that axis for a position
    hold on the boundary. the controller's stopping-distance profile (which
    we know brakes inside budget) then takes over, and since the held target
    sits *inside* the wall, any leftover overshoot gets pulled back. net
    result: the broom physically can't park outside the box.

Doing it per axis keeps tangential motion alive, so you can still skim a wall.
It's ArduPilot's fence idea, narrowed to a rectangular pitch.
"""

from __future__ import annotations

import numpy as np

from ..core.params import Params
from ..core.types import Setpoint, State


class Geofence:
    def __init__(self, params: Params, keep_in: float = 8.0):
        self.p = params
        self.keep_in = keep_in
        poly = params.fence_polygon
        # keep-in box = pitch bounding box pulled in by keep_in on each side
        self.lo = np.array([poly[:, 0].min() + keep_in, poly[:, 1].min() + keep_in,
                            params.fence_floor])
        self.hi = np.array([poly[:, 0].max() - keep_in, poly[:, 1].max() - keep_in,
                            params.fence_ceiling])
        # deliberately conservative brake accel, so we start braking early
        self.a_brake = 0.5 * params.max_accel_xy

    def apply(self, state: State, sp: Setpoint,
              allow_ground: bool = False) -> tuple[Setpoint, bool]:
        pos, vel = state.pos, state.vel
        breaching = False
        # the in-flight floor has to drop away during landing / emergency
        # descent, otherwise we could never actually touch down
        lo = self.lo.copy()
        if allow_ground:
            lo[2] = 0.0

        # pull any explicit hold target into the box first
        if sp.pos is not None:
            for k in range(3):
                if np.isfinite(sp.pos[k]):
                    sp.pos[k] = float(np.clip(sp.pos[k], lo[k], self.hi[k]))

        for k in range(3):
            v = vel[k]
            brake_dist = v * abs(v) / (2.0 * self.a_brake)   # signed stopping distance
            stop = pos[k] + brake_dist
            if stop > self.hi[k]:                            # heading out the top
                self._hold_axis(sp, k, self.hi[k], outward_sign=+1.0)
                breaching = breaching or pos[k] > self.hi[k]
            elif stop < lo[k]:                               # heading out the bottom
                self._hold_axis(sp, k, lo[k], outward_sign=-1.0)
                breaching = breaching or pos[k] < lo[k]
        return sp, breaching

    @staticmethod
    def _hold_axis(sp: Setpoint, k: int, bound: float, outward_sign: float) -> None:
        """Pin this axis to a hold on the boundary and zero out any outward vel."""
        if sp.pos is None:
            sp.pos = np.array([np.nan, np.nan, np.nan])
        sp.pos[k] = bound
        # inward feedforward is fine; outward is exactly what we're stopping
        if outward_sign > 0:
            sp.vel_ff[k] = min(sp.vel_ff[k], 0.0)
        else:
            sp.vel_ff[k] = max(sp.vel_ff[k], 0.0)

    def contains(self, pos: np.ndarray, slack: float = 0.5) -> bool:
        """Inside the hard wall? (keep-in box grown back out by keep_in + slack)."""
        lo = self.lo - self.keep_in - slack
        hi = self.hi + self.keep_in + slack
        return bool(np.all(pos >= lo) and np.all(pos <= hi))
