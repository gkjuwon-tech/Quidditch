"""A scripted rider, so a scenario reads like a flight plan.

Given a timeline it hands back (intent, commands) for any tick, which beats a
wall of if-statements. The script is a list of (start_time, RiderIntent,
Commands) segments and the active one is the last segment whose start_time is
<= t. Commands edge-trigger: each only fires on the tick its segment first
goes active.
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
        # only let a segment's command fire the first time we land on it
        if active not in self._fired:
            self._fired.add(active)
            cmd = seg.cmd
        else:
            cmd = Commands()
        return seg.intent, cmd, seg.link_ok
