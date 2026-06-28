"""Rider brains for broom-flown players: world state -> desired world velocity.

These answer "what do I want to do". BroomAgent takes that velocity, converts
it to stick intent, and lets the real flight stack go fly it.
"""

from __future__ import annotations

import numpy as np


def chase_ball(ball, lead: float = 0.3, gain: float = 1.2):
    """Seeker: head for where the ball is about to be."""
    def ai(world, me):
        if not ball.active:
            return np.zeros(3)
        target = ball.body.pos + ball.body.vel * lead
        return (target - me.pos) * gain
    return ai


def patrol(center, radius: float = 16.0, height: float = 9.0,
           omega: float = 0.4, gain: float = 1.0):
    """Just fly a steady loop around the pitch."""
    c = np.asarray(center, float)

    def ai(world, me):
        ang = np.arctan2(me.pos[1] - c[1], me.pos[0] - c[0]) + omega
        tgt = c + radius * np.array([np.cos(ang), np.sin(ang), 0.0])
        tgt[2] = height
        return (tgt - me.pos) * gain
    return ai


def guard_hoops(hoops, ball, gain: float = 1.2):
    """Keeper: park between the quaffle and the hoops it's threatening."""
    centers = np.array([h[0] for h in hoops])
    mid = centers.mean(axis=0)

    def ai(world, me):
        spot = 0.6 * mid + 0.4 * ball.body.pos
        return (spot - me.pos) * gain
    return ai
