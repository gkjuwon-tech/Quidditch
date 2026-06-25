"""Scripted rider: turn a timeline into per-tick (intent, commands) so
scenarios read like a flight plan instead of a wall of if-statements.

A script is a list of (start_time, RiderIntent, Commands) segments; the active
segment is the last one whose start_time <= t. Commands are edge-triggered, so
a command only fires on the tick its segment becomes active.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core.types import RiderIntent
from ..safety.commander import Commands


@dataclass
class Segment:
    t: float
    intent: RiderIntent = field(default_factory=RiderIntent)
    cmd: Commands = field(default_factory=Commands)
    link_ok: bool = True


class RiderScript:
    def __init__(self, segments: list[Segment]):
        self.segments = sorted(segments, key=lambda s: s.t)
        self._fired: set[int] = set()

    def __call__(self, t: float) -> tuple[RiderIntent, Commands, bool]:
        active = 0
        for i, seg in enumerate(self.segments):
            if seg.t <= t + 1e-9:
                active = i
            else:
                break
        seg = self.segments[active]
        # Edge-trigger commands: only on the first tick the segment is active.
        if active not in self._fired:
            self._fired.add(active)
            cmd = seg.cmd
        else:
            cmd = Commands()
        return seg.intent, cmd, seg.link_ok
