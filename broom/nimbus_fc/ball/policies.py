"""Simple player policies (AI) used to drive scenarios and stress the balls."""

from __future__ import annotations

import numpy as np


def seek_ball(ball, lead: float = 0.25):
    """lead-pursuit: chase a ball, aiming where it will be, at full speed."""
    def policy(world, pl):
        target = ball.body.pos + ball.body.vel * lead
        d = target - pl.pos
        n = float(np.linalg.norm(d))
        if n < 1e-6:
            return np.zeros(3)
        return d / n * pl.max_speed
    return policy


def hold(position):
    pos = np.asarray(position, dtype=float)

    def policy(world, pl):
        return (pos - pl.pos) * 1.5
    return policy
