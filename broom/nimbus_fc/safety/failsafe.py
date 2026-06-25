"""Failsafe evaluation: battery and datalink -> requested safe action.

Pure policy, no state machine here -- the commander owns transitions and just
asks this what the current hazards demand. Battery thresholds mirror
ArduPilot's two-stage low/critical scheme; link loss uses a debounce timer so
a single dropped packet doesn't trigger a return-to-pit.
"""

from __future__ import annotations

from enum import Enum

from ..core.params import Params


class FailsafeAction(str, Enum):
    NONE = "NONE"
    RETURN_TO_PIT = "RETURN_TO_PIT"   # battery low, or link lost
    LAND_NOW = "LAND_NOW"             # battery critical: nearest safe descent


class Failsafe:
    def __init__(self, params: Params, link_timeout: float = 1.5):
        self.p = params
        self.link_timeout = link_timeout
        self._link_lost_for = 0.0

    def evaluate(self, soc: float, link_ok: bool, dt: float) -> tuple[FailsafeAction, str]:
        self._link_lost_for = 0.0 if link_ok else self._link_lost_for + dt

        if soc <= self.p.batt_land_soc:
            return FailsafeAction.LAND_NOW, f"battery critical ({soc*100:.0f}%) - landing now"
        if soc <= self.p.batt_rtp_soc:
            return FailsafeAction.RETURN_TO_PIT, f"battery low ({soc*100:.0f}%) - returning to pit"
        if self._link_lost_for >= self.link_timeout:
            return FailsafeAction.RETURN_TO_PIT, "datalink lost - returning to pit"
        return FailsafeAction.NONE, ""
