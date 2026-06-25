"""Quaffle: the gentle scoring ball. Hover, get caught, get carried, get thrown.

The opposite of the Bludger -- it must be easy and safe to handle:
  FREE   -> holds a soft hover and sinks slowly; a player's hand within
            catch_radius catches it.
  HELD   -> rides just ahead of its holder, matching their motion. After a
            short carry it is thrown at the nearest hoop.
  THROWN -> flies to the aimed hoop with a gentle homing "assist" (forgiving
            aim, tunable per league), and scores when it passes through.

The no-contact layer still applies, so even the Quaffle never bonks anyone --
but its whole character is to be caught, so catch_radius is generous.
"""

from __future__ import annotations

import numpy as np

from ..core import math3d as m


class QuaffleBehavior:
    FREE, HELD, THROWN = "FREE", "HELD", "THROWN"

    def __init__(self, params, carry_time: float = 1.5,
                 throw_speed: float = 12.0, assist: float = 0.6):
        self.p = params
        self.catch_radius = params.extra["catch_radius"]
        self.hover_descent = params.extra["hover_descent"]
        self.carry_time = carry_time
        self.throw_speed = throw_speed
        self.assist = assist            # 0 = no help, 1 = strong homing to hoop
        self.state = self.FREE
        self.holder = None
        self._held_since = 0.0
        self._aim = None

    # ------------------------------------------------------------------ #
    def update(self, world, ball, dt):
        body = ball.body

        if self.state == self.FREE:
            for pl in world.players:
                hand = pl.hand_toward(body.pos)
                if float(np.linalg.norm(body.pos - hand)) < self.catch_radius:
                    self.state = self.HELD
                    self.holder = pl
                    self._held_since = world.t
                    world.log_event(f"QUAFFLE caught by player {pl.id} "
                                    f"at t={world.t:.2f}s")
                    break
            # soft hover with a slow sink so it's always reachable
            return np.array([0.0, 0.0, -self.hover_descent])

        if self.state == self.HELD:
            hold_at = self.holder.pos + _facing(self.holder) * 0.6
            if world.t - self._held_since > self.carry_time and world.hoops:
                self._aim = _nearest_hoop(world, body.pos)[0]
                self.state = self.THROWN
                world.log_event(f"QUAFFLE thrown at hoop by player "
                                f"{self.holder.id} at t={world.t:.2f}s")
            return (hold_at - body.pos) * 6.0 + self.holder.vel

        # THROWN: fly to the hoop, with homing assist, score on pass-through
        to_hoop = self._aim - body.pos
        n = float(np.linalg.norm(to_hoop))
        straight = body.vel.copy()
        sn = float(np.linalg.norm(straight))
        straight = straight / sn if sn > 1e-6 else to_hoop / max(n, 1e-6)
        dir_assisted = m.normalize((1 - self.assist) * straight
                                   + self.assist * (to_hoop / max(n, 1e-6)),
                                   to_hoop / max(n, 1e-6))
        center, radius = _nearest_hoop(world, body.pos)
        if float(np.linalg.norm(body.pos - center)) < radius:
            world.score += 10
            world.log_event(f"GOAL! quaffle through the hoop (+10) "
                            f"at t={world.t:.2f}s  score={world.score}")
            self.state = self.FREE
            self.holder = None
        return dir_assisted * self.throw_speed


def _facing(player):
    n = float(np.linalg.norm(player.vel))
    return player.vel / n if n > 1e-6 else np.array([1.0, 0.0, 0.0])


def _nearest_hoop(world, pos):
    return min(world.hoops, key=lambda h: float(np.linalg.norm(pos - h[0])))
