"""3D geofence: pitch keep-in volume + boundary handling.

Acts at the setpoint level (clean separation from the controller). the pitch is
an axis-aligned box, so the fence works per world axis -- simple and
bulletproof:

  * any position-hold target is clamped into the keep-in box.
  * for each axis, predict where the vehicle would COAST to a stop using the
    same brake-accel the position controller can deliver. if that stop point
    lies outside the box, replace the rider's velocity command on that axis
    with a position-hold at the boundary. the position controller's
    stopping-distance profile (proven to brake within budget) then does the
    work -- and because the held target is *inside* the wall, any residual
    overshoot is actively pulled back. the broom physically cannot park outside
    the box.

per-axis action preserves tangential motion: you can still skim along a wall.
modeled on ArduPilot's fence, specialized to a rectangular pitch.
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
        # axis-aligned keep-in box from the pitch bbox, shrunk by keep_in
        self.lo = np.array([poly[:, 0].min() + keep_in, poly[:, 1].min() + keep_in,
                            params.fence_floor])
        self.hi = np.array([poly[:, 0].max() - keep_in, poly[:, 1].max() - keep_in,
                            params.fence_ceiling])
        # conservative brake accel for stop prediction (brake early)
        self.a_brake = 0.5 * params.max_accel_xy

    def apply(self, state: State, sp: Setpoint,
              allow_ground: bool = False) -> tuple[Setpoint, bool]:
        pos, vel = state.pos, state.vel
        breaching = False
        # during landing / emergency descent the in-flight floor has to yield so
        # the vehicle can actually reach the ground
        lo = self.lo.copy()
        if allow_ground:
            lo[2] = 0.0

        # clamp any explicit position-hold target into the keep-in box
        if sp.pos is not None:
            for k in range(3):
                if np.isfinite(sp.pos[k]):
                    sp.pos[k] = float(np.clip(sp.pos[k], lo[k], self.hi[k]))

        for k in range(3):
            v = vel[k]
            brake_dist = v * abs(v) / (2.0 * self.a_brake)   # signed coast-to-stop
            stop = pos[k] + brake_dist
            if stop > self.hi[k]:                            # would exit high side
                self._hold_axis(sp, k, self.hi[k], outward_sign=+1.0)
                breaching = breaching or pos[k] > self.hi[k]
            elif stop < lo[k]:                               # would exit low side
                self._hold_axis(sp, k, lo[k], outward_sign=-1.0)
                breaching = breaching or pos[k] < lo[k]
        return sp, breaching

    @staticmethod
    def _hold_axis(sp: Setpoint, k: int, bound: float, outward_sign: float) -> None:
        """replace this axis with a position-hold at the boundary; kill outward vel."""
        if sp.pos is None:
            sp.pos = np.array([np.nan, np.nan, np.nan])
        sp.pos[k] = bound
        # allow inward velocity feedforward, never outward
        if outward_sign > 0:
            sp.vel_ff[k] = min(sp.vel_ff[k], 0.0)
        else:
            sp.vel_ff[k] = max(sp.vel_ff[k], 0.0)

    def contains(self, pos: np.ndarray, slack: float = 0.5) -> bool:
        """True if inside the hard wall (keep-in box + keep_in + slack)."""
        lo = self.lo - self.keep_in - slack
        hi = self.hi + self.keep_in + slack
        return bool(np.all(pos >= lo) and np.all(pos <= hi))
