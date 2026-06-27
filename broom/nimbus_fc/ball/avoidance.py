"""The unbreakable rule: a ball never drives into a person.

This is the single most important safety layer in the whole ball stack. it sits
between every ball's guidance and its motion, and it's identical for the gentle
Quaffle and the aggressive Bludger: guidance may *want* to get close, but the
ball's commanded velocity is clamped so its padded shell decelerates to a stop
at the safety distance from any person -- the same stopping-distance profile
that holds the broom inside the pitch, here applied to people.

If a person rams the ball anyway, the ball actively retreats. the Bludger's
"hit" is therefore a proximity tag at ~1 m, never a 0 m collision: the physics
of contact is removed and only the *judgement* of a hit remains.
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
            n = d_vec / dist                       # unit vector AWAY from person
            gap = dist - min_sep
            # gap closes at: player's approach speed minus the ball's outward
            # speed. keep that below the stopping-distance limit, accounting for
            # the PERSON's motion (so a charging player triggers a pre-emptive
            # retreat, not a too-late reaction). the ball is faster, so it wins.
            v_allow = np.sqrt(2.0 * a_brake * max(gap, 0.0))
            player_approach = float(np.dot(pl.vel, n))   # >0: moving toward ball
            needed_out = player_approach - v_allow       # required ball outward vel
            if gap < 0.0:                                # already inside -> hard escape
                needed_out = max(needed_out, body.p.max_speed)
            cur_out = float(np.dot(out, n))
            if cur_out < needed_out:
                out += (needed_out - cur_out) * n
        return out

    @staticmethod
    def min_separation(body: BallBody, players: list[Player]) -> float:
        """current shell-to-body clearance to the nearest person (neg = touch)."""
        if not players:
            return np.inf
        return min(
            float(np.linalg.norm(body.pos - pl.pos)) - body.p.safety_radius - pl.body_radius
            for pl in players
        )

    @staticmethod
    def closing_speed(body: BallBody, players: list[Player]) -> float:
        """relative speed along the line to the nearest person (impact speed if
        they were touching). low closing speed => a graze is gentle by design."""
        if not players:
            return 0.0
        pl = min(players, key=lambda p: float(np.linalg.norm(body.pos - p.pos)))
        d = body.pos - pl.pos
        n = float(np.linalg.norm(d))
        if n < 1e-9:
            return 0.0
        return abs(float(np.dot(body.vel - pl.vel, d / n)))
