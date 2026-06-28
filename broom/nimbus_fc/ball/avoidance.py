"""The one rule that never bends: a ball does not drive into a person.

This is the most important safety layer in the ball stack. It sits between
every ball's guidance and its actual motion, and it's the same code for the
gentle Quaffle and the nasty Bludger. Guidance is allowed to *want* to get
close; the commanded velocity then gets clamped so the padded shell brakes to
a stop at the safety distance from anyone -- the exact stopping-distance trick
that keeps the broom inside the pitch, just pointed at people instead.

If someone rams the ball, the ball backs off on its own. That's why a Bludger
"hit" is a proximity tag at ~1 m and never a 0 m collision: we delete the
physics of contact and keep only the *call* that a hit happened.
"""

from __future__ import annotations

import numpy as np

from ..core import math3d as m
from .body import BallBody, Player


class NoContactAvoidance:
    def __init__(self, buffer: float = 0.30, brake_frac: float = 0.35):
        self.buffer = buffer
        self.brake_frac = brake_frac

    def constrain(self, body: BallBody, players: list[Player],
                  vel_cmd: np.ndarray) -> np.ndarray:
        out = np.asarray(vel_cmd, dtype=float).copy()
        a_brake = self.brake_frac * body.p.max_accel
        for pl in players:
            d_vec = body.pos - pl.pos
            dist = float(np.linalg.norm(d_vec))
            min_sep = body.p.safety_radius + pl.body_radius + self.buffer
            if dist < 1e-6:
                out += np.array([0.0, 0.0, 1.0]) * body.p.max_speed
                continue
            n = d_vec / dist                       # points away from the person
            gap = dist - min_sep
            # the gap closes at (player approach speed - ball outward speed).
            # hold that under the stopping-distance limit, and fold in the
            # PERSON's velocity too so a charging player gets a pre-emptive
            # retreat instead of a late one. the ball is quicker, so it wins.
            v_allow = np.sqrt(2.0 * a_brake * max(gap, 0.0))
            player_approach = float(np.dot(pl.vel, n))   # >0 means closing on the ball
            needed_out = player_approach - v_allow       # outward speed the ball needs
            if gap < 0.0:                                # already too close -> bail hard
                needed_out = max(needed_out, body.p.max_speed)
            cur_out = float(np.dot(out, n))
            if cur_out < needed_out:
                out += (needed_out - cur_out) * n
        return out

    @staticmethod
    def min_separation(body: BallBody, players: list[Player]) -> float:
        """Shell-to-body clearance to the nearest person right now (<0 means contact)."""
        if not players:
            return np.inf
        return min(
            float(np.linalg.norm(body.pos - pl.pos)) - body.p.safety_radius - pl.body_radius
            for pl in players
        )

    @staticmethod
    def closing_speed(body: BallBody, players: list[Player]) -> float:
        """Closing speed along the line to the nearest person -- the impact speed
        if they were touching. Keep it low and any graze is gentle by design."""
        if not players:
            return 0.0
        pl = min(players, key=lambda p: float(np.linalg.norm(body.pos - p.pos)))
        d = body.pos - pl.pos
        n = float(np.linalg.norm(d))
        if n < 1e-9:
            return 0.0
        return abs(float(np.dot(body.vel - pl.vel, d / n)))
