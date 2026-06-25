"""Record a match into lightweight frames for replay / broadcast rendering.

Snapshots the World at a downsampled rate (the sim runs at 400 Hz; ~25 fps is
plenty for video). Each frame stores just what a renderer needs: time, score,
and every agent's position + state. Trails are reconstructed by the renderer
from the frame history, so frames stay small.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Frame:
    t: float
    score: int
    players: list           # (id, pos[3], tagged_out)
    balls: list             # (name, pos[3], active)
    event: str = ""         # newest event text at this frame, if any


@dataclass
class Recording:
    frames: list = field(default_factory=list)
    pitch_lo: np.ndarray = field(default_factory=lambda: np.array([-50., -25., 1.]))
    pitch_hi: np.ndarray = field(default_factory=lambda: np.array([50., 25., 18.]))
    hoops: list = field(default_factory=list)
    title: str = "NIMBUS match"


class MatchRecorder:
    def __init__(self, world, fps: float = 25.0, sim_dt: float = 0.0025,
                 title: str = "NIMBUS match"):
        self.world = world
        self.every = max(1, int(round(1.0 / (fps * sim_dt))))
        self.rec = Recording(hoops=list(world.hoops), title=title,
                             pitch_lo=world.lo.copy(), pitch_hi=world.hi.copy())
        self._tick = 0
        self._last_event_idx = 0

    def capture(self) -> None:
        if self._tick % self.every == 0:
            w = self.world
            ev = ""
            if len(w.events) > self._last_event_idx:
                ev = w.events[-1][1]
                self._last_event_idx = len(w.events)
            self.rec.frames.append(Frame(
                t=w.t, score=w.score,
                players=[(getattr(p, "id", i), p.pos.copy(),
                          bool(getattr(p, "tagged_out", False)))
                         for i, p in enumerate(w.players)],
                balls=[(b.name, b.body.pos.copy(), b.active) for b in w.balls],
                event=ev,
            ))
        self._tick += 1

    def run(self, duration: float, sim_dt: float, stop_on_game_over=None) -> Recording:
        for _ in range(int(duration / sim_dt)):
            self.world.step(sim_dt)
            self.capture()
            if stop_on_game_over is not None and stop_on_game_over.game_over:
                self.capture()
                break
        return self.rec
