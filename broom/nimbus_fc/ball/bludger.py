"""Bludger: aggressive pursuit where a "hit" is a proximity tag, not a crash.

The canonical Bludger is a cast-iron ball that cracks skulls. Ours looks every
bit as menacing and injures precisely no one:

  HUNT    -> lock the nearest eligible player and fly a lead-pursuit intercept
             toward where they're going to be.
  TAG     -> once inside tag_radius (~1 m) it logs a hit in software and peels
             off straight away. tag_radius lives *outside* the no-contact
             floor, so the shell never actually has to reach the person.
  RETREAT -> back away for a cooldown so it never loiters or piles in, then HUNT.

A bat swing inside bat_radius knocks it back. With the no-contact layer sitting
underneath all of this, contact-free is a guarantee rather than a wish.
"""

from __future__ import annotations

import numpy as np

from ..core import math3d as m


class BludgerPursuit:
    HUNT, RETREAT = "HUNT", "RETREAT"

    def __init__(self, params):
        self.p = params
        e = params.extra
        self.tag_radius = e["tag_radius"]
        self.retreat_time = e["retreat_time"]
        self.retreat_dist = e["retreat_dist"]
        self.bat_radius = e["bat_radius"]
        self.lead_gain = e["lead_gain"]
        self.state = self.HUNT
        self.target_id = None
        self._retreat_until = 0.0
        self._retreat_dir = np.zeros(3)
        self.hits: dict[int, int] = {}

    def update(self, world, ball, dt):
        body = ball.body

        if self.state == self.RETREAT:
            if world.t >= self._retreat_until:
                self.state = self.HUNT
            else:
                return self._retreat_dir * self.p.max_speed

        target = self._select_target(world, body)
        if target is None:
            return -body.vel  # no one left to chase, so coast down

        # bat deflection: a player swinging within bat_radius knocks it away
        bat = target.hand_toward(body.pos)
        if float(np.linalg.norm(body.pos - bat)) < self.bat_radius \
                and getattr(target, "swinging", False):
            self._begin_retreat(world, body, bat, "DEFLECTED by bat")
            world.log_event(f"BLUDGER deflected by player {target.id}'s bat "
                            f"at t={world.t:.2f}s")
            return self._retreat_dir * self.p.max_speed

        # tag: near enough to score a hit, no real contact required
        d = float(np.linalg.norm(body.pos - target.pos))
        if d < self.tag_radius:
            self.hits[target.id] = self.hits.get(target.id, 0) + 1
            world.log_event(f"BLUDGER TAGGED player {target.id} "
                            f"at t={world.t:.2f}s (d={d:.2f} m, no contact)")
            self._begin_retreat(world, body, target.pos, "tagged")
            return self._retreat_dir * self.p.max_speed

        # lead-pursuit intercept, but bleed the lead out as we close so the
        # endgame homes straight onto the player. chasing the tangent point
        # instead just tails a turning target forever.
        lead = self.lead_gain * min(1.0, d / 8.0)
        aim = target.pos + target.vel * lead
        v = aim - body.pos
        n = float(np.linalg.norm(v))
        if n <= 1e-6:
            return np.zeros(3)
        # ease off into the tag so it arrives slow and taps instead of blowing
        # through the safety floor: quick dart from range, soft for the last metre
        speed = min(self.p.max_speed, max(10.0, 8.0 * (d - self.tag_radius)))
        return v / n * speed

    def _select_target(self, world, body):
        live = [pl for pl in world.players if getattr(pl, "tagged_out", False) is False]
        if not live:
            return None
        return min(live, key=lambda pl: float(np.linalg.norm(pl.pos - body.pos)))

    def _begin_retreat(self, world, body, from_point, reason: str):
        self.state = self.RETREAT
        self._retreat_until = world.t + self.retreat_time
        d = body.pos - from_point
        n = float(np.linalg.norm(d))
        self._retreat_dir = d / n if n > 1e-6 else np.array([0.0, 0.0, 1.0])
