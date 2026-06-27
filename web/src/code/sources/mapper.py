"""Fly-by-intent: turn normalized rider inputs into safe control setpoints.

The contract that makes the broom "impossible to crash by being bad at flying":

  * Sticks centered  -> latch and HOLD current position + altitude + heading.
                        Let go and the broom just parks in the air.
  * Stick deflected  -> command a VELOCITY (capped to the envelope), not a
                        raw tilt. Push twice as hard, you do not go twice as
                        crazy -- you ask for at most max_speed.
  * Heading          -> yaw stick commands a yaw RATE; release holds heading.

Position hold is encoded per-axis: a NaN in the setpoint position means
"velocity mode on that axis", so the rider can hold a lateral spot while
climbing. POSITION mode holds laterally on release; ALTITUDE mode lets the
vehicle coast horizontally (and only holds height) for a looser, windier feel.
"""

from __future__ import annotations

import numpy as np

from ..core import math3d as m
from ..core.params import Params
from ..core.types import FlightMode, RiderIntent, Setpoint, State

_DEADBAND = 0.05


class IntentMapper:
    def __init__(self, params: Params):
        self.p = params
        self.hold_xy: np.ndarray | None = None
        self.hold_z: float | None = None
        self.hold_yaw: float | None = None

    def reset(self, state: State) -> None:
        """Latch holds to the current state (call when handing control to the rider)."""
        self.hold_xy = state.pos[:2].copy()
        self.hold_z = float(state.pos[2])
        self.hold_yaw = m.yaw_of(state.quat)

    # ------------------------------------------------------------------ #
    def update(self, intent: RiderIntent, state: State, dt: float,
               mode: FlightMode = FlightMode.POSITION) -> Setpoint:
        p = self.p
        intent = intent.clamped()
        if self.hold_yaw is None:
            self.reset(state)

        # --- heading: yaw stick -> yaw rate, release holds heading ------
        yaw_rate = intent.yaw * p.max_yaw_rate
        self.hold_yaw = _wrap(self.hold_yaw + yaw_rate * dt)

        pos = np.array([np.nan, np.nan, np.nan])
        vel_ff = np.zeros(3)

        # --- horizontal -------------------------------------------------
        if abs(intent.pitch) > _DEADBAND or abs(intent.roll) > _DEADBAND:
            # Velocity mode: rider frame -> world via current heading.
            fwd = intent.pitch * p.max_speed_xy        # +x_body
            right = intent.roll * p.max_speed_xy        # +right = -y_body
            yaw = m.yaw_of(state.quat)
            c, s = np.cos(yaw), np.sin(yaw)
            vel_ff[0] = c * fwd + s * right
            vel_ff[1] = s * fwd - c * right
            vel_ff[:2] = m.clamp_norm(vel_ff[:2], p.max_speed_xy)
            self.hold_xy = None
        elif mode == FlightMode.POSITION:
            if self.hold_xy is None:
                self.hold_xy = state.pos[:2].copy()
            pos[0], pos[1] = self.hold_xy
        else:  # ALTITUDE mode: no lateral hold, coast to a stop on drag
            self.hold_xy = None

        # --- vertical ---------------------------------------------------
        if abs(intent.lift) > _DEADBAND:
            rate = (intent.lift * p.max_climb_rate if intent.lift > 0
                    else intent.lift * p.max_descent_rate)
            vel_ff[2] = rate
            self.hold_z = None
        else:
            if self.hold_z is None:
                self.hold_z = float(state.pos[2])
            pos[2] = self.hold_z

        return Setpoint(pos=pos, vel_ff=vel_ff, yaw=self.hold_yaw,
                        yaw_rate_ff=yaw_rate)


def _wrap(a: float) -> float:
    """Wrap angle to [-pi, pi]."""
    return float((a + np.pi) % (2 * np.pi) - np.pi)
