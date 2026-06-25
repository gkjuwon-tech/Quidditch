"""Golden Snitch: predictive evasion. Its whole purpose is to not be caught.

Strategy each tick:
  1. PREDICT every seeker's reaching hand a short horizon ahead (they lunge
     toward the snitch), and flee the *predicted* hand, not the current one --
     so the snitch is already gone when the hand arrives.
  2. JUKE: add a tangential component (perpendicular to the nearest threat) with
     a periodically flipping sign, so escape isn't a straight predictable line a
     seeker can intercept. This is what makes it maddening to catch.
  3. Don't get cornered: repel from walls/ceiling/floor so seekers can't herd it
     into a boundary.
  4. FATIGUE handicap: max speed decays slowly over the match so the game
     actually ends -- late on, a good seeker can run it down. Drama by design.

Capture is judged here: a hand held within capture_radius for capture_dwell
seconds catches it (you must close your hand on it, not just brush it).
"""

from __future__ import annotations

import numpy as np

from ..core import math3d as m


class SnitchEvasion:
    def __init__(self, params):
        self.p = params
        e = params.extra
        self.danger = e["danger_radius"]
        self.capture_radius = e["capture_radius"]
        self.capture_dwell = e["capture_dwell"]
        self.juke_gain = e["juke_gain"]
        self.feint_period = e["feint_period"]
        self.fatigue_tau = e["fatigue_tau"]
        self.fatigue_floor = e["fatigue_floor"]
        self._dwell = 0.0          # how long a hand has been within capture range
        self.t = 0.0

    # ------------------------------------------------------------------ #
    def update(self, world, ball, dt):
        self.t += dt
        snitch = ball.body
        pos, vel = snitch.pos, snitch.vel

        flee = np.zeros(3)
        nearest_hand = None
        nearest_d = np.inf
        threat_dir = np.zeros(3)

        for pl in world.players:
            # predict where this seeker's hand will be as it lunges at us
            t_pred = 0.18
            p_future = pl.pos + pl.vel * t_pred
            to_snitch = pos - p_future
            n = float(np.linalg.norm(to_snitch))
            reach_dir = -to_snitch / n if n > 1e-6 else np.zeros(3)
            hand_future = p_future + reach_dir * pl.reach
            d_vec = pos - hand_future
            d = float(np.linalg.norm(d_vec))
            if d < nearest_d:
                nearest_d, nearest_hand, threat_dir = d, hand_future, (
                    d_vec / d if d > 1e-6 else np.array([1.0, 0.0, 0.0]))
            if d < self.danger:
                w = (self.danger - d) / self.danger
                flee += (d_vec / max(d, 1e-6)) * (w * w) * self.p.max_speed

            # capture judgement uses the CURRENT (not predicted) hand
            hand_now = pl.hand_toward(pos)
            if float(np.linalg.norm(pos - hand_now)) < self.capture_radius:
                self._dwell += dt
                if self._dwell >= self.capture_dwell:
                    ball.active = False
                    world.log_event(f"SNITCH CAUGHT by player {pl.id} "
                                    f"at t={world.t:.2f}s")
                    return np.zeros(3)
                break
        else:
            self._dwell = max(0.0, self._dwell - dt)  # decay if no hand close

        # juke: tangential to the nearest threat, sign flipping (feint)
        if nearest_d < self.danger:
            tang = np.cross(threat_dir, np.array([0.0, 0.0, 1.0]))
            tn = float(np.linalg.norm(tang))
            if tn > 1e-6:
                tang /= tn
                # bias the juke toward arena centre so we don't juke into a wall
                to_center = -pos.copy()
                to_center[2] = 0.0
                if np.dot(tang, to_center) < 0:
                    tang = -tang
                sign = 1.0 if np.sin(2 * np.pi * self.t / self.feint_period) >= 0 else -1.0
                w = (self.danger - nearest_d) / self.danger
                flee += tang * sign * self.juke_gain * w * self.p.max_speed

        # panic vertical dodge: when about to be pinned and the horizontal
        # escape is weak (surrounded/cornered), slip into the 3rd dimension.
        if nearest_d < 1.5 and np.linalg.norm(flee[:2]) < 0.4 * self.p.max_speed:
            up = world.hi[2] - pos[2]
            down = pos[2] - world.lo[2]
            flee[2] += (1.0 if up > down else -1.0) * self.p.max_speed

        flee += self._wall_repulsion(world, pos)

        # no nearby threat: gentle wander so it drifts rather than parks
        if nearest_d >= self.danger and np.linalg.norm(flee) < 1e-3:
            flee = 0.5 * self.p.max_speed * np.array([
                np.cos(0.4 * self.t), np.sin(0.3 * self.t), 0.2 * np.sin(0.5 * self.t)])

        speed_cap = self.p.max_speed * self._fatigue()
        return m.clamp_norm(flee, speed_cap)

    # ------------------------------------------------------------------ #
    def _fatigue(self) -> float:
        return max(self.fatigue_floor, np.exp(-self.t / self.fatigue_tau))

    def _wall_repulsion(self, world, pos) -> np.ndarray:
        push = np.zeros(3)
        react = 5.0
        for k in range(3):
            dlo = pos[k] - world.lo[k]
            dhi = world.hi[k] - pos[k]
            if dlo < react:
                push[k] += (react - dlo) / react * self.p.max_speed
            if dhi < react:
                push[k] -= (react - dhi) / react * self.p.max_speed
        return push
