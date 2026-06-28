"""The flying agents -- balls and players -- as accel-limited point masses.

BallBody chases a commanded velocity with a first-order response, clamped to
the ball's accel and speed envelope. It's a fair stand-in for a small agile
drone whose inner loop (the broom cascade) actually delivers the accel.

Player is a kinematic human-on-a-broom: position, velocity, a top speed, and a
reach (how far the hand/bat sticks out). Players are the thing the balls are
never allowed to physically touch.
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
    """A kinematic player. `reach` is how far the hand/bat extends past the body."""

    def __init__(self, pid: int, pos, max_speed: float = 14.0,
                 reach: float = 0.9, body_radius: float = 0.35):
        self.id = pid
        self.pos = np.asarray(pos, dtype=float).copy()
        self.vel = np.zeros(3)
        self.max_speed = max_speed
        self.reach = reach
        self.body_radius = body_radius
        self.vel_tau = 0.18          # heavier than a ball, so slower to react
        self.max_accel = 12.0
        self.tagged_out = False
        self._penalty_until = 0.0

    def penalise(self, until: float) -> None:
        self.tagged_out = True
        self._penalty_until = until

    def step(self, vel_cmd: np.ndarray, dt: float) -> None:
        vel_cmd = m.clamp_norm(np.asarray(vel_cmd, dtype=float), self.max_speed)
        acc = m.clamp_norm((vel_cmd - self.vel) / self.vel_tau, self.max_accel)
        self.vel = m.clamp_norm(self.vel + acc * dt, self.max_speed)
        self.pos = self.pos + self.vel * dt

    def act(self, world, dt: float, vel_override=None) -> None:
        """One World tick for a kinematic player."""
        if self.tagged_out and world.t < self._penalty_until:
            self.step(np.array([0.0, 0.0, -0.3]), dt)   # serving a penalty: just drift
            return
        self.tagged_out = False
        if vel_override is not None:
            vel_cmd = vel_override
        elif getattr(self, "policy", None) is not None:
            vel_cmd = self.policy(world, self)
        else:
            vel_cmd = np.zeros(3)
        self.step(vel_cmd, dt)

    def hand_toward(self, target: np.ndarray) -> np.ndarray:
        """Where the hand ends up when it reaches toward `target`."""
        d = np.asarray(target, dtype=float) - self.pos
        n = float(np.linalg.norm(d))
        if n < 1e-6:
            return self.pos.copy()
        return self.pos + (d / n) * self.reach
