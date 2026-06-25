"""Multi-agent arena: players + balls inside the pitch, advanced together.

The World owns the pitch bounds, steps every agent, runs each ball's guidance
(behaviour) through the shared no-contact avoidance layer, and records events
(captures, tags, scores) and telemetry. It is the closest thing here to the
fictional central referee -- it sees everyone and enforces the safety rule that
a ball never physically touches a person.
"""

from __future__ import annotations

import numpy as np

from ..core import math3d as m
from .avoidance import NoContactAvoidance
from .body import BallBody, Player


class Ball:
    """A ball = a flying body + a guidance behaviour + live status."""

    def __init__(self, body: BallBody, behavior):
        self.body = body
        self.behavior = behavior
        self.name = body.p.name
        self.active = True          # a caught/parked ball goes inactive
        self.events: list[str] = []


class World:
    def __init__(self, pitch_lo=(-50.0, -25.0, 1.0), pitch_hi=(50.0, 25.0, 18.0)):
        self.lo = np.asarray(pitch_lo, dtype=float)
        self.hi = np.asarray(pitch_hi, dtype=float)
        self.players: list[Player] = []
        self.balls: list[Ball] = []
        self.avoid = NoContactAvoidance()
        self.t = 0.0
        self.events: list[tuple[float, str]] = []
        # Scoring hoops: list of (center[3], ring_radius). Set by the scenario.
        self.hoops: list[tuple[np.ndarray, float]] = []
        self.score = 0
        self.referee = None          # optional Dementor; arbitrates + judges

    # ------------------------------------------------------------------ #
    def add_player(self, player: Player, policy=None) -> Player:
        player.policy = policy
        self.players.append(player)
        return player

    def add_ball(self, body: BallBody, behavior) -> Ball:
        b = Ball(body, behavior)
        self.balls.append(b)
        return b

    def log_event(self, msg: str) -> None:
        self.events.append((self.t, msg))

    # ------------------------------------------------------------------ #
    def step(self, dt: float) -> None:
        # players move first (they react to the previous tick's world).
        # An agent may be a kinematic Player or a real broom-flown BroomAgent;
        # both expose .act(world, dt).
        for pl in self.players:
            override = self.referee.override_for(self, pl) if self.referee else None
            pl.act(self, dt, vel_override=override)
            self._clamp_agent(pl)

        # then balls: guidance -> no-contact avoidance -> bounds -> integrate
        for ball in self.balls:
            if not ball.active:
                continue
            vel_cmd = ball.behavior.update(self, ball, dt)
            vel_cmd = self.avoid.constrain(ball.body, self.players, vel_cmd)
            vel_cmd = self._bound_velocity(ball.body.pos, vel_cmd)
            ball.body.step(vel_cmd, dt)
            self._clamp_ball(ball.body)

        self.t += dt
        if self.referee is not None:
            self.referee.judge(self, dt)

    # ------------------------------------------------------------------ #
    def _bound_velocity(self, pos: np.ndarray, vel_cmd: np.ndarray) -> np.ndarray:
        """Ramp outward velocity to zero near a wall (soft keep-in)."""
        out = vel_cmd.copy()
        margin = 2.0
        for k in range(3):
            if pos[k] > self.hi[k] - margin and out[k] > 0:
                out[k] *= max(0.0, (self.hi[k] - pos[k]) / margin)
            if pos[k] < self.lo[k] + margin and out[k] < 0:
                out[k] *= max(0.0, (pos[k] - self.lo[k]) / margin)
        return out

    def _clamp_ball(self, body: BallBody) -> None:
        for k in range(3):
            if body.pos[k] < self.lo[k]:
                body.pos[k] = self.lo[k]
                body.vel[k] = max(0.0, body.vel[k])
            elif body.pos[k] > self.hi[k]:
                body.pos[k] = self.hi[k]
                body.vel[k] = min(0.0, body.vel[k])

    def _clamp_agent(self, pl: Player) -> None:
        for k in range(3):
            pl.pos[k] = float(np.clip(pl.pos[k], self.lo[k], self.hi[k]))

    # ------------------------------------------------------------------ #
    def nearest_player(self, pos: np.ndarray):
        if not self.players:
            return None, np.inf
        ds = [(pl, float(np.linalg.norm(pl.pos - pos))) for pl in self.players]
        return min(ds, key=lambda x: x[1])
