"""Flying agents: the balls and the players, as acceleration-limited masses.

`BallBody` tracks a commanded velocity with a first-order response, capped by
the ball's acceleration and speed envelope -- a faithful stand-in for a small
agile drone whose inner loop (the broom cascade) realises the demanded accel.

`Player` is a kinematic human-on-a-broom: a position, a velocity, a top speed,
and a `reach` (how far a hand/bat extends). Players are what the balls must
never physically touch.
"""

from __future__ import annotations

import numpy as np

from ..core import math3d as m
from .params import BallParams


class BallBody:
    def __init__(self, params: BallParams, pos: np.ndarray):
        self.p = params
        self.pos = np.asarray(pos, dtype=float).copy()
        self.vel = np.zeros(3)

    def step(self, vel_cmd: np.ndarray, dt: float) -> None:
        p = self.p
        vel_cmd = m.clamp_norm(np.asarray(vel_cmd, dtype=float), p.max_speed)
        desired_acc = (vel_cmd - self.vel) / p.vel_tau
        acc = m.clamp_norm(desired_acc, p.max_accel)
        self.vel = m.clamp_norm(self.vel + acc * dt, p.max_speed)
        self.pos = self.pos + self.vel * dt

    @property
    def speed(self) -> float:
        return float(np.linalg.norm(self.vel))


class Player:
    """A kinematic player. `reach` is the hand/bat extension from the body."""

    def __init__(self, pid: int, pos, max_speed: float = 14.0,
                 reach: float = 0.9, body_radius: float = 0.35):
        self.id = pid
        self.pos = np.asarray(pos, dtype=float).copy()
        self.vel = np.zeros(3)
        self.max_speed = max_speed
        self.reach = reach
        self.body_radius = body_radius
        self.vel_tau = 0.18          # players are heavier/slower to respond
        self.max_accel = 12.0

    def step(self, vel_cmd: np.ndarray, dt: float) -> None:
        vel_cmd = m.clamp_norm(np.asarray(vel_cmd, dtype=float), self.max_speed)
        acc = m.clamp_norm((vel_cmd - self.vel) / self.vel_tau, self.max_accel)
        self.vel = m.clamp_norm(self.vel + acc * dt, self.max_speed)
        self.pos = self.pos + self.vel * dt

    def hand_toward(self, target: np.ndarray) -> np.ndarray:
        """Position of the outstretched hand reaching toward `target`."""
        d = np.asarray(target, dtype=float) - self.pos
        n = float(np.linalg.norm(d))
        if n < 1e-6:
            return self.pos.copy()
        return self.pos + (d / n) * self.reach
