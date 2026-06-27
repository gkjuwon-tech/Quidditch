"""Parameters for the three balls.

A ball is, at the guidance level, an acceleration- and speed-limited flying
agent: the inner attitude/thrust loop that realises a commanded acceleration is
the broom's proven control cascade (nimbus_fc.control). Here we model each ball
as a 2nd-order agent and focus on the part that is genuinely new -- autonomous
guidance, evasion, pursuit, and the no-contact safety guarantee.

Every length is metres, speed m/s, accel m/s^2.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class BallParams:
    name: str
    radius: float            # physical radius of the padded shell
    mass: float
    max_speed: float
    max_accel: float
    vel_tau: float = 0.10    # velocity-command tracking time constant
    safety_radius: float = 0.35  # hard min distance its shell keeps from a person

    # behaviour-specific knobs (interpreted by each ball's guidance)
    extra: dict = field(default_factory=dict)


def quaffle() -> BallParams:
    # Big, gentle, easy to catch. Hovers and drifts; never threatening.
    return BallParams(
        name="quaffle", radius=0.18, mass=0.5,
        max_speed=7.0, max_accel=6.0, vel_tau=0.18, safety_radius=0.20,
        extra=dict(hover_descent=0.4, catch_radius=0.45),
    )


def bludger() -> BallParams:
    # Fast and aggressive, but its "hit" is a proximity tag, not a collision.
    return BallParams(
        name="bludger", radius=0.15, mass=1.2,
        max_speed=15.0, max_accel=22.0, vel_tau=0.07, safety_radius=0.45,
        # tag_radius sits well outside the no-contact floor (~0.95 m), so a
        # "hit" registers with margin to spare and never risks contact.
        extra=dict(tag_radius=1.5, retreat_time=1.2, retreat_dist=6.0,
                   bat_radius=1.6, lead_gain=0.8),
    )


def snitch() -> BallParams:
    # Tiny, absurdly agile, exists to not be caught.
    return BallParams(
        name="snitch", radius=0.04, mass=0.05,
        max_speed=19.0, max_accel=32.0, vel_tau=0.04, safety_radius=0.25,
        extra=dict(capture_radius=0.22, capture_dwell=0.25, danger_radius=4.0,
                   juke_gain=0.9, feint_period=1.3, fatigue_tau=120.0,
                   fatigue_floor=0.55),
    )


PRESETS = {"quaffle": quaffle, "bludger": bludger, "snitch": snitch}
