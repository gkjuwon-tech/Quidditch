"""The Dementor -- the central referee that sees everyone.

It does two jobs the individual agents can't do for themselves:

  1. DECONFLICTION. Broom-flown players have no inter-broom avoidance of their
     own (each only knows its geofence and the balls avoid people). The
     Dementor adds a symmetric separation push between brooms so two players
     diving for the same snitch never collide.

  2. JUDGEMENT. It owns the rulebook and the scoreboard: a Bludger tag sends a
     player off for a penalty; a Quaffle through a hoop scores; catching the
     Snitch is +150 and ends the match. A master kill makes everyone descend.

It is named after the thing in the books that watches everything and ends
games -- which is exactly what a central safety/scoring server does.
"""

from __future__ import annotations

import numpy as np


class Dementor:
    def __init__(self, broom_sep: float = 3.0, margin: float = 2.5,
                 penalty_time: float = 4.0, snitch_points: int = 150):
        self.broom_sep = broom_sep
        self.margin = margin
        self.penalty_time = penalty_time
        self.snitch_points = snitch_points
        self._processed_hits: dict[int, int] = {}
        self.snitch_awarded = 0
        self.game_over = False
        self.killed = False
        self.log: list[tuple[float, str]] = []
        self.world = None

    def attach(self, world) -> "Dementor":
        world.referee = self
        self.world = world
        return self

    # ------------------------------------------------------------------ #
    @staticmethod
    def _is_broom(agent) -> bool:
        return hasattr(agent, "rider_ai")

    def override_for(self, world, agent):
        """Deconflicted velocity for a broom-flown player (None for kinematic)."""
        if not self._is_broom(agent):
            return None
        if self.killed:
            return np.array([0.0, 0.0, -1.0])      # master kill: gentle descent

        # base intent: serve a penalty (idle) or chase -- but deconfliction is
        # added either way, so penalised craft still never collide.
        if getattr(agent, "tagged_out", False) and world.t < agent._penalty_until:
            v = np.array([0.0, 0.0, -0.3])
        else:
            agent.tagged_out = False
            v = np.asarray(agent.rider_ai(world, agent), dtype=float)
        thresh = self.broom_sep + self.margin
        for other in world.players:
            if other is agent or not self._is_broom(other):
                continue
            d = agent.pos - other.pos
            dist = float(np.linalg.norm(d))
            if 1e-6 < dist < thresh:
                n = d / dist
                # symmetric separation push, ramps up as they close
                v = v + n * ((thresh - dist) / self.margin) * agent.p.max_speed_xy
        return v

    # ------------------------------------------------------------------ #
    def judge(self, world, dt: float) -> None:
        if self.game_over:
            return
        self._judge_bludger(world)
        self._judge_snitch(world)

    def _judge_bludger(self, world) -> None:
        for ball in world.balls:
            hits = getattr(ball.behavior, "hits", None)
            if not hits:
                continue
            for pid, count in hits.items():
                if count > self._processed_hits.get(pid, 0):
                    self._processed_hits[pid] = count
                    pl = self._player(world, pid)
                    if pl is not None:
                        pl.penalise(world.t + self.penalty_time)
                        self._log(world, f"player {pid} sent off for "
                                  f"{self.penalty_time:.0f}s (bludger tag)")

    def _judge_snitch(self, world) -> None:
        for ball in world.balls:
            if ball.name == "snitch" and not ball.active and self.snitch_awarded == 0:
                self.snitch_awarded = self.snitch_points
                self.game_over = True
                self._log(world, f"SNITCH CAUGHT  +{self.snitch_points}  -> GAME OVER")

    # ------------------------------------------------------------------ #
    def kill(self, world) -> None:
        """Master emergency stop: everyone descends gently, match ends."""
        self.killed = True
        self.game_over = True
        self._log(world, "MASTER KILL -- all craft to controlled descent")

    def scoreboard(self, world) -> dict:
        return {
            "quaffle_goals": world.score,
            "snitch": self.snitch_awarded,
            "total": world.score + self.snitch_awarded,
            "game_over": self.game_over,
        }

    # ------------------------------------------------------------------ #
    def _player(self, world, pid):
        return next((pl for pl in world.players if getattr(pl, "id", None) == pid), None)

    def _log(self, world, msg: str) -> None:
        self.log.append((world.t, msg))
        world.log_event(f"[DEMENTOR] {msg}")
