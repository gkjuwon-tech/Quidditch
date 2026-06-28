"""Per-ball parameters.

At the guidance level a ball is just a speed- and accel-capped flying agent --
the attitude/thrust loop that turns a commanded acceleration into reality is
the same control cascade the broom already uses (nimbus_fc.control). So we
model each ball as a second-order agent and spend our effort on the new part:
autonomous guidance, evasion, pursuit, and the no-contact guarantee.

Lengths in m, speeds in m/s, accels in m/s^2.
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
    vel_tau: float = 0.10    # how quickly it tracks a velocity command (s)
    safety_radius: float = 0.35  # hard floor on shell-to-person distance

    # behaviour-specific knobs (interpreted by each ball's guidance)
    extra: dict = field(default_factory=dict)


def quaffle() -> BallParams:
    # big, slow, easy to grab; just hovers and drifts, never a threat
    return BallParams(
        name="quaffle", radius=0.18, mass=0.5,
        max_speed=7.0, max_accel=6.0, vel_tau=0.18, safety_radius=0.20,
        extra=dict(hover_descent=0.4, catch_radius=0.45),
    )


def bludger() -> BallParams:
    # fast and pushy, but a "hit" is a proximity tag, never an actual collision
    return BallParams(
        name="bludger", radius=0.15, mass=1.2,
        max_speed=15.0, max_accel=22.0, vel_tau=0.07, safety_radius=0.45,
        # tag_radius (1.5) sits comfortably outside the ~0.95 m no-contact
        # floor, so a tag always registers with room to spare
        extra=dict(tag_radius=1.5, retreat_time=1.2, retreat_dist=6.0,
                   bat_radius=1.6, lead_gain=0.8),
    )


def snitch() -> BallParams:
    # tiny, stupidly nimble, whole job is to not get caught
    return BallParams(
        name="snitch", radius=0.04, mass=0.05,
        max_speed=19.0, max_accel=32.0, vel_tau=0.04, safety_radius=0.25,
        extra=dict(capture_radius=0.22, capture_dwell=0.25, danger_radius=4.0,
                   juke_gain=0.9, feint_period=1.3, fatigue_tau=120.0,
                   fatigue_floor=0.55),
    )


PRESETS = {"quaffle": quaffle, "bludger": bludger, "snitch": snitch}
