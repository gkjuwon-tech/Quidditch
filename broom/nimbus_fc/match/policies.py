"""Rider-AIs for broom-flown players: world state -> desired WORLD velocity.

These are the 'what do I want to do' brains; BroomAgent turns the desired
velocity into stick intent and lets the flight stack actually fly it.
"""

from __future__ import annotations

import numpy as np


def chase_ball(ball, lead: float = 0.3, gain: float = 1.2):
    """seeker: fly toward where the ball will be."""
    def ai(world, me):
        if not ball.active:
            return np.zeros(3)
        target = ball.body.pos + ball.body.vel * lead
        return (target - me.pos) * gain
    return ai


def patrol(center, radius: float = 16.0, height: float = 9.0,
           omega: float = 0.4, gain: float = 1.0):
    """fly a steady circuit around the pitch."""
    c = np.asarray(center, float)

    def ai(world, me):
        ang = np.arctan2(me.pos[1] - c[1], me.pos[0] - c[0]) + omega
        tgt = c + radius * np.array([np.cos(ang), np.sin(ang), 0.0])
        tgt[2] = height
        return (tgt - me.pos) * gain
    return ai


def guard_hoops(hoops, ball, gain: float = 1.2):
    """keeper: sit between the quaffle and the hoops it threatens."""
    centers = np.array([h[0] for h in hoops])
    mid = centers.mean(axis=0)

    def ai(world, me):
        spot = 0.6 * mid + 0.4 * ball.body.pos
        return (spot - me.pos) * gain
    return ai
